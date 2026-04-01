# Dev Workflow Skills Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add three skills to the `claude-dev-workflow` plugin — `create-pr`, `review-pr`, and `working-on-jira-ticket` — enabling developers to create Bitbucket PRs, review PRs with inline comments, and work through JIRA tickets using a two-phase Analyse → Develop workflow.

**Architecture:** Each skill is a standalone `SKILL.md` in its own directory under `skills/`. `working-on-jira-ticket` invokes `create-pr` as its final sub-step. Bitbucket MCP (read-only) is used to fetch PR data; the Bitbucket REST API (via `curl`) handles writes. JIRA reads use the Atlassian MCP; JIRA writes (comments, transitions) use the JIRA REST API.

**Tech Stack:** Claude Code skills (Markdown), Bitbucket MCP (read), Bitbucket REST API v2 (write), Atlassian MCP (JIRA read), JIRA REST API v3 (write), `git` CLI, `curl`, `jq`

---

## File Map

| Action | Path | Purpose |
|--------|------|---------|
| Create | `skills/create-pr/SKILL.md` | Standalone PR creation skill |
| Create | `skills/review-pr/SKILL.md` | PR review skill (terminal + optional Bitbucket post) |
| Create | `skills/working-on-jira-ticket/SKILL.md` | Two-phase JIRA ticket workflow skill |
| Modify | `plugin.json` | Update description to mention new skills |
| Modify | `README.md` | Document new skills and their requirements |

---

## Task 1: Create `create-pr` skill

**Files:**
- Create: `skills/create-pr/SKILL.md`

- [ ] **Step 1: Create the skill file**

Create `skills/create-pr/SKILL.md` with this exact content:

```markdown
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

Parse workspace and repo slug from the remote URL:
- HTTPS: `https://bitbucket.org/<workspace>/<repo-slug>.git`
- SSH: `git@bitbucket.org:<workspace>/<repo-slug>.git`

Detect default branch:
```bash
git remote show origin | grep "HEAD branch" | awk '{print $NF}'
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
Omit the `## JIRA` section if no ticket was provided.
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
  | jq -r '.links.html.href'
```

Print the returned PR URL.

---

## Requirements

- `BITBUCKET_TOKEN` — Bitbucket App Password with `pullrequest:write` scope
- `JIRA_BASE_URL` — e.g. `https://myorg.atlassian.net` (only needed if linking JIRA tickets)
- Must be on a feature branch (not `main` or `master`)
- `jq` installed (`brew install jq`)
```

- [ ] **Step 2: Verify the file was created correctly**

```bash
cat skills/create-pr/SKILL.md
```
Expected: file exists, frontmatter has `name: create-pr`, all 5 steps present.

- [ ] **Step 3: Commit**

```bash
git add skills/create-pr/SKILL.md
git commit -m "feat: add create-pr skill for Bitbucket PR creation"
```

---

## Task 2: Create `review-pr` skill

**Files:**
- Create: `skills/review-pr/SKILL.md`

- [ ] **Step 1: Create the skill file**

Create `skills/review-pr/SKILL.md` with this exact content:

```markdown
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

---

## Requirements

- `BITBUCKET_TOKEN` — Bitbucket App Password with `pullrequest:write` scope
- Bitbucket MCP configured and authenticated
- `jq` installed (`brew install jq`)
```

- [ ] **Step 2: Verify the file was created correctly**

```bash
cat skills/review-pr/SKILL.md
```
Expected: file exists, frontmatter has `name: review-pr`, all 6 steps present, both curl commands present.

- [ ] **Step 3: Commit**

```bash
git add skills/review-pr/SKILL.md
git commit -m "feat: add review-pr skill for Bitbucket PR review"
```

---

## Task 3: Create `working-on-jira-ticket` skill

**Files:**
- Create: `skills/working-on-jira-ticket/SKILL.md`

- [ ] **Step 1: Create the skill file**

Create `skills/working-on-jira-ticket/SKILL.md` with this exact content:

```markdown
---
name: working-on-jira-ticket
description: Use when the user asks to work on a JIRA ticket (by key e.g. PROJ-123). Enforces a two-phase workflow — Analyse first, then Develop — and keeps the ticket and Bitbucket PR updated throughout.
---

# Working on a JIRA Ticket

**Announce at start:** "I'm using the working-on-jira-ticket skill."

## Overview

Every JIRA ticket goes through two phases before the branch is merged:

