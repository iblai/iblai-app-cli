"""iblai deploy -- Deploy frontend to hosting platforms."""

import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel

console = Console()


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


def _resolve_scope(token):
    """Resolve the Vercel token scope from out/.vercel/project.json or API.

    Returns (org_id, scope_label) — org_id is passed as teamId/--scope,
    scope_label is for display. Returns (None, None) for full account.
    """
    # Try previous deploy first
    project_json = Path("out/.vercel/project.json")
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
def vercel(scope):
    """Deploy the frontend to Vercel.

    \b
    Builds the frontend, writes vercel.json for SPA routing,
    deploys to Vercel, disables authentication protection,
    and updates tauri.conf.json devUrl if present.

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

    # 3. Resolve scope: --scope flag > previous deploy > API detection
    org_id = scope
    scope_label = scope
    if not org_id:
        org_id, scope_label = _resolve_scope(token)

    # 4. Build frontend
    _run_frontend_build()

    out_dir = Path("out")
    if not out_dir.exists():
        console.print("[red]out/ directory not found. Build may have failed.[/red]")
        sys.exit(1)

    # 5. Write out/vercel.json (SPA routing)
    vercel_config = {
        "cleanUrls": True,
        "rewrites": [{"source": "/(.*)", "destination": "/index.html"}],
    }
    (out_dir / "vercel.json").write_text(
        json.dumps(vercel_config, indent=2) + "\n", encoding="utf-8"
    )
    console.print("[cyan]Wrote out/vercel.json (cleanUrls + SPA rewrite)[/cyan]")

    # 6. Deploy
    console.print("[cyan]Deploying to Vercel...[/cyan]")
    deploy_cmd = [
        "npx", "vercel", "deploy", "out/",
        f"--token={token}", "--yes", "--public",
    ]
    if org_id:
        deploy_cmd.extend(["--scope", org_id])

    try:
        result = subprocess.run(
            deploy_cmd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=None,  # stream to terminal so user sees progress
            text=True,
            timeout=600,
        )
    except subprocess.TimeoutExpired:
        console.print("[red]Vercel deploy timed out after 10 minutes.[/red]")
        sys.exit(1)
    if result.returncode != 0:
        console.print("[red]Vercel deploy failed.[/red]")
        sys.exit(result.returncode)

    # 7. Read project.json for projectId and orgId
    project_json = out_dir / ".vercel" / "project.json"
    project_id = None
    if project_json.exists():
        try:
            project_data = json.loads(project_json.read_text(encoding="utf-8"))
            project_id = project_data.get("projectId")
            org_id = project_data.get("orgId") or org_id
        except (json.JSONDecodeError, OSError):
            pass

    # 8. Get deployment URL from Vercel API
    deploy_url = None
    if project_id:
        deployments = _vercel_api(
            "GET",
            f"/v6/deployments?projectId={project_id}&limit=1",
            token,
            team_id=org_id,
        )
        if deployments and deployments.get("deployments"):
            latest = deployments["deployments"][0]
            deploy_url = f"https://{latest['url']}"

    if not deploy_url:
        # Fallback: parse stdout (last line is the URL)
        lines = result.stdout.strip().splitlines()
        deploy_url = lines[-1].strip() if lines else None

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
