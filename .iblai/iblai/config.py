"""Configuration loading from .env files with stage-based overrides.

Resolution priority (highest wins):
    CLI flags > System env vars > iblai.env > .env.{DEV_STAGE} > .env.local > .env

Values from .env files are injected into os.environ so that Click's
built-in envvar= mechanism picks them up automatically. Existing
system environment variables are never overwritten.

Shorthand variables:
    DOMAIN             → derives NEXT_PUBLIC_API_BASE_URL, AUTH_URL, BASE_WS_URL, PLATFORM_BASE_DOMAIN
    PLATFORM           → derives NEXT_PUBLIC_MAIN_TENANT_KEY
    TOKEN              → derives IBLAI_API_KEY (server-side, not NEXT_PUBLIC_)
    TAURI_CUSTOM_SCHEME → derives NEXT_PUBLIC_TAURI_CUSTOM_SCHEME
"""

import os
from pathlib import Path
from typing import Dict, Optional

from dotenv import dotenv_values


def _derive_env_vars() -> None:
    """Derive NEXT_PUBLIC_* vars from shorthand DOMAIN/PLATFORM/TOKEN.

    Only sets derived vars that are not already present in os.environ,
    so explicit overrides always win.
    """
    domain = os.environ.get("DOMAIN")
    if domain:
        defaults = {
            "NEXT_PUBLIC_API_BASE_URL": f"https://api.{domain}",
            "NEXT_PUBLIC_AUTH_URL": f"https://login.{domain}",
            "NEXT_PUBLIC_BASE_WS_URL": f"wss://asgi.data.{domain}",
            "NEXT_PUBLIC_PLATFORM_BASE_DOMAIN": domain,
        }
        for key, value in defaults.items():
            if key not in os.environ:
                os.environ[key] = value

    platform = os.environ.get("PLATFORM")
    if platform and "NEXT_PUBLIC_MAIN_TENANT_KEY" not in os.environ:
        os.environ["NEXT_PUBLIC_MAIN_TENANT_KEY"] = platform

    token = os.environ.get("TOKEN")
    if token and "IBLAI_API_KEY" not in os.environ:
        os.environ["IBLAI_API_KEY"] = token

    tauri_scheme = os.environ.get("TAURI_CUSTOM_SCHEME")
    if tauri_scheme and "NEXT_PUBLIC_TAURI_CUSTOM_SCHEME" not in os.environ:
        os.environ["NEXT_PUBLIC_TAURI_CUSTOM_SCHEME"] = tauri_scheme


def load_config(
    env_file: Optional[str] = None,
    stage: Optional[str] = None,
) -> Dict[str, Optional[str]]:
    """
    Load configuration from .env files.

    Reads dot-env files in this order (later files override earlier):
        .env → .env.local → .env.development → .env.{stage} → iblai.env

    Then derives NEXT_PUBLIC_* vars from DOMAIN/PLATFORM/TOKEN shorthands.
    Loaded values are injected into os.environ without overwriting existing
    system environment variables.

    Args:
        env_file: Custom path to base .env file. Defaults to .env in
                  the current working directory.
        stage: Stage name (e.g., production, staging). Falls back to
               DEV_STAGE or IBLAI_STAGE environment variables.

    Returns:
        Merged config dict from all .env sources.
    """
    config: Dict[str, Optional[str]] = {}

    # 1. Load base .env
    base_path = Path(env_file) if env_file else Path.cwd() / ".env"
    base_dir = base_path.parent
    if base_path.is_file():
        config.update(dotenv_values(base_path))

    # 2. Load .env.local and .env.development (common Next.js convention)
    for name in (".env.local", ".env.development"):
        extra = base_dir / name
        if extra.is_file():
            config.update(dotenv_values(extra))

    # 3. Load stage-specific .env.{stage} (overrides base values)
    resolved_stage = (
        stage or os.environ.get("DEV_STAGE") or os.environ.get("IBLAI_STAGE")
    )
    if resolved_stage:
        stage_path = base_dir / f".env.{resolved_stage}"
        if stage_path.is_file():
            config.update(dotenv_values(stage_path))

    # 4. Load iblai.env (highest priority among dot-env files)
    iblai_env = base_dir / "iblai.env"
    if iblai_env.is_file():
        config.update(dotenv_values(iblai_env))

    # 5. Inject into os.environ so Click's envvar= picks them up.
    #    iblai.env values win over .env.local because they were loaded last.
    #    Never overwrite existing system env vars — they take precedence.
    for key, value in config.items():
        if value is not None and key not in os.environ:
            os.environ[key] = value

    # 6. Derive NEXT_PUBLIC_* from DOMAIN/PLATFORM/TOKEN shorthands.
    _derive_env_vars()

    return config
