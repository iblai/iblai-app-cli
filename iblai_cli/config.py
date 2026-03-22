"""Configuration loading from .env files with stage-based overrides.

Resolution priority (highest wins):
    CLI flags > System env vars > .env.{DEV_STAGE} > .env

Values from .env files are injected into os.environ so that Click's
built-in envvar= mechanism picks them up automatically. Existing
system environment variables are never overwritten.
"""

import os
from pathlib import Path
from typing import Dict, Optional

from dotenv import dotenv_values


def load_config(
    env_file: Optional[str] = None,
    stage: Optional[str] = None,
) -> Dict[str, Optional[str]]:
    """
    Load configuration from .env files.

    Reads a base .env file, then overlays values from a stage-specific
    .env.{stage} file if a stage is specified (via argument, DEV_STAGE,
    or IBLAI_STAGE env vars). Loaded values are injected into os.environ
    without overwriting existing system environment variables.

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
    if base_path.is_file():
        config.update(dotenv_values(base_path))

    # 2. Load stage-specific .env.{stage} (overrides base values)
    resolved_stage = (
        stage or os.environ.get("DEV_STAGE") or os.environ.get("IBLAI_STAGE")
    )
    if resolved_stage:
        stage_dir = base_path.parent
        stage_path = stage_dir / f".env.{resolved_stage}"
        if stage_path.is_file():
            config.update(dotenv_values(stage_path))

    # 3. Inject into os.environ so Click's envvar= picks them up.
    #    Never overwrite existing system env vars — they take precedence.
    for key, value in config.items():
        if value is not None and key not in os.environ:
            os.environ[key] = value

    return config
