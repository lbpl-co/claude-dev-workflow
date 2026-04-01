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

Before proceeding, verify both required environment variables are set:

```bash
: "${JIRA_TOKEN:?JIRA_TOKEN is not set. Get an API token from Atlassian account settings → Security → API tokens.}"
: "${JIRA_BASE_URL:?JIRA_BASE_URL is not set. Set it to e.g. https://myorg.atlassian.net}"
```

If either is missing, stop and show the error message to the user.

---

## Step 2 — Detect phase

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
      storyPoints: (.fields.customfield_10028 // .fields.story_points // null),
      sprint: .fields.sprint.name,
      labels: .fields.labels,
      linkedIssues: [.fields.issuelinks[] | {type: .type.name, key: (.inwardIssue.key // .outwardIssue.key)}],
      acceptanceCriteria: .fields.customfield_10016
    }'
```

Note: Story points field ID varies by JIRA instance — commonly `customfield_10028`. If storyPoints returns null, ask your JIRA admin for the correct custom field ID.

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

### 2c. Invoke test-driven-development

Invoke the `superpowers:test-driven-development` skill. This is a mandatory step — do not write implementation code without it.

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