```
Phase 1 — Analyse        Phase 2 — Develop
  Read ticket (all fields)   Transition → In Progress
  Explore codebase           Create branch
  Post analysis comment      Implement (TDD)
  Transition → In Progress   Post milestone comments
  STOP & wait                Invoke create-pr skill
                             Post completion comment
                             Transition → In Review
```

**Hard rule:** Never write implementation code until an analysis comment exists on the ticket.

---

## Step 1 — Identify the ticket

Accept any of:
- Ticket key only: `PROJ-123`
- Full URL: `https://myorg.atlassian.net/browse/PROJ-123`

Extract the project key and ticket number. The JIRA base URL comes from the `JIRA_BASE_URL` environment variable (e.g. `https://myorg.atlassian.net`).

---

## Step 2 — Detect phase

Read existing comments on the ticket via JIRA REST API:

```bash
curl -s \
  -H "Authorization: Bearer $JIRA_TOKEN" \
  "$JIRA_BASE_URL/rest/api/3/issue/PROJ-123/comment?orderBy=created" \
  | jq -r '.comments[].body.content[0].content[0].text // empty' \
  | grep -c "^## Analysis"
```

- Result is 0 → **Phase 1**
- Result is 1+ → **Phase 2**

---

## Phase 1 — Analyse

### 1a. Read ticket (all fields)

```bash
curl -s \
  -H "Authorization: Bearer $JIRA_TOKEN" \
  "$JIRA_BASE_URL/rest/api/3/issue/PROJ-123?expand=renderedFields" \
  | jq '{
      summary: .fields.summary,
      description: .fields.description,
      status: .fields.status.name,
      priority: .fields.priority.name,
      storyPoints: .fields.story_points,
      sprint: .fields.sprint.name,
      labels: .fields.labels,
      linkedIssues: [.fields.issuelinks[] | {type: .type.name, key: (.inwardIssue.key // .outwardIssue.key)}],
      acceptanceCriteria: .fields.customfield_10016
    }'
```

Also read existing comments:
```bash
curl -s \
  -H "Authorization: Bearer $JIRA_TOKEN" \
  "$JIRA_BASE_URL/rest/api/3/issue/PROJ-123/comment" \
  | jq -r '.comments[] | "\(.author.displayName): \(.body.content[0].content[0].text // "(rich content)")"'
```

Note: `customfield_10016` is a common field ID for acceptance criteria — adjust to your JIRA instance if different.

### 1b. Explore codebase

Launch an Explore subagent focused on areas mentioned in the ticket summary, description, and acceptance criteria. Look for:
- Files directly mentioned
- Related components, services, hooks, utilities
- Existing patterns to reuse or extend

### 1c. Post analysis comment

```bash
curl -s -X POST \
  -H "Authorization: Bearer $JIRA_TOKEN" \
  -H "Content-Type: application/json" \
  -d "$(cat <<'PAYLOAD'
{
  "body": {
    "type": "doc",
    "version": 1,
    "content": [{
      "type": "paragraph",
      "content": [{"type": "text", "text": "## Analysis\n\n**Scope:** <files, components, APIs affected>\n\n**Approach:** <how we plan to solve it — key decisions, alternatives considered>\n\n**AC coverage:**\n- AC1: <how it will be met>\n- AC2: <how it will be met>\n\n**Files to change:**\n- `path/to/file.ts` — <reason>\n\n**Risks / open questions:**\n- <unknowns, edge cases, things needing human input>"}]
    }]
  }
}
PAYLOAD
)" \
  "$JIRA_BASE_URL/rest/api/3/issue/PROJ-123/comment"
```

### 1d. Transition ticket → In Progress

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

### 1e. STOP

Tell the user:

```
Analysis posted to PROJ-123. Status set to "In Progress".

Review the analysis at: $JIRA_BASE_URL/browse/PROJ-123

Say "develop" (or "develop PROJ-123") to begin implementation.
```

Do NOT write any implementation code. Do NOT create a branch. Wait for the user.

---

## Phase 2 — Develop

### 2a. Create branch

Branch name: `feature/PROJ-123-<short-description>` where `<short-description>` is the ticket title in kebab-case, truncated to 5 words.

```bash
git checkout -b feature/PROJ-123-short-description
git push -u origin feature/PROJ-123-short-description
```

### 2b. Post start comment to JIRA

```bash
curl -s -X POST \
  -H "Authorization: Bearer $JIRA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"body": {"type": "doc", "version": 1, "content": [{"type": "paragraph", "content": [{"type": "text", "text": "🚧 Starting implementation on branch `feature/PROJ-123-short-description`."}]}]}}' \
  "$JIRA_BASE_URL/rest/api/3/issue/PROJ-123/comment"
```

