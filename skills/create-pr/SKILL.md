---
name: create-pr
description: Use when the user wants to create a Bitbucket pull request from the current branch. Generates a structured PR title, description, and test plan. Optionally links a JIRA ticket.
---

# Create PR

**Announce at start:** "I'm using the create-pr skill."

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

**If invoked by `working-on-jira-ticket`:** ticket ID is already known (passed as context). Skip this step.

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
[PROJ-123]($JIRA_BASE_URL/browse/PROJ-123)
~~~
Omit the `## JIRA` section if no ticket was provided, or if `JIRA_BASE_URL` is not set.
If `JIRA_BASE_URL` is not set but a ticket ID was given, include the bare ticket ID as text (e.g. `JIRA: PROJ-123`) rather than a broken link.
`JIRA_BASE_URL` is read from the `JIRA_BASE_URL` environment variable (e.g. `https://myorg.atlassian.net`).

---

## Step 4 — Show draft and confirm

Print the full PR title and body to the terminal. Ask:
```
Create this PR on Bitbucket? (y/n)
```
If n, stop.

---

## Step 5 — Create PR via Bitbucket REST API

```bash
curl -s -X POST \
  -H "Authorization: Bearer $BITBUCKET_TOKEN" \
  -H "Content-Type: application/json" \
  -d "$(cat <<'PAYLOAD'
{
  "title": "<title>",
  "description": "<body>",
  "source": {"branch": {"name": "<current-branch>"}},
  "destination": {"branch": {"name": "<default-branch>"}},
  "close_source_branch": true
}
PAYLOAD
)" \
  "https://api.bitbucket.org/2.0/repositories/<workspace>/<repo-slug>/pullrequests" \
  | jq -r 'if .type == "error" then "ERROR: \(.error.message)" else .links.html.href end'
```

If the output starts with `ERROR:`, stop and show the error message to the user.

Print the returned PR URL.

---

## Requirements

- `BITBUCKET_TOKEN` — Bitbucket App Password with `pullrequest:write` scope
- `JIRA_BASE_URL` — e.g. `https://myorg.atlassian.net` (only needed if linking JIRA tickets)
- Must be on a feature branch (not `main` or `master`)
- `jq` installed (`brew install jq`)
