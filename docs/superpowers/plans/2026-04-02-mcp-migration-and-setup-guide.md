# MCP Migration + Developer Setup Guide — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace all `curl`/REST calls in the three JIRA/Bitbucket skills with MCP tool calls, remove manual token env vars from those skills, and add a complete developer `SETUP.md` at the repo root.

**Architecture:** `sooperset/mcp-atlassian` handles all JIRA operations; `aashari/mcp-server-atlassian-bitbucket` handles Bitbucket write operations (create PR, post comments, approve/reject). The existing read-only `bitbucket-mcp` is kept for PR diff/metadata reads. Skills become clean prose + MCP tool references with no bash. `README.md` env vars table is trimmed to reflect only `GITHUB_TOKEN` remaining.

**Tech Stack:** Claude Code skill files (Markdown), `sooperset/mcp-atlassian`, `aashari/mcp-server-atlassian-bitbucket`, existing `bitbucket-mcp` (read-only)

---

## File Map

| Action | Path | What changes |
|--------|------|-------------|
| Modify | `skills/working-on-jira-ticket/SKILL.md` | Remove all curl/bash; replace with MCP tool calls; simplify Requirements |
| Modify | `skills/create-pr/SKILL.md` | Replace Step 5 curl with `bb_add_pr`; update Step 3 JIRA URL note; simplify Requirements |
| Modify | `skills/review-pr/SKILL.md` | Replace Step 5 token guard + Step 6 curl with MCP tools; add verdict posting; simplify Requirements |
| Create | `SETUP.md` | Full developer setup guide (zero → working in ~15 min) |
| Modify | `README.md` | Trim env vars table; update requirements per skill |

---

## Task 1: Migrate `working-on-jira-ticket` to JIRA MCP

**Files:**
- Modify: `skills/working-on-jira-ticket/SKILL.md`

- [ ] **Step 1: Read the current file**

```bash
cat skills/working-on-jira-ticket/SKILL.md
```

Confirm lines 37–44 contain the env var guard block (`JIRA_TOKEN`, `JIRA_BASE_URL`).

- [ ] **Step 2: Replace Step 1 — remove env var guard, simplify identification**

Find:
```
Extract the project key and ticket number. The JIRA base URL comes from the `JIRA_BASE_URL` environment variable (e.g. `https://myorg.atlassian.net`).

Before proceeding, verify both required environment variables are set:

```bash
: "${JIRA_TOKEN:?JIRA_TOKEN is not set. Get an API token from Atlassian account settings → Security → API tokens.}"
: "${JIRA_BASE_URL:?JIRA_BASE_URL is not set. Set it to e.g. https://myorg.atlassian.net}"
```

If either is missing, stop and show the error message to the user.
```

Replace with:
```
Extract the project key and issue number. The JIRA MCP handles authentication — no environment variables needed.
```

- [ ] **Step 3: Replace Step 2 — phase detection via MCP**

Find the entire Step 2 section (from the bash block through the two bullet points):
```
Read existing comments on the ticket via JIRA REST API:

```bash
RESPONSE=$(curl -s -w "\n%{http_code}" \
  -H "Authorization: Bearer $JIRA_TOKEN" \
  "$JIRA_BASE_URL/rest/api/3/issue/PROJ-123/comment?orderBy=created")
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_CODE" != "200" ]; then
  echo "ERROR: Could not read JIRA comments (HTTP $HTTP_CODE). Check JIRA_TOKEN and ticket key."
  exit 1
fi

ANALYSIS_COUNT=$(echo "$BODY" \
  | jq -r '.comments[].body.content[0].content[0].text // empty' \
  | grep -c "^## Analysis")
```

- `ANALYSIS_COUNT` is 0 → **Phase 1**
- `ANALYSIS_COUNT` is 1+ → **Phase 2**
```

Replace with:
```
Use the JIRA MCP tool `jira_get_issue` to fetch the issue (includes comments in the response).

