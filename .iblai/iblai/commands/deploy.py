"""iblai deploy -- Deploy frontend to hosting platforms."""

import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel

console = Console()


def _detect_deploy_mode(root: Path) -> str:
    """Return 'static' if next.config sets output: 'export', else 'server'.

    Static apps (Tauri shells) export to out/ and ship as plain HTML/JS.
    Server apps keep server actions, dynamic routes, and API routes, and let
    Vercel run the Next.js build remotely with serverless functions.
    """
    for name in ("next.config.ts", "next.config.mjs", "next.config.js"):
        p = root / name
        if not p.exists():
            continue
        content = p.read_text(encoding="utf-8")
        if re.search(r"output\s*:\s*[\"']export[\"']", content):
            return "static"
    return "server"


def _project_json_path(mode: str) -> Path:
    """Where Vercel writes .vercel/project.json after `vercel deploy`.

    Static runs `vercel deploy out/` so Vercel writes out/.vercel/.
    Server deploys from cwd so Vercel writes ./.vercel/.
    """
    return (
        Path("out/.vercel/project.json")
        if mode == "static"
        else Path(".vercel/project.json")
    )


def _parse_env_file(path: Path) -> dict:
    """Parse a .env file into {key: value}. Strips surrounding quotes,
    skips comments and blank lines. Returns {} if the file does not exist.
    """
    env: dict = {}
    if not path.exists():
        return env
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
            value = value[1:-1]
        if key:
            env[key] = value
    return env


# Vars that Vercel manages itself or that don't belong in a deployed env.
_RESERVED_ENV_VARS = {
    "NODE_ENV",
    "VERCEL",
    "VERCEL_ENV",
    "VERCEL_URL",
    "VERCEL_REGION",
    "VERCEL_GIT_COMMIT_SHA",
    "VERCEL_GIT_COMMIT_MESSAGE",
    "VERCEL_GIT_COMMIT_AUTHOR_LOGIN",
    "VERCEL_GIT_COMMIT_AUTHOR_NAME",
    "VERCEL_GIT_REPO_SLUG",
    "VERCEL_GIT_REPO_ID",
    "VERCEL_GIT_REPO_OWNER",
    "VERCEL_GIT_PROVIDER",
    "VERCEL_GIT_PREVIOUS_SHA",
    # Local-only / sensitive to leak — never push to a deployed project.
    "VERCEL_TOKEN",
    "IBLAI_DEV",
}


def _is_placeholder(value: str) -> bool:
    """Empty or 'your-...' template values that shouldn't be deployed."""
    if not value:
        return True
    return value.startswith("your-")


def _push_env_to_vercel(
    token: str,
    project_id: str,
    org_id,
    env_vars: dict,
    targets=("production", "preview"),
):
    """Upsert env vars on a Vercel project. Idempotent.

    Returns (created, updated, skipped). `created` are new keys POSTed,
    `updated` are existing keys PATCHed, `skipped` are placeholders / reserved
    keys / missing values not pushed.
    """
    existing_resp = _vercel_api(
        "GET", f"/v10/projects/{project_id}/env", token, team_id=org_id
    )
    existing = {}
    if existing_resp:
        for e in existing_resp.get("envs", []):
            existing[e["key"]] = e

    created = updated = skipped = 0
    for key, value in env_vars.items():
        if key in _RESERVED_ENV_VARS or _is_placeholder(value):
            skipped += 1
            continue
        env_type = "plain" if key.startswith("NEXT_PUBLIC_") else "encrypted"
        target_list = list(targets)
        if key in existing:
            env_id = existing[key]["id"]
            resp = _vercel_api(
                "PATCH",
                f"/v10/projects/{project_id}/env/{env_id}",
                token,
                data={"value": value, "target": target_list, "type": env_type},
                team_id=org_id,
            )
            if resp is not None:
                updated += 1
        else:
            resp = _vercel_api(
                "POST",
                f"/v10/projects/{project_id}/env",
                token,
                data={
                    "key": key,
                    "value": value,
                    "type": env_type,
                    "target": target_list,
                },
                team_id=org_id,
            )
            if resp is not None:
                created += 1

    return created, updated, skipped