### 2c. Implement

Use the `superpowers:test-driven-development` skill. Write tests first, then implementation.

### 2d. Post milestone comments

After each significant milestone (tests passing, key component done), post a brief JIRA comment:

```bash
curl -s -X POST \
  -H "Authorization: Bearer $JIRA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"body": {"type": "doc", "version": 1, "content": [{"type": "paragraph", "content": [{"type": "text", "text": "✓ <milestone description>"}]}]}}' \
  "$JIRA_BASE_URL/rest/api/3/issue/PROJ-123/comment"
```

Keep it short — one sentence per milestone.

### 2e. Create PR

Invoke the `create-pr` skill. Pass ticket ID `PROJ-123` automatically — no need to ask the user.

### 2f. Post completion comment to JIRA

```bash
curl -s -X POST \
  -H "Authorization: Bearer $JIRA_TOKEN" \
  -H "Content-Type: application/json" \
  -d "$(cat <<'PAYLOAD'
{
  "body": {
    "type": "doc",
    "version": 1,
    "content": [{
      "type": "paragraph",
      "content": [{"type": "text", "text": "## Implementation Complete\n\n**PR:** <Bitbucket PR URL>\n\n**What changed:**\n- <bullet 1>\n- <bullet 2>\n\n**Tests:** <N> passing"}]
    }]
  }
}
PAYLOAD
)" \
  "$JIRA_BASE_URL/rest/api/3/issue/PROJ-123/comment"
```

### 2g. Transition ticket → In Review

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

---

## Quick Reference

| Phase | Trigger | Key output |
|-------|---------|-----------|
| 1 — Analyse | "work on PROJ-123" | Analysis comment + status → In Progress + STOP |
| 2 — Develop | "develop" | Branch + implementation + PR + completion comment + status → In Review |

## Red Flags

- **Never** skip Phase 1 even if the ticket seems trivial
- **Never** create a branch before the analysis comment is posted
- **Never** claim "done" without a PR link in the completion comment
- **Never** guess the JIRA transition ID — always fetch and match by name

## Requirements

- `JIRA_TOKEN` — JIRA API token (from Atlassian account settings)
- `JIRA_BASE_URL` — e.g. `https://myorg.atlassian.net`
- `BITBUCKET_TOKEN` — Bitbucket App Password (needed for `create-pr` sub-step)
- `jq` installed (`brew install jq`)
- `curl` available (pre-installed on macOS)
```

- [ ] **Step 2: Verify the file was created correctly**

```bash
cat skills/working-on-jira-ticket/SKILL.md
```
Expected: file exists, frontmatter has `name: working-on-jira-ticket`, both Phase 1 and Phase 2 sections present, all curl commands present.

- [ ] **Step 3: Commit**

```bash
git add skills/working-on-jira-ticket/SKILL.md
git commit -m "feat: add working-on-jira-ticket skill for two-phase JIRA workflow"
```

---

## Task 4: Update `plugin.json` and `README.md`

**Files:**
- Modify: `plugin.json`
- Modify: `README.md`

- [ ] **Step 1: Update `plugin.json`**

Replace the contents of `.claude-plugin/plugin.json` with:

```json
{
  "name": "claude-dev-workflow",
  "description": "Developer workflow skills: two-phase GitHub issue and JIRA ticket workflows, Bitbucket PR creation, and PR review with inline comments.",
  "author": { "name": "Lead" }
}
```

- [ ] **Step 2: Verify `plugin.json`**

```bash
cat .claude-plugin/plugin.json
```
Expected: description mentions all four skills.

- [ ] **Step 3: Update `README.md`**

Replace the contents of `README.md` with:

```markdown
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
```

- [ ] **Step 4: Verify `README.md`**

```bash
cat README.md | grep "^### "
```
Expected output:
```
### `working-on-github-issue`
### `working-on-jira-ticket`
### `create-pr`
### `review-pr`
```

- [ ] **Step 5: Commit**

```bash
git add .claude-plugin/plugin.json README.md
git commit -m "docs: update plugin.json and README for new skills"
```

---

## Final Check

- [ ] **Verify all four skill files exist**

```bash
ls skills/*/SKILL.md
```
Expected:
```
skills/create-pr/SKILL.md
skills/review-pr/SKILL.md
skills/working-on-github-issue/SKILL.md
skills/working-on-jira-ticket/SKILL.md
```

- [ ] **Verify clean git state**

```bash
git status
```
Expected: `nothing to commit, working tree clean`