Scan the returned comments for any whose body contains the text `## Analysis`.
- No matching comment found → **Phase 1**
- Matching comment found → **Phase 2**
```

- [ ] **Step 4: Replace Step 1a — read ticket via MCP**

Find the entire step 1a section (from the curl bash block through the "Also read existing comments" block):
```
```bash
curl -s \
  -H "Authorization: Bearer $JIRA_TOKEN" \
  "$JIRA_BASE_URL/rest/api/3/issue/PROJ-123?expand=renderedFields" \
  | jq '{
      summary: .fields.summary,
      description: .fields.description,
      status: .fields.status.name,
      priority: .fields.priority.name,
      storyPoints: (.fields.customfield_10028 // .fields.story_points // null),
      sprint: (.fields.customfield_10020[-1].name // .fields.sprint.name // null),
      labels: .fields.labels,
      linkedIssues: [.fields.issuelinks[] | {type: .type.name, key: (.inwardIssue.key // .outwardIssue.key)}],
      acceptanceCriteria: .fields.customfield_10016
    }'
```

Note: Story points field ID varies by JIRA instance — commonly `customfield_10028`. If storyPoints returns null, ask your JIRA admin for the correct custom field ID.
Note: Sprint data is commonly stored in `customfield_10020` on JIRA Cloud. If sprint returns null, check your JIRA instance's custom field IDs.

Also read existing comments:
```bash
curl -s \
  -H "Authorization: Bearer $JIRA_TOKEN" \
  "$JIRA_BASE_URL/rest/api/3/issue/PROJ-123/comment" \
  | jq -r '.comments[] | "\(.author.displayName): \(.body.content[0].content[0].text // "(rich content)")"'
```

Note: `customfield_10016` is a common field ID for acceptance criteria — adjust to your JIRA instance if different.
```

Replace with:
```
Use the JIRA MCP tool `jira_get_issue` with:
- `issue_key`: PROJ-123

Read all returned fields: summary, description, status, priority, story points, sprint, labels, linked issues, acceptance criteria, and all existing comments.

Note: Custom field IDs for story points (commonly `customfield_10028`) and sprint (commonly `customfield_10020`) vary by JIRA instance. Acceptance criteria is commonly `customfield_10016`. If any of these return null, ask your JIRA admin for the correct field IDs for your instance.
```

- [ ] **Step 5: Replace Step 1c — post analysis comment via MCP**

Find the entire step 1c bash block and the two notes below it:
```
```bash
curl -s -X POST \
  -H "Authorization: Bearer $JIRA_TOKEN" \
  -H "Content-Type: application/json" \
  -d "$(cat <<'PAYLOAD'
{
  "body": {
    "type": "doc",
    "version": 1,
    "content": [
      {"type": "heading", "attrs": {"level": 2}, "content": [{"type": "text", "text": "Analysis"}]},
      {"type": "paragraph", "content": [{"type": "text", "text": "Scope: <files, components, APIs affected>"}]},
      {"type": "paragraph", "content": [{"type": "text", "text": "Approach: <how we plan to solve it — key decisions, alternatives considered>"}]},
      {"type": "heading", "attrs": {"level": 3}, "content": [{"type": "text", "text": "AC coverage"}]},
      {"type": "bulletList", "content": [
        {"type": "listItem", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "AC1: <how it will be met>"}]}]},
        {"type": "listItem", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "AC2: <how it will be met>"}]}]}
      ]},
      {"type": "heading", "attrs": {"level": 3}, "content": [{"type": "text", "text": "Files to change"}]},
      {"type": "bulletList", "content": [
        {"type": "listItem", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "path/to/file.ts — <reason>"}]}]}
      ]},
      {"type": "heading", "attrs": {"level": 3}, "content": [{"type": "text", "text": "Risks / open questions"}]},
      {"type": "bulletList", "content": [
        {"type": "listItem", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "<unknowns, edge cases, things needing human input>"}]}]}
      ]}
    ]
  }
}
PAYLOAD
)" \
  "$JIRA_BASE_URL/rest/api/3/issue/PROJ-123/comment"
```

Note: When constructing the actual comment, replace each placeholder in the ADF `text` nodes with real content. Do not embed markdown inside `text` nodes — use proper ADF structure (headings, bulletList, listItem) for formatted output.