def _vercel_api(method, path, token, data=None, team_id=None):
    """Make a Vercel API request. Returns parsed JSON or None on error."""
    url = f"https://api.vercel.com{path}"
    if team_id:
        sep = "&" if "?" in url else "?"
        url += f"{sep}teamId={team_id}"
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method=method,
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except (urllib.error.URLError, json.JSONDecodeError, OSError):
        return None


def _execute_deploy(cmd, extra_env=None):
    """Run `vercel deploy ...` and return the CompletedProcess.

    Exits the program on timeout or non-zero return code so callers can treat
    a returned value as a successful deploy. `extra_env` is merged on top of
    os.environ for the subprocess (e.g. VERCEL_FORCE_NO_BUILD_CACHE=1).
    """
    env = None
    if extra_env:
        env = os.environ.copy()
        env.update(extra_env)
    try:
        result = subprocess.run(
            cmd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=None,  # stream to terminal so user sees progress
            text=True,
            timeout=600,
            env=env,
        )
    except subprocess.TimeoutExpired:
        console.print("[red]Vercel deploy timed out after 10 minutes.[/red]")
        sys.exit(1)
    if result.returncode != 0:
        console.print("[red]Vercel deploy failed.[/red]")
        sys.exit(result.returncode)
    return result


def _resolve_deploy_url(result, project_id, org_id, token):
    """Return the just-deployed URL. Prefer the Vercel API (project's latest
    deployment), fall back to the last line of vercel CLI stdout.
    """
    if project_id:
        deployments = _vercel_api(
            "GET",
            f"/v6/deployments?projectId={project_id}&limit=1",
            token,
            team_id=org_id,
        )
        if deployments and deployments.get("deployments"):
            return f"https://{deployments['deployments'][0]['url']}"
    lines = result.stdout.strip().splitlines()
    return lines[-1].strip() if lines else None


def _resolve_scope(token, mode="static"):
    """Resolve the Vercel token scope from .vercel/project.json or API.

    Returns (org_id, scope_label) — org_id is passed as teamId/--scope,
    scope_label is for display. Returns (None, None) for full account.
    """
    # Try previous deploy first
    project_json = _project_json_path(mode)
    if project_json.exists():
        try:
            data = json.loads(project_json.read_text(encoding="utf-8"))
            org_id = data.get("orgId")
            if org_id:
                return org_id, org_id
        except (json.JSONDecodeError, OSError):
            pass

    # No previous deploy — check API for teams
    console.print("[cyan]Checking Vercel token scope...[/cyan]")
    teams_resp = _vercel_api("GET", "/v2/teams", token)
    if teams_resp:
        teams = teams_resp.get("teams", [])
        if len(teams) == 1:
            team = teams[0]
            team_id = team.get("id")
            team_name = team.get("name") or team.get("slug") or team_id
            console.print(f"[cyan]Token scoped to team: {team_name}[/cyan]")
            return team_id, team_name

    return None, None


@click.group()
def deploy():
    """Deploy frontend to hosting platforms."""
    pass


