"""Tests for claude_brief.py -- mocked, no real API calls."""
import os
from unittest.mock import patch, MagicMock

import pytest

from claude_brief import call_claude, ClaudeCallError, CLAUDE_MODEL


def _mock_client_returning(text: str) -> MagicMock:
    mock_client = MagicMock()
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text=text)]
    mock_client.messages.create.return_value = mock_message
    return mock_client


class TestCallClaudeSuccess:
    def test_returns_stripped_text(self):
        with patch("anthropic.Anthropic") as mock_cls:
            mock_cls.return_value = _mock_client_returning("  Grid stress is elevated.  ")
            result = call_claude([{"role": "user", "content": "hi"}], api_key="test-key")
        assert result == "Grid stress is elevated."

    def test_uses_pinned_model_by_default(self):
        with patch("anthropic.Anthropic") as mock_cls:
            mock_client = _mock_client_returning("ok")
            mock_cls.return_value = mock_client
            call_claude([{"role": "user", "content": "hi"}], api_key="test-key")
        _, kwargs = mock_client.messages.create.call_args
        assert kwargs["model"] == CLAUDE_MODEL

    def test_passes_system_prompt_when_given(self):
        with patch("anthropic.Anthropic") as mock_cls:
            mock_client = _mock_client_returning("ok")
            mock_cls.return_value = mock_client
            call_claude([{"role": "user", "content": "hi"}], system="be terse", api_key="test-key")
        _, kwargs = mock_client.messages.create.call_args
        assert kwargs["system"] == "be terse"

    def test_omits_system_kwarg_when_not_given(self):
        with patch("anthropic.Anthropic") as mock_cls:
            mock_client = _mock_client_returning("ok")
            mock_cls.return_value = mock_client
            call_claude([{"role": "user", "content": "hi"}], api_key="test-key")
        _, kwargs = mock_client.messages.create.call_args
        assert "system" not in kwargs

    def test_passes_max_tokens(self):
        with patch("anthropic.Anthropic") as mock_cls:
            mock_client = _mock_client_returning("ok")
            mock_cls.return_value = mock_client
            call_claude([{"role": "user", "content": "hi"}], max_tokens=64, api_key="test-key")
        _, kwargs = mock_client.messages.create.call_args
        assert kwargs["max_tokens"] == 64

    def test_env_var_api_key_used_when_not_passed_explicitly(self):
        os.environ["ANTHROPIC_API_KEY"] = "from-env"
        try:
            with patch("anthropic.Anthropic") as mock_cls:
                mock_cls.return_value = _mock_client_returning("ok")
                call_claude([{"role": "user", "content": "hi"}])
            mock_cls.assert_called_once_with(api_key="from-env")
        finally:
            os.environ.pop("ANTHROPIC_API_KEY", None)


class TestOnErrorRaise:
    """Default behavior -- matches water_monitor's and gridpulse's own brief.py."""

    def test_missing_api_key_raises_claude_call_error(self):
        os.environ.pop("ANTHROPIC_API_KEY", None)
        with pytest.raises(ClaudeCallError):
            call_claude([{"role": "user", "content": "hi"}], api_key="")

    def test_missing_api_key_env_fallback_raises(self):
        os.environ.pop("ANTHROPIC_API_KEY", None)
        with pytest.raises(ClaudeCallError):
            call_claude([{"role": "user", "content": "hi"}])

    def test_sdk_typeerror_wrapped_as_claude_call_error(self):
        # The Anthropic SDK raises a bare TypeError (not anthropic.APIError)
        # for a missing/malformed key -- this must be caught by the broad
        # except Exception, not slip through unguarded.
        with patch("anthropic.Anthropic", side_effect=TypeError("bad key")):
            with pytest.raises(ClaudeCallError):
                call_claude([{"role": "user", "content": "hi"}], api_key="test-key")

    def test_generic_exception_wrapped_as_claude_call_error(self):
        with patch("anthropic.Anthropic") as mock_cls:
            mock_client = MagicMock()
            mock_client.messages.create.side_effect = RuntimeError("network blip")
            mock_cls.return_value = mock_client
            with pytest.raises(ClaudeCallError, match="network blip"):
                call_claude([{"role": "user", "content": "hi"}], api_key="test-key")

    def test_fallback_ignored_in_raise_mode(self):
        """A caller shouldn't accidentally get silent fallback behavior by
        passing fallback= without also setting on_error="fallback"."""
        with patch("anthropic.Anthropic") as mock_cls:
            mock_client = MagicMock()
            mock_client.messages.create.side_effect = RuntimeError("network blip")
            mock_cls.return_value = mock_client
            with pytest.raises(ClaudeCallError):
                call_claude(
                    [{"role": "user", "content": "hi"}],
                    api_key="test-key",
                    fallback="should not be returned",
                )


class TestOnErrorFallback:
    """Matches joule's own brief.py behavior -- screening tools keep the
    already-computed deterministic template rather than failing outright."""

    def test_requires_fallback_text(self):
        with pytest.raises(ValueError, match="fallback"):
            call_claude([{"role": "user", "content": "hi"}], on_error="fallback", api_key="test-key")

    def test_missing_api_key_returns_fallback_not_raise(self):
        os.environ.pop("ANTHROPIC_API_KEY", None)
        result = call_claude(
            [{"role": "user", "content": "hi"}],
            api_key="",
            on_error="fallback",
            fallback="deterministic template text",
        )
        assert result == "deterministic template text"

    def test_api_failure_returns_fallback_not_raise(self):
        with patch("anthropic.Anthropic") as mock_cls:
            mock_client = MagicMock()
            mock_client.messages.create.side_effect = RuntimeError("network blip")
            mock_cls.return_value = mock_client
            result = call_claude(
                [{"role": "user", "content": "hi"}],
                api_key="test-key",
                on_error="fallback",
                fallback="deterministic template text",
            )
        assert result == "deterministic template text"

    def test_success_still_returns_real_text_not_fallback(self):
        with patch("anthropic.Anthropic") as mock_cls:
            mock_cls.return_value = _mock_client_returning("real Claude output")
            result = call_claude(
                [{"role": "user", "content": "hi"}],
                api_key="test-key",
                on_error="fallback",
                fallback="deterministic template text",
            )
        assert result == "real Claude output"


class TestInvalidOnError:
    def test_unknown_on_error_value_raises_value_error(self):
        with pytest.raises(ValueError, match="on_error"):
            call_claude([{"role": "user", "content": "hi"}], on_error="ignore", api_key="test-key")
