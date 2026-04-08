---
name: pr
description: Use when the user wants to create a Bitbucket pull request from the current branch. Generates a structured PR title, description, and test plan. Optionally links a JIRA ticket.
---

# Create PR

**Announce at start:** "I'm using the /cdv:pr skill."

## Overview

Creates a Bitbucket pull request from the current branch with a structured title, description, and test plan.

---

## Step 1 — Read context

```bash
# Current branch
git branch --show-current

# Commits since main (adjust base branch if needed)
git log origin/main..HEAD --oneline

# Files changed
git diff origin/main --stat

# Remote URL — used to extract workspace + repo slug
git remote get-url origin
```

**Guard:** If the current branch is `main` or `master`, stop immediately and tell the user:
"You are on the `main` branch. Please switch to a feature branch before creating a PR."

Parse workspace and repo slug from the remote URL:
- HTTPS: `https://bitbucket.org/<workspace>/<repo-slug>.git`
- SSH: `git@bitbucket.org:<workspace>/<repo-slug>.git`

Detect default branch:
```bash
# Detect default branch (falls back to 'main' if network unavailable)
git remote show origin 2>/dev/null | grep "HEAD branch" | awk '{print $NF}' || echo "main"
```

---

## Step 2 — JIRA ticket

**If invoked by `/cdv:jira`:** the ticket ID (`PROJ-123` or similar) is already present in the conversation context from the parent skill. Use the same ticket key that has been referenced throughout the current conversation. Skip the user prompt and proceed directly to Step 3.

**If invoked standalone:** ask the user:
```
JIRA ticket ID? (e.g. PROJ-123 — press Enter to skip)
```

---

## Step 3 — Generate PR content

Compose:

**Title:** `[PROJ-123] <concise description from commits>` (omit `[PROJ-123]` prefix if no ticket)

**Body:**
~~~markdown
## Summary
- <bullet 1 — what changed and why>
- <bullet 2>

## Test plan
- [ ] <test step derived from the changes>
- [ ] <test step>

## JIRA
[PROJ-123](https://<your-org>.atlassian.net/browse/PROJ-123)
~~~
Omit the `## JIRA` section if no ticket was provided.
For the JIRA link, construct the URL as `https://<your-org>.atlassian.net/browse/PROJ-123` — your org name is the Atlassian subdomain (e.g. if you access JIRA at `mycompany.atlassian.net`, use `mycompany`).

---

## Step 4 — Show draft and confirm

Print the full PR title and body to the terminal. Ask:
```
Create this PR on Bitbucket? (y/n)
```
If n, stop.

---

## Step 5 — Create PR via Bitbucket MCP

Use the Bitbucket MCP tool `bb_add_pr` with:
- `workspace`: <workspace extracted from git remote in Step 1>
- `repo_slug`: <repo-slug extracted from git remote in Step 1>
- `title`: <generated title from Step 3>
- `description`: <generated body from Step 3>
- `source_branch`: <current branch from Step 1>
- `destination_branch`: <default branch from Step 1>
- `close_source_branch`: true

The MCP returns the PR URL. Print it to the terminal.

---

## Requirements

- Bitbucket MCP (`aashari/mcp-server-atlassian-bitbucket`) configured — see `SETUP.md`
- Must be on a feature branch (not `main` or `master`)