If the response contains `"errorMessages"` or the HTTP status is not 201, stop and report the error to the user before proceeding.
```

Replace with:
```
Use the JIRA MCP tool `jira_add_comment` with:
- `issue_key`: PROJ-123
- `comment`: write in Markdown — the MCP converts to JIRA's ADF format automatically

Use this template for the comment body:

```markdown
## Analysis

**Scope:** <files, components, APIs affected>

**Approach:** <how we plan to solve it — key decisions, alternatives considered>

**AC coverage:**
- AC1: <how it will be met>
- AC2: <how it will be met>

**Files to change:**
- `path/to/file.ts` — <reason>

**Risks / open questions:**
- <unknowns, edge cases, things needing human input>
```
```

- [ ] **Step 6: Replace Step 1d — transitions via MCP**

Find the entire step 1d section (both curl blocks and the note):
```
First, get available transitions:
```bash
curl -s \
  -H "Authorization: Bearer $JIRA_TOKEN" \
  "$JIRA_BASE_URL/rest/api/3/issue/PROJ-123/transitions" \
  | jq '.transitions[] | {id, name}'
```

Find the ID for "In Progress" (name varies by project — match case-insensitively). Then apply:
```bash
curl -s -X POST \
  -H "Authorization: Bearer $JIRA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"transition": {"id": "<transition-id>"}}' \
  "$JIRA_BASE_URL/rest/api/3/issue/PROJ-123/transitions"
```

If the transition POST fails (non-204 response or `"errorMessages"` in body), report the error but continue — a failed status transition should not block implementation.
```

Replace with:
```
Use the JIRA MCP tool `jira_get_issue_transitions` with:
- `issue_key`: PROJ-123

Find the transition whose name matches "In Progress" (match case-insensitively — names vary by project).

Use the JIRA MCP tool `jira_transition_issue` with:
- `issue_key`: PROJ-123
- `transition_id`: <id from above>

If the transition fails, report the error but continue — a failed transition should not block implementation.
```

- [ ] **Step 7: Replace Step 1e STOP message — remove env var reference**

Find:
```
Review the analysis at: $JIRA_BASE_URL/browse/PROJ-123
```

Replace with:
```
Review the analysis at: https://<your-org>.atlassian.net/browse/PROJ-123
```

- [ ] **Step 8: Replace Step 2b — start comment via MCP**

Find:
```
```bash
curl -s -X POST \
  -H "Authorization: Bearer $JIRA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"body": {"type": "doc", "version": 1, "content": [{"type": "paragraph", "content": [{"type": "text", "text": "🚧 Starting implementation on branch `feature/PROJ-123-short-description`."}]}]}}' \
  "$JIRA_BASE_URL/rest/api/3/issue/PROJ-123/comment"
```

If this POST fails, note it but continue — a failed start comment should not block implementation.
```

Replace with:
```
Use the JIRA MCP tool `jira_add_comment` with:
- `issue_key`: PROJ-123
- `comment`: `🚧 Starting implementation on branch \`feature/PROJ-123-short-description\`.`

If this fails, note it but continue — a failed start comment should not block implementation.
```

- [ ] **Step 9: Replace Step 2d — milestone comments via MCP**

Find:
```
```bash
curl -s -X POST \
  -H "Authorization: Bearer $JIRA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"body": {"type": "doc", "version": 1, "content": [{"type": "paragraph", "content": [{"type": "text", "text": "✓ <milestone description>"}]}]}}' \
  "$JIRA_BASE_URL/rest/api/3/issue/PROJ-123/comment"
```

Keep it short — one sentence per milestone.
```

Replace with:
```
Use the JIRA MCP tool `jira_add_comment` with:
- `issue_key`: PROJ-123
- `comment`: `✓ <milestone description>`

