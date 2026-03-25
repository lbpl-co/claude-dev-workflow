# claude-dev-workflow

A Claude Code plugin that enforces a two-phase GitHub issue workflow:
**Analyse first, then Develop** — keeping issues well-maintained throughout.

## What it does

When Claude works on a GitHub issue, this plugin ensures:

1. **Phase 1 — Analyse**: Claude reads the issue, explores the codebase, posts an `## Analysis` comment to GitHub, sets the project board status to `In Develop`, then **stops and waits** for your go-ahead.

2. **Phase 2 — Develop**: After you say "develop", Claude creates a branch, implements with TDD, posts milestone progress comments, takes screenshots for UI changes, creates a PR with `Closes #N`, posts a completion summary, and sets status to `In Review`.

## Why

Without discipline, Claude jumps straight to coding with no visibility for the team, leaves issue boards stale, and loses the audit trail that comments provide.

## Install

```bash
claude plugin install github:lbpl-co/claude-dev-workflow
```

## Usage

```
You: Work on issue #295
Claude: [reads issue, explores code, posts analysis comment, sets status, stops]

You: develop
Claude: [creates branch, implements, posts progress, creates PR, posts completion]
```

## Skills included

- **`working-on-github-issue`** — the two-phase issue workflow skill

## Requirements

- `gh` CLI authenticated (`gh auth login`)
- `GITHUB_TOKEN` env var set (for screenshot uploads via GitHub assets API)
- Issue must be on a GitHub Projects board for status updates to work
