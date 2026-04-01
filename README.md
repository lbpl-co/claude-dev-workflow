# claude-dev-workflow

A Claude Code plugin that enforces disciplined developer workflows: two-phase issue/ticket analysis before coding, structured Bitbucket PRs, and inline PR review.

## Skills

### `working-on-github-issue`
Two-phase GitHub issue workflow (Analyse → Develop). Keeps GitHub Issues and project boards up to date.

**Trigger:** "Work on issue #295"

**Requirements:**
- `gh` CLI authenticated (`gh auth login`)
- `GITHUB_TOKEN` env var set
- Issue must be on a GitHub Projects board

---

### `working-on-jira-ticket`
Two-phase JIRA ticket workflow (Analyse → Develop). Reads all ticket fields, posts analysis + milestone comments to JIRA, creates a Bitbucket PR at the end.

**Trigger:** "Work on PROJ-123" or "pick up ticket PROJ-123"

**Requirements:**
- `JIRA_TOKEN` — JIRA API token (Atlassian account settings → Security → API tokens)
- `JIRA_BASE_URL` — e.g. `https://myorg.atlassian.net`
- `BITBUCKET_TOKEN` — Bitbucket App Password with `pullrequest:write` scope
- `jq` installed

---

### `create-pr`
Creates a structured Bitbucket pull request from the current branch. Generates title, description, and test plan checklist. Optionally links a JIRA ticket.

**Trigger:** "Create a PR" or "open a PR"

**Requirements:**
- `BITBUCKET_TOKEN` — Bitbucket App Password with `pullrequest:write` scope
- `JIRA_BASE_URL` — only needed if linking a JIRA ticket
- `jq` installed

---

### `review-pr`
Reviews a Bitbucket PR. Fetches diff via Bitbucket MCP, produces a structured terminal review (blocking issues, suggestions, nits, verdict), then optionally posts inline comments to Bitbucket.

**Trigger:** "Review PR 42" or "Review https://bitbucket.org/.../pull-requests/42"

**Requirements:**
- `BITBUCKET_TOKEN` — Bitbucket App Password with `pullrequest:write` scope
- Bitbucket MCP configured
- `jq` installed

---

## Install

```bash
claude plugin install github:lbpl-co/claude-dev-workflow
```

## Environment variables

| Variable | Used by | Description |
|----------|---------|-------------|
| `GITHUB_TOKEN` | `working-on-github-issue` | GitHub PAT for uploading screenshots |
| `JIRA_TOKEN` | `working-on-jira-ticket` | JIRA API token |
| `JIRA_BASE_URL` | `working-on-jira-ticket`, `create-pr` | e.g. `https://myorg.atlassian.net` |
| `BITBUCKET_TOKEN` | `create-pr`, `review-pr`, `working-on-jira-ticket` | Bitbucket App Password |

Add to your shell profile (`~/.zshrc` or `~/.bashrc`):
```bash
export JIRA_TOKEN="your-token"
export JIRA_BASE_URL="https://myorg.atlassian.net"
export BITBUCKET_TOKEN="your-token"
export GITHUB_TOKEN="your-token"
```