Keep it short — one sentence per milestone.
```

- [ ] **Step 10: Replace Step 2f — completion comment via MCP**

Find the entire completion comment curl block:
```
```bash
curl -s -X POST \
  -H "Authorization: Bearer $JIRA_TOKEN" \
  -H "Content-Type: application/json" \
  -d "$(cat <<'PAYLOAD'
{
  "body": {
    "type": "doc",
    "version": 1,
    "content": [
      {"type": "heading", "attrs": {"level": 2}, "content": [{"type": "text", "text": "Implementation Complete"}]},
      {"type": "paragraph", "content": [{"type": "text", "text": "PR: <Bitbucket PR URL>"}]},
      {"type": "heading", "attrs": {"level": 3}, "content": [{"type": "text", "text": "What changed"}]},
      {"type": "bulletList", "content": [
        {"type": "listItem", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "<bullet 1>"}]}]},
        {"type": "listItem", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "<bullet 2>"}]}]}
      ]},
      {"type": "paragraph", "content": [{"type": "text", "text": "Tests: <N> passing"}]}
    ]
  }
}
PAYLOAD
)" \
  "$JIRA_BASE_URL/rest/api/3/issue/PROJ-123/comment"
```
```

Replace with:
```
Use the JIRA MCP tool `jira_add_comment` with:
- `issue_key`: PROJ-123
- `comment`:

```markdown
## Implementation Complete

**PR:** <Bitbucket PR URL>

**What changed:**
- <bullet 1>
- <bullet 2>

**Tests:** <N> passing
```
```

- [ ] **Step 11: Replace Step 2g — In Review transition via MCP**

Find:
```
Get transitions and find the ID for "In Review":
```bash
curl -s \
  -H "Authorization: Bearer $JIRA_TOKEN" \
  "$JIRA_BASE_URL/rest/api/3/issue/PROJ-123/transitions" \
  | jq '.transitions[] | {id, name}'
```

Apply:
```bash
curl -s -X POST \
  -H "Authorization: Bearer $JIRA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"transition": {"id": "<transition-id>"}}' \
  "$JIRA_BASE_URL/rest/api/3/issue/PROJ-123/transitions"
```
```

Replace with:
```
Use the JIRA MCP tool `jira_get_issue_transitions` with `issue_key`: PROJ-123.
Find the transition whose name matches "In Review" (case-insensitive).
Use the JIRA MCP tool `jira_transition_issue` with `issue_key`: PROJ-123 and the matched `transition_id`.
```

- [ ] **Step 12: Replace Requirements section**

Find:
```
## Requirements

- `JIRA_TOKEN` — JIRA API token (from Atlassian account settings)
- `JIRA_BASE_URL` — e.g. `https://myorg.atlassian.net`
- `BITBUCKET_TOKEN` — Bitbucket App Password (needed for `create-pr` sub-step)
- `jq` installed (`brew install jq`)
- `curl` available (pre-installed on macOS)
```

Replace with:
```
## Requirements

- JIRA MCP (`sooperset/mcp-atlassian`) configured — see `SETUP.md`
- Bitbucket MCP (`aashari/mcp-server-atlassian-bitbucket`) configured — see `SETUP.md` (used by `create-pr` sub-step)
```

- [ ] **Step 13: Verify the file**

```bash
grep -n "JIRA_TOKEN\|JIRA_BASE_URL\|BITBUCKET_TOKEN\|curl\|jq" skills/working-on-jira-ticket/SKILL.md
```

Expected: no output (zero matches).

- [ ] **Step 14: Commit**

```bash
git add skills/working-on-jira-ticket/SKILL.md
git commit -m "feat: migrate working-on-jira-ticket to use JIRA MCP tools"
```

---

## Task 2: Migrate `create-pr` to Bitbucket MCP

**Files:**
- Modify: `skills/create-pr/SKILL.md`

- [ ] **Step 1: Update Step 3 — remove JIRA_BASE_URL env var reference**

Find:
```
Omit the `## JIRA` section if no ticket was provided, or if `JIRA_BASE_URL` is not set.
If `JIRA_BASE_URL` is not set but a ticket ID was given, include the bare ticket ID as text (e.g. `JIRA: PROJ-123`) rather than a broken link.
`JIRA_BASE_URL` is read from the `JIRA_BASE_URL` environment variable (e.g. `https://myorg.atlassian.net`).
```

Replace with:
```
Omit the `## JIRA` section if no ticket was provided.
For the JIRA link, construct the URL as `https://<your-org>.atlassian.net/browse/PROJ-123` — your org name is the Atlassian subdomain (e.g. if you access JIRA at `mycompany.atlassian.net`, use `mycompany`).
```

- [ ] **Step 2: Replace Step 5 — create PR via MCP**

Find:
```
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
```

Replace with:
```
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
```

- [ ] **Step 3: Replace Requirements section**

Find:
```
## Requirements