@deploy.command("vercel")
@click.option(
    "--scope",
    default=None,
    help="Vercel team ID or slug. Auto-detected from previous deploy or token scope.",
)
@click.option(
    "--mode",
    type=click.Choice(["auto", "static", "server"]),
    default="auto",
    help=(
        "Deploy mode. 'auto' (default) detects from next.config — 'static' "
        "when output: 'export' is set (Tauri shells), otherwise 'server' "
        "(Next.js with server actions / dynamic routes / API routes)."
    ),
)
def vercel(scope, mode):
    """Deploy the frontend to Vercel.

    \b
    Auto-detects static vs server mode from next.config.
      static — builds locally, deploys out/ as plain files (Tauri shells)
      server — deploys the repo; Vercel runs the build and provisions
               serverless functions for server actions / API routes
    Both modes disable auth protection and update tauri.conf.json devUrl
    if present.

    \b
    Requires VERCEL_TOKEN in iblai.env.
    Create a token at https://vercel.com/account/tokens
    """
    from iblai.commands.builds import _run_frontend_build

    # 1. Check VERCEL_TOKEN
    token = os.environ.get("VERCEL_TOKEN", "")
    if not token or token in ("your-vercel-token",):
        console.print(
            Panel(
                "[bold red]VERCEL_TOKEN not found[/bold red]\n\n"
                "Add your Vercel token to [cyan]iblai.env[/cyan]:\n\n"
                "  VERCEL_TOKEN=your-token-here\n\n"
                "Create a token at: [cyan]https://vercel.com/account/tokens[/cyan]",
                title="Missing Token",
                border_style="red",
            )
        )
        sys.exit(1)

    # 2. Validate token
    console.print("[cyan]Checking Vercel token...[/cyan]")
    user = _vercel_api("GET", "/v2/user", token)
    if not user or "user" not in user:
        console.print(
            Panel(
                "[bold red]Invalid VERCEL_TOKEN[/bold red]\n\n"
                "The token in iblai.env is not valid or has expired.\n\n"
                "Create a new token at: [cyan]https://vercel.com/account/tokens[/cyan]",
                title="Authentication Failed",
                border_style="red",
            )
        )
        sys.exit(1)

    # 3. Detect deploy mode
    deploy_mode = _detect_deploy_mode(Path.cwd()) if mode == "auto" else mode
    console.print(f"[cyan]Deploy mode: {deploy_mode}[/cyan]")

    # 4. Resolve scope: --scope flag > previous deploy > API detection
    org_id = scope
    scope_label = scope
    if not org_id:
        org_id, scope_label = _resolve_scope(token, deploy_mode)

    # 5. Mode-specific build + deploy command
    if deploy_mode == "static":
        # Build locally, deploy out/ as a static SPA.
        _run_frontend_build()

        out_dir = Path("out")
        if not out_dir.exists():
            console.print(
                "[red]out/ directory not found. Build may have failed.[/red]"
            )
            sys.exit(1)

        # Write out/vercel.json (SPA routing)
        vercel_config = {
            "cleanUrls": True,
            "rewrites": [{"source": "/(.*)", "destination": "/index.html"}],
        }
        (out_dir / "vercel.json").write_text(
            json.dumps(vercel_config, indent=2) + "\n", encoding="utf-8"
        )
        console.print(
            "[cyan]Wrote out/vercel.json (cleanUrls + SPA rewrite)[/cyan]"
        )

        deploy_cmd = [
            "npx", "vercel", "deploy", "out/",
            f"--token={token}", "--yes", "--public",
        ]
    else:
        # Server mode: deploy the repo; Vercel runs the build remotely and
        # provisions serverless functions for server actions, API routes,
        # and dynamic pages.
        console.print(
            "[cyan]Server mode — deploying repo root; Vercel will run the "
            "Next.js build.[/cyan]"
        )
        deploy_cmd = [
            "npx", "vercel", "deploy", "--prod",
            f"--token={token}", "--yes", "--public",
        ]

    if org_id:
        deploy_cmd.extend(["--scope", org_id])

    console.print("[cyan]Deploying to Vercel...[/cyan]")
    result = _execute_deploy(deploy_cmd)

    # 7. Read project.json for projectId and orgId (path depends on mode)
    project_json = _project_json_path(deploy_mode)
    project_id = None
    if project_json.exists():
        try:
            project_data = json.loads(project_json.read_text(encoding="utf-8"))
            project_id = project_data.get("projectId")
            org_id = project_data.get("orgId") or org_id
        except (json.JSONDecodeError, OSError):
            pass

    # 8. Resolve deployment URL
    deploy_url = _resolve_deploy_url(result, project_id, org_id, token)
    if not deploy_url:
        console.print("[red]Could not determine deployment URL.[/red]")
        sys.exit(1)
    console.print(f"[green]Deployed:[/green] {deploy_url}")

    # 9. Disable auth protection (pass teamId if scoped)
    if project_id:
        console.print("[cyan]Disabling Vercel authentication...[/cyan]")
        resp = _vercel_api(
            "PATCH",
            f"/v9/projects/{project_id}",
            token,
            data={"ssoProtection": None, "passwordProtection": None},
            team_id=org_id,
        )
        if resp is not None:
            console.print("[green]Authentication protection disabled.[/green]")
        else:
            console.print(
                "[yellow]Warning: Could not disable auth protection.[/yellow]"
            )

    # 9b. Push env vars from .env.local (server mode only) and rebuild if
    # anything changed. NEXT_PUBLIC_* values are baked into the client bundle
    # at build time, so the first build has stale (or missing) values until
    # we rebuild with the freshly-uploaded env in place.
    if deploy_mode == "server" and project_id:
        env_local = _parse_env_file(Path(".env.local"))
        if env_local:
            console.print(
                "[cyan]Pushing env vars from .env.local to Vercel "
                "(production + preview)...[/cyan]"
            )
            created, updated, skipped = _push_env_to_vercel(
                token, project_id, org_id, env_local
            )
            console.print(
                f"[green]Env vars:[/green] {created} created, {updated} updated, "
                f"{skipped} skipped"
            )
            if created > 0 or updated > 0:
                console.print(
                    "[cyan]Env vars changed — rebuilding without build "
                    "cache so the new values are inlined into the client "
                    "bundle...[/cyan]"
                )
                # --force creates a new deployment; VERCEL_FORCE_NO_BUILD_CACHE
                # tells Vercel's remote builder to skip cache restore so
                # `process.env.NEXT_PUBLIC_*` references are re-inlined from
                # the freshly-uploaded env vars, instead of reusing the
                # previous build's compiled bundle.
                rebuild_cmd = deploy_cmd + ["--force"]
                result = _execute_deploy(
                    rebuild_cmd,
                    extra_env={"VERCEL_FORCE_NO_BUILD_CACHE": "1"},
                )
                deploy_url = (
                    _resolve_deploy_url(result, project_id, org_id, token)
                    or deploy_url
                )
                console.print(f"[green]Redeployed:[/green] {deploy_url}")
        else:
            console.print(
                "[yellow].env.local not found — skipping env push.[/yellow]"
            )

    # 10. Update tauri.conf.json devUrl
    tauri_conf = Path("src-tauri/tauri.conf.json")
    if tauri_conf.exists():
        try:
            conf = json.loads(tauri_conf.read_text(encoding="utf-8"))
            conf.setdefault("build", {})["devUrl"] = deploy_url
            tauri_conf.write_text(
                json.dumps(conf, indent=2) + "\n", encoding="utf-8"
            )
            console.print(
                f"[cyan]Updated src-tauri/tauri.conf.json devUrl → {deploy_url}[/cyan]"
            )
        except (json.JSONDecodeError, OSError) as exc:
            console.print(
                f"[yellow]Warning: Could not update tauri.conf.json: {exc}[/yellow]"
            )

    # 11. Summary
    scope_info = f"\n[bold]Scope:[/bold] {scope_label}" if scope_label else ""
    console.print()
    console.print(
        Panel(
            f"[bold green]Deployment complete[/bold green]\n\n"
            f"[bold]URL:[/bold] [cyan]{deploy_url}[/cyan]{scope_info}",
            title="iblai deploy vercel",
            border_style="green",
        )
    )
