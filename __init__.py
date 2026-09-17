"""Kiro ACP provider profile for Hermes Agent.

kiro-cli does not speak OpenAI-over-HTTP: it drives an external ACP subprocess
over stdio, so the profile supplies its own client via
:meth:`ProviderProfile.create_client`. Ships as a standalone plugin per the
upstream vendor-integration policy (see the closed PRs #80362/#98151) — zero
core edits.
"""

from typing import Any

from providers import register_provider
from providers.base import ProviderProfile

# Public API re-exports (used by tests and power users to inspect what will spawn).
from .kiro_acp_client import KiroACPClient, resolve_kiro_args, resolve_kiro_command  # noqa: F401


class KiroACPProfile(ProviderProfile):
    """Kiro CLI (AWS) via ACP subprocess — external process, no REST endpoint."""

    def create_client(self, **client_kwargs: Any) -> Any:
        """Build the ACP stdio shim rather than an HTTP client."""
        from .kiro_acp_client import KiroACPClient

        command = client_kwargs.get("command") or self.process_command
        args = tuple(client_kwargs.get("args") or self.process_args or ())

        return KiroACPClient(command=command, args=args, **{
            k: v for k, v in client_kwargs.items() if k not in ("command", "args")
        })

    def fetch_models(
        self, *, api_key: str | None = None, base_url: str | None = None, timeout: float = 8.0
    ) -> list[str] | None:
        """Model listing is handled by the ACP subprocess."""
        return None


kiro_acp = KiroACPProfile(
    name="kiro-acp",
    aliases=("kiro", "kiro-cli", "kiro-acp-agent"),
    display_name="Kiro (AWS)",
    description="Kiro CLI agent driven over ACP stdio",
    api_mode="chat_completions",  # ACP subprocess uses chat_completions routing
    env_vars=(),  # Auth handled by the kiro-cli subprocess itself
    base_url="acp://kiro",  # ACP internal scheme
    auth_type="external_process",
    # How to launch the CLI. Env overrides let users point at a custom binary
    # or pass extra flags (e.g. --agent / --effort) without editing the plugin.
    process_command="kiro-cli",
    process_args=("acp",),
    process_command_env_vars=("HERMES_KIRO_ACP_COMMAND", "KIRO_CLI_PATH"),
    process_args_env_var="HERMES_KIRO_ACP_ARGS",
)

register_provider(kiro_acp)