- `BITBUCKET_TOKEN` — Bitbucket App Password with `pullrequest:write` scope
- `JIRA_BASE_URL` — e.g. `https://myorg.atlassian.net` (only needed if linking JIRA tickets)
- Must be on a feature branch (not `main` or `master`)
- `jq` installed (`brew install jq`)
```

Replace with:
```
## Requirements

- Bitbucket MCP (`aashari/mcp-server-atlassian-bitbucket`) configured — see `SETUP.md`
- Must be on a feature branch (not `main` or `master`)
```

- [ ] **Step 4: Verify**

```bash
grep -n "BITBUCKET_TOKEN\|JIRA_BASE_URL\|curl\|jq" skills/create-pr/SKILL.md
```

Expected: no output.

- [ ] **Step 5: Commit**

```bash
git add skills/create-pr/SKILL.md
git commit -m "feat: migrate create-pr to use Bitbucket MCP bb_add_pr"
```

---

## Task 3: Migrate `review-pr` to Bitbucket MCP

**Files:**
- Modify: `skills/review-pr/SKILL.md`

- [ ] **Step 1: Replace Step 5 — remove BITBUCKET_TOKEN guard**

Find:
```
Before posting, verify `BITBUCKET_TOKEN` is set. If it is not set or empty, tell the user:
"BITBUCKET_TOKEN is not set. Set it to a Bitbucket App Password with `pullrequest:write` scope, then re-run."
Stop.

```
Post these comments to Bitbucket? (y/n)
```
If n, stop here.
```

Replace with:
```
```
Post these comments to Bitbucket? (y/n)
```
If n, stop here.
```

- [ ] **Step 2: Replace Step 6 — post comments + verdict via MCP**

Find the entire Step 6 section (heading through the end of the Requirements section's preceding content):
```
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
```

Replace with:
```
## Step 6 — Post comments + verdict via Bitbucket MCP

For each **Issue** and **Suggestion**, use the Bitbucket MCP tool `bb_add_pr_comment` with:
- `workspace`: <workspace>
- `repo_slug`: <repo-slug>
- `pr_id`: <PR number>
- `content`: <comment text>
- `inline_to`: <line number>
- `path`: <file path>

For **Nits**, use `bb_add_pr_comment` with `content`: `**Nits:**\n- <nit 1>\n- <nit 2>` and no `inline_to`/`path` — posts as a top-level comment.

For the **verdict**:
- **Approve** → use Bitbucket MCP tool `bb_approve_pr` with `workspace`, `repo_slug`, `pr_id`
- **Request Changes** → use Bitbucket MCP tool `bb_reject_pr` with `workspace`, `repo_slug`, `pr_id`
- **Needs Discussion** → use `bb_add_pr_comment` with a summary of what needs to be discussed before merge
```

- [ ] **Step 3: Replace Requirements section**

Find:
```
## Requirements

- `BITBUCKET_TOKEN` — Bitbucket App Password with `pullrequest:write` scope
- Bitbucket MCP configured and authenticated
- `jq` installed (`brew install jq`) — used to inspect curl responses for errors
```

Replace with:
```
## Requirements

