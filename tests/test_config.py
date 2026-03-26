"""Tests for iblai.config -- .env file loading with stage overrides."""

import os
from pathlib import Path

import pytest

from iblai.config import load_config


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    """Remove IBLAI/DEV_STAGE env vars before each test to avoid leakage."""
    for key in list(os.environ):
        if key.startswith("IBLAI_") or key in ("DEV_STAGE", "IBLAI_STAGE"):
            monkeypatch.delenv(key, raising=False)
    yield


class TestLoadConfig:
    """Tests for load_config()."""

    def test_load_config_from_default_env_file(self, tmp_path, monkeypatch):
        """Reads .env in cwd and injects values into os.environ."""
        (tmp_path / ".env").write_text("IBLAI_PLATFORM_KEY=test-tenant\n")
        monkeypatch.chdir(tmp_path)

        result = load_config()

        assert result["IBLAI_PLATFORM_KEY"] == "test-tenant"
        assert os.environ["IBLAI_PLATFORM_KEY"] == "test-tenant"

    def test_load_config_from_custom_env_file(self, tmp_path, monkeypatch):
        """Reads from a custom path via env_file argument."""
        custom = tmp_path / "custom.env"
        custom.write_text("IBLAI_AGENT_ID=agent-42\n")
        monkeypatch.chdir(tmp_path)

        result = load_config(env_file=str(custom))

        assert result["IBLAI_AGENT_ID"] == "agent-42"
        assert os.environ["IBLAI_AGENT_ID"] == "agent-42"

    def test_load_config_stage_override(self, tmp_path, monkeypatch):
        """.env.production values override base .env values."""
        (tmp_path / ".env").write_text(
            "IBLAI_PLATFORM_KEY=base\nIBLAI_APP_NAME=base-app\n"
        )
        (tmp_path / ".env.production").write_text("IBLAI_PLATFORM_KEY=prod\n")
        monkeypatch.chdir(tmp_path)

        result = load_config(stage="production")

        assert result["IBLAI_PLATFORM_KEY"] == "prod"
        assert result["IBLAI_APP_NAME"] == "base-app"  # not in stage, comes from base

    def test_load_config_stage_from_DEV_STAGE_env_var(self, tmp_path, monkeypatch):
        """Auto-reads DEV_STAGE env var for stage name."""
        (tmp_path / ".env").write_text("IBLAI_PLATFORM_KEY=base\n")
        (tmp_path / ".env.staging").write_text("IBLAI_PLATFORM_KEY=staging\n")
        monkeypatch.setenv("DEV_STAGE", "staging")
        monkeypatch.chdir(tmp_path)

        result = load_config()

        assert result["IBLAI_PLATFORM_KEY"] == "staging"

    def test_load_config_does_not_overwrite_system_env(self, tmp_path, monkeypatch):
        """Existing system env vars take precedence over .env file values."""
        (tmp_path / ".env").write_text("IBLAI_PLATFORM_KEY=from-file\n")
        monkeypatch.setenv("IBLAI_PLATFORM_KEY", "from-system")
        monkeypatch.chdir(tmp_path)

        load_config()

        assert os.environ["IBLAI_PLATFORM_KEY"] == "from-system"

    def test_load_config_missing_env_file(self, tmp_path, monkeypatch):
        """Returns empty dict when no .env file exists, without raising."""
        monkeypatch.chdir(tmp_path)

        result = load_config()

        assert result == {}

    def test_load_config_missing_stage_file(self, tmp_path, monkeypatch):
        """Loads base .env only when stage file doesn't exist."""
        (tmp_path / ".env").write_text("IBLAI_PLATFORM_KEY=base\n")
        monkeypatch.chdir(tmp_path)

        result = load_config(stage="nonexistent")

        assert result["IBLAI_PLATFORM_KEY"] == "base"

    def test_load_config_returns_merged_dict(self, tmp_path, monkeypatch):
        """Return value is the union of base + stage."""
        (tmp_path / ".env").write_text("A=1\nB=2\n")
        (tmp_path / ".env.prod").write_text("B=3\nC=4\n")
        monkeypatch.chdir(tmp_path)

        result = load_config(stage="prod")

        assert result["A"] == "1"
        assert result["B"] == "3"  # overridden by stage
        assert result["C"] == "4"
