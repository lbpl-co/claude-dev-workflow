"""Configures and invokes PR-Agent with local Ollama + Bitbucket settings."""

from __future__ import annotations

import asyncio
import base64
import sys
from pathlib import Path

CONFIG_DIR = Path(__file__).resolve().parent.parent.parent / "config"


def run_review(
    pr_url: str,
    command: str,
    model: str,
    secrets: dict,
    question: str | None = None,
) -> None:
    """Configure PR-Agent and run the requested command against a PR."""
    _configure_pr_agent(model, secrets)
    _patch_bitbucket_auth(secrets)
    asyncio.run(_execute(pr_url, command, question))


def _configure_pr_agent(model: str, secrets: dict) -> None:
    """Apply all settings to PR-Agent's Dynaconf config."""
    from pr_agent.config_loader import get_settings

    # Load our configuration.toml into PR-Agent's settings
    config_path = CONFIG_DIR / "configuration.toml"
    if config_path.exists():
        get_settings().load_file(path=str(config_path))

    # LLM settings
    get_settings().set("CONFIG.MODEL", model)
    get_settings().set("CONFIG.FALLBACK_MODELS", [model])
    get_settings().set("CONFIG.CUSTOM_MODEL_MAX_TOKENS", 128000)

    # Ollama connection
    get_settings().set("OLLAMA.API_BASE", secrets["ollama_api_base"])

    # Git provider — set to bitbucket, auth is handled by the patch below
    get_settings().set("CONFIG.GIT_PROVIDER", "bitbucket")

    # Set a dummy bearer token so PR-Agent doesn't crash before our patch runs
    get_settings().set("BITBUCKET.BEARER_TOKEN", "patched-below")


def _patch_bitbucket_auth(secrets: dict) -> None:
    """Monkey-patch BitbucketProvider to use Basic auth with App Passwords.

    PR-Agent's BitbucketProvider hardcodes Bearer auth, but Bitbucket App
    Passwords require HTTP Basic auth (username:app_password base64-encoded).
    """
    from pr_agent.git_providers.bitbucket_provider import BitbucketProvider

    username = secrets["bitbucket_username"]
    app_password = secrets["bitbucket_app_password"]
    credentials = base64.b64encode(f"{username}:{app_password}".encode()).decode()

    _original_init = BitbucketProvider.__init__

    def _patched_init(self, pr_url=None, incremental=False):
        import requests
        from atlassian.bitbucket import Cloud

        s = requests.Session()
        s.headers["Authorization"] = f"Basic {credentials}"
        s.headers["Content-Type"] = "application/json"
        self.headers = s.headers
        self.bitbucket_client = Cloud(session=s)
        self.max_comment_length = 31000
        self.workspace_slug = None
        self.repo_slug = None
        self.repo = None
        self.pr_num = None
        self.pr = None
        self.pr_url = pr_url
        self.temp_comments = []
        self.incremental = incremental
        self.diff_files = None
        self.git_files = None
        if pr_url:
            self.set_pr(pr_url)
        self.bitbucket_comment_api_url = (
            self.pr._BitbucketBase__data["links"]["comments"]["href"]
        )
        self.bitbucket_pull_request_api_url = (
            self.pr._BitbucketBase__data["links"]["self"]["href"]
        )

    BitbucketProvider.__init__ = _patched_init


async def _execute(pr_url: str, command: str, question: str | None) -> None:
    """Run a PR-Agent command."""
    from pr_agent.agent.pr_agent import PRAgent

    agent = PRAgent()

    if command == "ask" and question:
        request = f"ask {question}"
    else:
        request = command

    try:
        result = await agent.handle_request(pr_url, request)
    except Exception as e:
        print(f"\n\033[91mPR-Agent error:\033[0m {e}\n", file=sys.stderr)
        sys.exit(1)

    if not result:
        print(
            "\n\033[93mWarning:\033[0m PR-Agent returned no result. "
            "The PR may not exist or the command may not be supported.\n",
            file=sys.stderr,
        )