- Bitbucket MCP read (`bitbucket-mcp`) configured — for fetching PR diff and metadata (Steps 1–2)
- Bitbucket MCP write (`aashari/mcp-server-atlassian-bitbucket`) configured — for posting comments and verdict (Step 6)
- See `SETUP.md` for both
```

- [ ] **Step 4: Verify**

```bash
grep -n "BITBUCKET_TOKEN\|curl\|jq" skills/review-pr/SKILL.md
```

Expected: no output.

- [ ] **Step 5: Commit**

```bash
git add skills/review-pr/SKILL.md
git commit -m "feat: migrate review-pr to use Bitbucket MCP for comments and verdict"
```

---

## Task 4: Create `SETUP.md`

**Files:**
- Create: `SETUP.md`

- [ ] **Step 1: Create the file**

Create `SETUP.md` at repo root with this exact content:

````markdown
# Developer Setup Guide

Get all four `claude-dev-workflow` skills working in ~15 minutes.

---

## Prerequisites

- **macOS** or Linux
- **Node.js 18+** — check: `node --version`; install via [nodejs.org](https://nodejs.org) or `brew install node`
- **git** — pre-installed on macOS
- **Homebrew** (macOS only) — install at [brew.sh](https://brew.sh)

---

## 1. Install Claude CLI

```bash
npm install -g @anthropic-ai/claude-code
```

Log in:
```bash
claude login
```

Follow the browser prompt to authenticate with your Anthropic account.

Verify:
```bash
claude --version
# Expected: prints a version number
```

---

## 2. Install this plugin

```bash
claude plugin install github:lbpl-co/claude-dev-workflow
```

Verify:
```bash
claude plugin list
# Expected: "claude-dev-workflow" appears in the list
```

---

## 3. MCP: JIRA (`sooperset/mcp-atlassian`)

**Required by:** `working-on-jira-ticket`

### 3a. Get a JIRA API token

1. Go to [id.atlassian.com/manage-profile/security/api-tokens](https://id.atlassian.com/manage-profile/security/api-tokens)
2. Click **Create API token**
3. Label it `claude-code`, click Create, and **copy the token immediately** (it won't be shown again)

### 3b. Find your Atlassian subdomain

Your subdomain is the part before `.atlassian.net` in your JIRA URL.
Example: if JIRA is at `https://acme.atlassian.net`, your subdomain is `acme`.

### 3c. Add MCP to Claude settings

Open (or create) `~/.claude/settings.json` and add the `mcpServers` block:

```json
{
  "mcpServers": {
    "mcp-atlassian": {
      "command": "npx",
      "args": ["-y", "@sooperset/mcp-atlassian"],
      "env": {
        "JIRA_URL": "https://your-org.atlassian.net",
        "JIRA_USERNAME": "you@yourcompany.com",
        "JIRA_API_TOKEN": "your-api-token-here"
      }
    }
  }
}
```

Replace:
- `your-org` → your Atlassian subdomain (from 3b)
- `you@yourcompany.com` → your Atlassian account email
- `your-api-token-here` → token from step 3a

### 3d. Verify

Start a **new** Claude session (settings are loaded at startup):
```
claude
```

Then type:
```
List my open JIRA issues
```

Expected: Claude lists your open JIRA tickets. If you see an error, check the `JIRA_URL` and token in `settings.json`.

---

## 4. MCP: Bitbucket (`aashari/mcp-server-atlassian-bitbucket`)

**Required by:** `working-on-jira-ticket`, `create-pr`, `review-pr`

### 4a. Create a Bitbucket App Password

1. Go to Bitbucket → click your avatar → **Personal settings**
2. In the left sidebar, click **App passwords**
3. Click **Create app password**
4. Label it `claude-code`
5. Enable these permissions:
   - **Repositories:** Read
   - **Pull requests:** Read, Write
6. Click Create and **copy the password immediately**

### 4b. Find your Bitbucket workspace slug

Your workspace slug appears in Bitbucket URLs: `bitbucket.org/<workspace>/...`
Example: if your repos are at `bitbucket.org/acme-inc/...`, the workspace slug is `acme-inc`.

### 4c. Add MCP to Claude settings

Add the following entry inside the `mcpServers` object in `~/.claude/settings.json` (alongside the `mcp-atlassian` entry from step 3):

