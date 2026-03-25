"""Tests for iblai_cli.ai_helper -- AIHelper constructor and parameter handling."""

import pytest

from iblai_cli.ai_helper import AIHelper


class TestAIHelperInit:
    """Tests for AIHelper.__init__ and parameter defaults."""

    def test_default_anthropic_model(self):
        h = AIHelper(provider="anthropic", anthropic_key="fake-key")
        assert h.model == AIHelper.DEFAULT_ANTHROPIC_MODEL

    def test_default_openai_model(self):
        h = AIHelper(provider="openai", openai_key="fake-key")
        assert h.model == AIHelper.DEFAULT_OPENAI_MODEL

    def test_custom_model_override(self):
        h = AIHelper(provider="anthropic", anthropic_key="fake", model="custom-v1")
        assert h.model == "custom-v1"

    def test_custom_temperature(self):
        h = AIHelper(provider="openai", openai_key="fake", temperature=0.9)
        assert h.temperature == 0.9

    def test_custom_max_tokens(self):
        h = AIHelper(provider="anthropic", anthropic_key="fake", max_tokens=2048)
        assert h.max_tokens == 2048

    def test_default_temperature_is_none(self):
        h = AIHelper(provider="anthropic", anthropic_key="fake")
        assert h.temperature is None

    def test_default_max_tokens_is_none(self):
        h = AIHelper(provider="openai", openai_key="fake")
        assert h.max_tokens is None

    def test_invalid_provider_raises(self):
        with pytest.raises(ValueError, match="Unsupported AI provider"):
            AIHelper(provider="invalid")

    def test_anthropic_without_key_raises(self):
        with pytest.raises(ValueError, match="Anthropic API key required"):
            AIHelper(provider="anthropic")

    def test_openai_without_key_raises(self):
        with pytest.raises(ValueError, match="OpenAI API key required"):
            AIHelper(provider="openai")
