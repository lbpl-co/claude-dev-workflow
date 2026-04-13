---
name: jira-ticket
description: "MUST use when the message contains a JIRA ticket reference — key (PROJ-123) or Atlassian URL — regardless of other content in the message. This skill takes priority over any other skill when a JIRA ticket is referenced. Enforces a two-phase workflow: Analyse first, then Develop. Keeps the ticket and Bitbucket PR updated throughout."
---

# Working on a JIRA Ticket

**Announce at start:** "I'm using the /cdv:jira-ticket skill."

## Overview

Every JIRA ticket goes through two phases before the branch is merged:

```
Phase 1 — Analyse        Phase 2 — Develop
  Read ticket (all fields)   Transition → In Progress
  Explore codebase           Create branch
  Post analysis comment      Implement (TDD)
  Transition → In Progress   Post milestone comments
  STOP & wait                Create PR (manually or via git)
                             Post completion comment
                             Transition → In Review
```

**Hard rule:** Never write implementation code until an analysis comment exists on the ticket.

---

## Step 0 — Preflight checks

Before anything else, verify the required MCP tools are available.

Try calling `jira_get_issue` with a test key. If the tool is not found or returns an auth error:

```
JIRA MCP is not configured. To set it up:

1. Get a JIRA API token: https://id.atlassian.com/manage-profile/security/api-tokens
2. Add to ~/.claude/settings.json under "mcpServers":

   "mcp-atlassian": {
     "command": "npx",
     "args": ["-y", "@sooperset/mcp-atlassian"],
     "env": {
       "JIRA_URL": "https://your-org.atlassian.net",
       "JIRA_USERNAME": "you@yourcompany.com",
       "JIRA_API_TOKEN": "your-token"
     }
   }

3. Restart Claude (settings load at startup).

Full guide: see SETUP.md in the claude-dev-workflow plugin.
```

Stop and wait for the user to configure.

---

## Step 1 — Identify the ticket

Accept any of:
- Ticket key only: `PROJ-123`
- Full URL: `https://myorg.atlassian.net/browse/PROJ-123`

Extract the project key and issue number. The JIRA MCP handles authentication — no environment variables needed.

---

## Step 2 — Detect phase

Use the JIRA MCP tool `jira_get_issue` to fetch the issue (includes comments in the response).

Scan the returned comments for any whose body contains the text `## Analysis`.
- No matching comment found → **Phase 1**
- Matching comment found → **Phase 2**

---

## Phase 1 — Analyse

### 1a. Read ticket (all fields)

Use the JIRA MCP tool `jira_get_issue` with:
- `issue_key`: PROJ-123

Read all returned fields: summary, description, status, priority, story points, sprint, labels, linked issues, acceptance criteria, and all existing comments.

Note: Custom field IDs for story points (commonly `customfield_10028`) and sprint (commonly `customfield_10020`) vary by JIRA instance. Acceptance criteria is commonly `customfield_10016`. If any of these return null, ask your JIRA admin for the correct field IDs for your instance.

### 1b. Explore codebase

Use the `Agent` tool with `subagent_type: "Explore"` and a prompt that includes:
- The ticket summary, key acceptance criteria, and any file names mentioned in the description
- Instructions to find: files directly mentioned, related components/services/hooks/utilities, existing patterns to reuse or extend

The Explore subagent should return a list of relevant files and a brief description of how each relates to the ticket. Use this output to inform the analysis comment in step 1c.

### 1c. Post analysis comment

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

### 1d. Transition ticket → In Progress

Use the JIRA MCP tool `jira_get_issue_transitions` with:
- `issue_key`: PROJ-123

Find the transition whose name matches "In Progress" (match case-insensitively — names vary by project).

Use the JIRA MCP tool `jira_transition_issue` with:
- `issue_key`: PROJ-123
- `transition_id`: <id from above>

If the transition fails, report the error but continue — a failed transition should not block implementation.

### 1e. STOP

Tell the user:

```
Analysis posted to PROJ-123. Status set to "In Progress".

Review the analysis at: https://<your-org>.atlassian.net/browse/PROJ-123

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

Use the JIRA MCP tool `jira_add_comment` with:
- `issue_key`: PROJ-123
- `comment`: `🚧 Starting implementation on branch \`feature/PROJ-123-short-description\`.`

If this fails, note it but continue — a failed start comment should not block implementation.

### 2c. Invoke test-driven-development

Follow test-driven development: write tests first, then implementation. This is mandatory — do not write implementation code without tests.

### 2d. Post milestone comments

After each significant milestone (tests passing, key component done), post a brief JIRA comment:

Use the JIRA MCP tool `jira_add_comment` with:
- `issue_key`: PROJ-123
- `comment`: `✓ <milestone description>`

Keep it short — one sentence per milestone.

### 2e. Post completion comment to JIRA

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

### 2f. Transition ticket → In Review

Use the JIRA MCP tool `jira_get_issue_transitions` with `issue_key`: PROJ-123.
Find the transition whose name matches "In Review" (case-insensitive).
Use the JIRA MCP tool `jira_transition_issue` with `issue_key`: PROJ-123 and the matched `transition_id`.

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

- JIRA MCP (`sooperset/mcp-atlassian`) configured — see `SETUP.md`
- Bitbucket MCP (`aashari/mcp-server-atlassian-bitbucket`) configured — see `SETUP.md`