```json
"mcp-server-atlassian-bitbucket": {
  "command": "npx",
  "args": ["-y", "@aashari/mcp-server-atlassian-bitbucket"],
  "env": {
    "ATLASSIAN_SITE_NAME": "your-workspace",
    "ATLASSIAN_USER_EMAIL": "you@yourcompany.com",
    "ATLASSIAN_API_TOKEN": "your-app-password-here"
  }
}
```

Replace:
- `your-workspace` → workspace slug from step 4b
- `you@yourcompany.com` → your Bitbucket account email
- `your-app-password-here` → app password from step 4a

### 4d. Verify

Start a new Claude session and type:
```
List pull requests in repo <one-of-your-repo-names>
```

Expected: Claude lists open PRs from that Bitbucket repo.

---

## 5. GitHub token (`working-on-github-issue` only)

Skip this section if your team only uses JIRA, not GitHub Issues.

### 5a. Create a GitHub Personal Access Token

1. Go to GitHub → **Settings** → **Developer settings** → **Personal access tokens** → **Tokens (classic)**
2. Click **Generate new token (classic)**
3. Give it a note: `claude-code`
4. Select scope: `repo`
5. Click **Generate token** and copy it

### 5b. Add to shell profile

```bash
echo 'export GITHUB_TOKEN="your-github-token"' >> ~/.zshrc
source ~/.zshrc
```

### 5c. Authenticate the `gh` CLI

```bash
brew install gh
gh auth login
```

Follow the prompts to authenticate via browser.

---

## 6. Complete `settings.json` example

Your finished `~/.claude/settings.json`:

```json
{
  "mcpServers": {
    "mcp-atlassian": {
      "command": "npx",
      "args": ["-y", "@sooperset/mcp-atlassian"],
      "env": {
        "JIRA_URL": "https://your-org.atlassian.net",
        "JIRA_USERNAME": "you@yourcompany.com",
        "JIRA_API_TOKEN": "your-jira-api-token"
      }
    },
    "mcp-server-atlassian-bitbucket": {
      "command": "npx",
      "args": ["-y", "@aashari/mcp-server-atlassian-bitbucket"],
      "env": {
        "ATLASSIAN_SITE_NAME": "your-workspace",
        "ATLASSIAN_USER_EMAIL": "you@yourcompany.com",
        "ATLASSIAN_API_TOKEN": "your-bitbucket-app-password"
      }
    }
  }
}
```

> **If you already have other MCPs configured:** add the two new entries inside your existing `mcpServers` object — don't replace the whole file.

---

## 7. Verify all skills

Open a terminal, `cd` into any git repository, and start Claude:

```bash
cd ~/your-project
claude
```

Run each check:

| Skill | What to type | Expected |
|-------|-------------|----------|
| JIRA MCP | `List my open JIRA issues` | Lists your JIRA tickets |
| Bitbucket MCP | `List PRs in repo <repo-name>` | Lists open PRs |
| `working-on-jira-ticket` | `work on PROJ-123` | Reads ticket, posts analysis to JIRA, stops for "develop" |
| `create-pr` | `create a PR` (on a feature branch) | Drafts and creates PR on Bitbucket |
| `review-pr` | `review PR 42` | Fetches diff, prints structured review |
| `working-on-github-issue` | `work on issue #1 --repo owner/repo` | Reads GitHub issue, posts analysis comment |

---

## Quick reference

| Skill | Trigger | Needs |
|-------|---------|-------|
| `working-on-github-issue` | "Work on issue #N" | `gh` CLI + `GITHUB_TOKEN` |
| `working-on-jira-ticket` | "Work on PROJ-123" | JIRA MCP (step 3) |
| `create-pr` | "Create a PR" | Bitbucket MCP (step 4) |
| `review-pr` | "Review PR 42" | Both Bitbucket MCPs (steps 3 read + 4 write) |

---

## Troubleshooting

**MCP tools not available / "tool not found"**
- You must start a **new** Claude session after editing `settings.json`
- Check for JSON syntax errors (missing comma, unclosed brace): `python3 -m json.tool ~/.claude/settings.json`
- Run `claude --list-tools | grep jira` to confirm the JIRA MCP loaded

