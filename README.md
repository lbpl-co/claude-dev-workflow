# CDV — Claude Dev Workflow

A Claude Code plugin with slash commands for disciplined developer workflows: GitHub issue tracking, JIRA ticket management, Bitbucket PR creation, and code review.

## Commands

| Command | What it does |
|---------|-------------|
| `/cdv:setup` | Interactive onboarding — pick your integrations, guided setup |
| `/cdv:gh-issue #123` | Work on a GitHub issue (status-driven: analysis → development) |
| `/cdv:jira-ticket PROJ-123` | Work on a JIRA ticket (two-phase: analyse → develop) |
| `/cdv:bb-pr` | Create a structured Bitbucket PR from current branch |
| `/cdv:bb-prreview 42` | Review a Bitbucket PR with inline comments |

## Install

```bash
# 1. Add the marketplace (one-time)
claude plugin marketplace add lbpl-co/claude-dev-workflow

# 2. Install the plugin
claude plugin install cdv@lead-cdv --scope user
```

Then run `/cdv:setup` to configure your integrations.

> **Project-only install:** Use `--scope project` instead of `--scope user` to limit to one project.

## Setup

Run `/cdv:setup` in any Claude session — it walks you through everything interactively.

Or see [SETUP.md](./SETUP.md) for manual setup instructions.

## Requirements by command

| Command | Needs |
|---------|-------|
| `/cdv:gh-issue` | `gh` CLI + `GITHUB_TOKEN` + `jq` |
| `/cdv:jira-ticket` | JIRA MCP + Bitbucket MCP |
| `/cdv:bb-pr` | Bitbucket MCP |
| `/cdv:bb-prreview` | Bitbucket MCP (read + write) |
