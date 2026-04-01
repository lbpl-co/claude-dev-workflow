---
name: review-pr
description: Use when the user wants to review a Bitbucket pull request. Fetches the PR diff via Bitbucket MCP, produces a structured inline review in the terminal, then optionally posts comments back to Bitbucket.
---

# Review PR

**Announce at start:** "I'm using the review-pr skill."

## Overview

Reviews a Bitbucket PR: fetches diff and metadata via MCP, produces a structured review in the terminal, then optionally posts inline comments to Bitbucket.

---

## Step 1 — Identify PR

Extract workspace, repo slug, and PR number from what the user provided:
- URL: `https://bitbucket.org/<workspace>/<repo>/pull-requests/<N>`
- Number only: infer workspace + repo from current directory's git remote; if ambiguous, ask.

---

## Step 2 — Fetch PR data

Use Bitbucket MCP tools:

```
mcp__bitbucket-mcp__bb_get_pull_request        → title, description, author, target branch
mcp__bitbucket-mcp__bb_get_pull_request_diff   → full unified diff
mcp__bitbucket-mcp__bb_get_pull_request_comments → existing comments (avoid duplicating feedback)
```

If any MCP tool returns an error (e.g. PR not found), report the error to the user and stop. Do not proceed with an empty or partial diff.

---

## Step 3 — Analyse

Review the diff for:

- **Correctness** — does the code do what the PR claims?
- **Edge cases** — unhandled inputs, error paths, null/empty, concurrency
- **Test coverage** — are the right things tested? are assertions meaningful?
- **Naming and clarity** — is intent obvious without reading internals?
- **Security** — injection, auth gaps, secrets in code, OWASP Top 10
- **Performance** — obvious inefficiencies in hot paths

Do NOT flag issues that are already covered in existing PR comments.

---

## Step 4 — Print review to terminal

```
## PR Review — #<N>: <title>

### Summary
<2-3 sentence overview of the change and overall quality>

### Issues (blocking)
- `path/to/file.ts:42` — <description of problem and suggested fix>

### Suggestions (non-blocking)
- `path/to/file.ts:88` — <improvement suggestion>

### Nits
- <minor style/naming items — grouped, not inline>

### Verdict
**Approve** / **Request Changes** / **Needs Discussion**
<one-sentence rationale>
```

If there are no issues or suggestions, say so explicitly rather than leaving sections empty.

---

## Step 5 — Ask to post

Before posting, verify `BITBUCKET_TOKEN` is set. If it is not set or empty, tell the user:
"BITBUCKET_TOKEN is not set. Set it to a Bitbucket App Password with `pullrequest:write` scope, then re-run."
Stop.

```
Post these comments to Bitbucket? (y/n)
```
If n, stop here.

---

## Step 6 — Post comments via Bitbucket REST API

For each **Issue** and **Suggestion**, post an inline comment at the relevant file + line:

```bash
curl -s -X POST \
  -H "Authorization: Bearer $BITBUCKET_TOKEN" \
  -H "Content-Type: application/json" \
  -d "$(cat <<'PAYLOAD'
{
  "content": {"raw": "<comment text>"},
  "inline": {"to": <line_number>, "path": "<file_path>"}
}
PAYLOAD
)" \
  "https://api.bitbucket.org/2.0/repositories/<workspace>/<repo-slug>/pullrequests/<PR_ID>/comments"
```

Post all **Nits** as a single top-level comment (omit `inline` field) to avoid noise:

```bash
curl -s -X POST \
  -H "Authorization: Bearer $BITBUCKET_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content": {"raw": "**Nits:**\n- <nit 1>\n- <nit 2>"}}' \
  "https://api.bitbucket.org/2.0/repositories/<workspace>/<repo-slug>/pullrequests/<PR_ID>/comments"
```

After each curl call, inspect the response. If it contains `"type":"error"` or the HTTP status is not 2xx, report the error message to the user and stop posting further comments.

---

## Requirements

- `BITBUCKET_TOKEN` — Bitbucket App Password with `pullrequest:write` scope
- Bitbucket MCP configured and authenticated
- `jq` installed (`brew install jq`) — used to inspect curl responses for errors
