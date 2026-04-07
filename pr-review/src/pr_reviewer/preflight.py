"""Preflight checks: Ollama reachability, model availability, config validation."""

from __future__ import annotations

import sys
from pathlib import Path

import httpx

CONFIG_DIR = Path(__file__).resolve().parent.parent.parent / "config"


def load_secrets() -> dict:
    """Load .secrets.toml, falling back to env vars."""
    secrets_path = CONFIG_DIR / ".secrets.toml"

    ollama_base = "http://localhost:11434"
    bb_username = ""
    bb_app_password = ""

    if secrets_path.exists():
        if sys.version_info >= (3, 11):
            import tomllib
        else:
            import tomli as tomllib
        with open(secrets_path, "rb") as f:
            data = tomllib.load(f)
        ollama_base = data.get("ollama", {}).get("api_base", ollama_base)
        bb_username = data.get("bitbucket", {}).get("username", bb_username)
        bb_app_password = data.get("bitbucket", {}).get("app_password", bb_app_password)

    import os
    bb_username = os.environ.get("BITBUCKET_USERNAME", bb_username)
    bb_app_password = os.environ.get("BITBUCKET_APP_PASSWORD", bb_app_password)

    return {
        "ollama_api_base": ollama_base,
        "bitbucket_username": bb_username,
        "bitbucket_app_password": bb_app_password,
    }


def check_ollama(api_base: str, model: str) -> None:
    """Verify Ollama is running and the requested model is available."""
    # 1. Reachability
    try:
        resp = httpx.get(f"{api_base}/api/tags", timeout=5)
        resp.raise_for_status()
    except httpx.ConnectError:
        _fail(
            f"Cannot reach Ollama at {api_base}.\n"
            "Start it with: OLLAMA_CONTEXT_LENGTH=131072 ollama serve"
        )
    except httpx.HTTPStatusError as e:
        _fail(f"Ollama returned HTTP {e.response.status_code} at {api_base}/api/tags")

    # 2. Model availability — resolve short name to full tag
    model_name = model.removeprefix("ollama/")
    tags = resp.json()
    available = [m["name"] for m in tags.get("models", [])]

    # Check exact match first, then base name match
    if model_name not in available:
        base_matches = [n for n in available if n.split(":")[0] == model_name]
        if base_matches:
            # Return the resolved full name so caller can use it
            return base_matches[0]
        _fail(
            f"Model '{model_name}' not found in Ollama.\n"
            f"Available: {', '.join(available) or '(none)'}\n"
            f"Pull it with: ollama pull {model_name}"
        )
    return model_name


def check_bitbucket_credentials(username: str, app_password: str) -> None:
    """Verify Bitbucket credentials are configured."""
    missing = []
    if not username:
        missing.append("username")
    if not app_password:
        missing.append("app_password")

    if missing:
        _fail(
            f"Bitbucket {' and '.join(missing)} not configured.\n\n"
            "Option 1: Add to config/.secrets.toml:\n"
            "  [bitbucket]\n"
            '  username = "your-bitbucket-username"\n'
            '  app_password = "your-app-password"\n\n'
            "Option 2: Set environment variables:\n"
            "  export BITBUCKET_USERNAME=your-username\n"
            "  export BITBUCKET_APP_PASSWORD=your-app-password\n\n"
            "Create an App Password at:\n"
            "  Bitbucket → Personal settings → App passwords\n"
            "  Scopes needed: pullrequest:read, pullrequest:write"
        )


def _fail(msg: str) -> None:
    print(f"\n\033[91mError:\033[0m {msg}\n", file=sys.stderr)
    sys.exit(1)


def _warn(msg: str) -> None:
    print(f"\n\033[93mWarning:\033[0m {msg}\n", file=sys.stderr)
