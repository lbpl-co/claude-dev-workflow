"""CLI entrypoint: argument parsing, validation, orchestration."""

from __future__ import annotations

import argparse
import re
import sys

BITBUCKET_PR_PATTERN = re.compile(
    r"https?://bitbucket\.org/[\w.-]+/[\w.-]+/pull-requests/\d+"
)

COMMANDS = ("review", "improve", "describe", "ask")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="pr-review",
        description="Review Bitbucket PRs locally using Ollama + PR-Agent",
    )
    parser.add_argument(
        "pr_url",
        help="Bitbucket PR URL (e.g. https://bitbucket.org/workspace/repo/pull-requests/42)",
    )
    parser.add_argument(
        "command",
        nargs="?",
        default="review",
        choices=COMMANDS,
        help="Command to run (default: review)",
    )
    parser.add_argument(
        "question",
        nargs="?",
        default=None,
        help='Question string (only used with "ask" command)',
    )
    parser.add_argument(
        "--model",
        default="ollama/gemma4",
        help="Ollama model to use (default: ollama/gemma4)",
    )

    args = parser.parse_args()

    # Validate PR URL
    if not BITBUCKET_PR_PATTERN.match(args.pr_url):
        _fail(
            f"Invalid Bitbucket PR URL: {args.pr_url}\n"
            "Expected format: https://bitbucket.org/<workspace>/<repo>/pull-requests/<N>"
        )

    # Validate ask requires a question
    if args.command == "ask" and not args.question:
        _fail('The "ask" command requires a question.\nUsage: pr-review <url> ask "your question"')

    # Ensure model has ollama/ prefix
    model = args.model
    if not model.startswith("ollama/"):
        model = f"ollama/{model}"

    # Preflight checks
    from pr_reviewer.preflight import check_bitbucket_credentials, check_ollama, load_secrets

    secrets = load_secrets()
    resolved_model = check_ollama(secrets["ollama_api_base"], model)
    if resolved_model:
        model = f"ollama/{resolved_model}"
    check_bitbucket_credentials(secrets["bitbucket_username"], secrets["bitbucket_app_password"])

    # Run
    print(f"\nReviewing PR with {model}...")
    print(f"Command: {args.command}")
    print(f"URL: {args.pr_url}\n")

    from pr_reviewer.runner import run_review

    run_review(
        pr_url=args.pr_url,
        command=args.command,
        model=model,
        secrets=secrets,
        question=args.question,
    )


def _fail(msg: str) -> None:
    print(f"\n\033[91mError:\033[0m {msg}\n", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()
