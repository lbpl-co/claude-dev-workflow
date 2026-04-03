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
- JIRA MCP (`sooperset/mcp-atlassian`) — see [SETUP.md](./SETUP.md)
- Bitbucket MCP (`aashari/mcp-server-atlassian-bitbucket`) — see [SETUP.md](./SETUP.md)

---

### `create-pr`
Creates a structured Bitbucket pull request from the current branch. Generates title, description, and test plan checklist. Optionally links a JIRA ticket.

**Trigger:** "Create a PR" or "open a PR"

**Requirements:**
- Bitbucket MCP (`aashari/mcp-server-atlassian-bitbucket`) — see [SETUP.md](./SETUP.md)

---

### `review-pr`
Reviews a Bitbucket PR. Fetches diff via Bitbucket MCP, produces a structured terminal review (blocking issues, suggestions, nits, verdict), then optionally posts inline comments to Bitbucket.

**Trigger:** "Review PR 42" or "Review https://bitbucket.org/.../pull-requests/42"

**Requirements:**
- Bitbucket MCP read (`bitbucket-mcp`) + write (`aashari/mcp-server-atlassian-bitbucket`) — see [SETUP.md](./SETUP.md)

---

## Install

```bash
claude plugin install github:lbpl-co/claude-dev-workflow
```

## Setup

JIRA and Bitbucket authentication is handled via MCP servers — no environment variables needed for those skills.

The only env var required is:

| Variable | Used by | Description |
|----------|---------|-------------|
| `GITHUB_TOKEN` | `working-on-github-issue` | GitHub PAT for uploading screenshots |

**Full setup instructions:** see [SETUP.md](./SETUP.md)