**JIRA: 401 Unauthorized**
- API token may have expired — regenerate at [id.atlassian.com/manage-profile/security/api-tokens](https://id.atlassian.com/manage-profile/security/api-tokens)
- Confirm `JIRA_USERNAME` is your **email address**, not your display name

**Bitbucket: 403 Forbidden when creating PR**
- App password must have **Pull requests: Write** permission enabled
- Regenerate the app password and update `settings.json`

**`gh` CLI: "not logged in"**
- Run `gh auth login` and complete the browser flow
````

- [ ] **Step 2: Verify file created**

```bash
grep "^## " SETUP.md
```

Expected:
```
## Prerequisites
## 1. Install Claude CLI
## 2. Install this plugin
## 3. MCP: JIRA (`sooperset/mcp-atlassian`)
## 4. MCP: Bitbucket (`aashari/mcp-server-atlassian-bitbucket`)
## 5. GitHub token (`working-on-github-issue` only)
## 6. Complete `settings.json` example
## 7. Verify all skills
## Quick reference
## Troubleshooting
```

- [ ] **Step 3: Commit**

```bash
git add SETUP.md
git commit -m "docs: add developer setup guide for MCPs and plugin"
```

---

## Task 5: Update `README.md`

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Update `working-on-jira-ticket` requirements**

Find:
```
**Requirements:**
- `JIRA_TOKEN` — JIRA API token (Atlassian account settings → Security → API tokens)
- `JIRA_BASE_URL` — e.g. `https://myorg.atlassian.net`
- `BITBUCKET_TOKEN` — Bitbucket App Password with `pullrequest:write` scope
- `jq` installed
```

Replace with:
```
**Requirements:**
- JIRA MCP (`sooperset/mcp-atlassian`) — see [SETUP.md](./SETUP.md)
- Bitbucket MCP (`aashari/mcp-server-atlassian-bitbucket`) — see [SETUP.md](./SETUP.md)
```

- [ ] **Step 2: Update `create-pr` requirements**

Find:
```
**Requirements:**
- `BITBUCKET_TOKEN` — Bitbucket App Password with `pullrequest:write` scope
- `JIRA_BASE_URL` — only needed if linking a JIRA ticket
- `jq` installed
```

Replace with:
```
**Requirements:**
- Bitbucket MCP (`aashari/mcp-server-atlassian-bitbucket`) — see [SETUP.md](./SETUP.md)
```

- [ ] **Step 3: Update `review-pr` requirements**

Find:
```
**Requirements:**
- `BITBUCKET_TOKEN` — Bitbucket App Password with `pullrequest:write` scope
- Bitbucket MCP configured
- `jq` installed
```

Replace with:
```
**Requirements:**
- Bitbucket MCP read (`bitbucket-mcp`) + write (`aashari/mcp-server-atlassian-bitbucket`) — see [SETUP.md](./SETUP.md)
```

- [ ] **Step 4: Replace the environment variables section**

Find:
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
```

Replace with:
```
## Setup

JIRA and Bitbucket authentication is handled via MCP servers — no environment variables needed for those skills.

The only env var required is:

| Variable | Used by | Description |
|----------|---------|-------------|
| `GITHUB_TOKEN` | `working-on-github-issue` | GitHub PAT for uploading screenshots |

**Full setup instructions:** see [SETUP.md](./SETUP.md)
```

- [ ] **Step 5: Verify**

```bash
grep -n "JIRA_TOKEN\|BITBUCKET_TOKEN\|JIRA_BASE_URL" README.md
```

Expected: no output.

- [ ] **Step 6: Commit**

```bash
git add README.md
git commit -m "docs: update README to reflect MCP-based auth, link to SETUP.md"
```

---

## Final Check

- [ ] **Verify no curl/token references remain in skill files**

```bash
grep -rn "JIRA_TOKEN\|JIRA_BASE_URL\|BITBUCKET_TOKEN\|curl -s" skills/
```

Expected: no output.

- [ ] **Verify SETUP.md exists at repo root**

```bash
ls SETUP.md
```

Expected: `SETUP.md`

- [ ] **Verify clean git state**

```bash
git status
```

Expected: `nothing to commit, working tree clean`
