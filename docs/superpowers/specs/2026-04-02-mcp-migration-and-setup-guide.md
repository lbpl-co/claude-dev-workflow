# MCP Migration + Developer Setup Guide
**Date:** 2026-04-02

---

## Goals

1. **MCP migration** — Replace all `curl`/REST calls in `create-pr`, `review-pr`, and `working-on-jira-ticket` with MCP tool calls. Remove manual env var management from those skills.
2. **Setup guide** — Write `SETUP.md` at repo root: a complete, linear walkthrough from zero to all four skills working, covering new developers and existing devs alike.

---

## Context

Current state:
- `working-on-jira-ticket` uses `curl` against JIRA REST API v3 with `JIRA_TOKEN` + `JIRA_BASE_URL`
- `create-pr` uses `curl` against Bitbucket REST API v2 with `BITBUCKET_TOKEN`
- `review-pr` uses Bitbucket MCP (read-only) + `curl` for posting comments with `BITBUCKET_TOKEN`
- All three skills require manual env var setup and contain brittle bash

Target state:
- JIRA operations → `sooperset/mcp-atlassian` (battle-tested community MCP, JIRA Cloud + API token)
- Bitbucket write operations → `aashari/mcp-server-atlassian-bitbucket` (write-capable, Cloud)
- No `curl`, no `JIRA_TOKEN`, no `JIRA_BASE_URL`, no `BITBUCKET_TOKEN` in any skill
- Only remaining token: `GITHUB_TOKEN` for `working-on-github-issue` screenshot uploads

---

## MCP Choices

### JIRA: `sooperset/mcp-atlassian`

- Supports JIRA Cloud with API token auth
- Most widely used community JIRA MCP (battle-tested)
- Install: `npx -y @smithery/cli install @sooperset/mcp-atlassian --client claude`

**Tools used** (prefix `mcp__<server-name>__` varies by MCP config name — verify at install time):

| Operation | Tool (base name) |
|-----------|------|
| Read ticket (all fields) | `jira_get_issue` |
| Read comments | `jira_get_issue_comments` |
| Post comment | `jira_add_comment` |
| Get transitions | `jira_get_issue_transitions` |
| Apply transition | `jira_transition_issue` |

### Bitbucket: `aashari/mcp-server-atlassian-bitbucket`

- Supports Bitbucket Cloud with app password auth
- Full read + write: create PRs, post inline comments, approve/reject
- Install: `npx -y @smithery/cli install @aashari/mcp-server-atlassian-bitbucket --client claude`

**Tools used** (prefix `mcp__<server-name>__` varies by MCP config name — verify at install time):

| Operation | Tool (base name) |
|-----------|------|
| Create PR | `bb_add_pr` |
| Post PR comment (inline or general) | `bb_add_pr_comment` |
| Approve PR | `bb_approve_pr` |
| Decline PR | `bb_reject_pr` |

The existing read-only Bitbucket MCP (`mcp__bitbucket-mcp__*`) remains in place for `bb_get_pull_request_diff` and related read tools — the `aashari` MCP supplements it for writes.

---

## Skill Changes

### `working-on-jira-ticket`

**Remove entirely:**
- `JIRA_TOKEN` / `JIRA_BASE_URL` env var guard block (Step 1)
- All `curl` commands (Steps 2, 1a, 1c, 1d, 2b, 2d, 2f, 2g)
- Manual HTTP status checks on every curl call
- ADF JSON assembly (MCP handles serialisation)
- `jq` requirement

**Replace with:**
- Step 2 (phase detection): call `mcp__mcp-atlassian__jira_get_issue_comments`, scan results for `## Analysis` text
- Step 1a (read ticket): call `mcp__mcp-atlassian__jira_get_issue` with `fields=*all`
- Step 1c (post analysis comment): call `mcp__mcp-atlassian__jira_add_comment` with markdown body (MCP converts to ADF automatically)
- Step 1d (transition → In Progress): call `mcp__mcp-atlassian__jira_get_issue_transitions` then `mcp__mcp-atlassian__jira_transition_issue`
- Steps 2b, 2d, 2f (comments): call `mcp__mcp-atlassian__jira_add_comment`
- Step 2g (transition → In Review): same pattern as 1d

**Note on comment format:** With MCP, analysis comments can be written in plain markdown — no manual ADF node construction needed.

### `create-pr`

**Remove entirely:**
- `BITBUCKET_TOKEN` env var, guard, and all curl commands (Step 5)
- `jq` requirement
- Manual error handling on curl response

**Replace with:**
- Step 5: call `mcp__mcp-server-atlassian-bitbucket__bb_add_pr` with title, description, source branch, destination branch

### `review-pr`

**Remove entirely:**
- `BITBUCKET_TOKEN` env var guard (Step 5)
- Both `curl` commands in Step 6
- `jq` requirement

**Replace with:**
- Step 6: call `mcp__mcp-server-atlassian-bitbucket__bb_add_pr_comment` for each issue/suggestion/nit
- Step 6 verdict: call `mcp__mcp-server-atlassian-bitbucket__bb_approve_pr` or `bb_reject_pr` based on verdict

---

## Setup Guide: `SETUP.md`

Located at repo root. Audience: new devs (read every step) and existing devs (skim to find what they're missing).

### Structure

```
# Developer Setup Guide

## Prerequisites
## 1. Install Claude CLI
## 2. Install the plugin
## 3. MCP: JIRA (sooperset/mcp-atlassian)
## 4. MCP: Bitbucket (aashari)
## 5. GitHub token (working-on-github-issue only)
## 6. Verify setup
## Quick reference
```

### Section detail

**Prerequisites**
- macOS or Linux
- Node.js 18+ (`node --version`)
- `git`
- `jq` (`brew install jq`) — only needed for `working-on-github-issue`

**1. Install Claude CLI**
```bash
npm install -g @anthropic-ai/claude-code
claude login
```

**2. Install the plugin**
```bash
claude plugin install github:lbpl-co/claude-dev-workflow
```

**3. MCP: JIRA**
- Install `sooperset/mcp-atlassian` via Smithery
- Get a JIRA API token from Atlassian account settings
- Configure with Cloud URL + token
- Exact config snippet provided in guide

**4. MCP: Bitbucket**
- Install `aashari/mcp-server-atlassian-bitbucket` via Smithery
- Create a Bitbucket App Password with `pullrequest:write` + `repository:read` scopes
- Configure with workspace + app password
- Exact config snippet provided in guide

**5. GitHub token**
- Only required for `working-on-github-issue`
- Create a GitHub PAT with `repo` scope
- `export GITHUB_TOKEN="..."` in shell profile

**6. Verify setup**
One test per skill:
```
claude "List my open JIRA issues"            # tests JIRA MCP
claude "List PRs in repo X"                  # tests Bitbucket MCP
claude "work on issue #1" --repo owner/repo  # tests full github-issue skill
```

**Quick reference table**

| Skill | Trigger | Requires |
|-------|---------|---------|
| `working-on-github-issue` | "work on issue #N" | gh CLI + GITHUB_TOKEN |
| `working-on-jira-ticket` | "work on PROJ-123" | JIRA MCP |
| `create-pr` | "create a PR" | Bitbucket MCP (aashari) |
| `review-pr` | "review PR 42" | Bitbucket MCP (both) |

---

## What Does NOT Change

- `working-on-github-issue/SKILL.md` — no changes (uses `gh` CLI, no curl to migrate)
- `plugin.json` — no changes
- `README.md` — update env vars table to reflect reduced requirements
- `github-status-helper.md` — no changes

---

## File Map

| Action | Path |
|--------|------|
| Modify | `skills/working-on-jira-ticket/SKILL.md` |
| Modify | `skills/create-pr/SKILL.md` |
| Modify | `skills/review-pr/SKILL.md` |
| Create | `SETUP.md` |
| Modify | `README.md` (env vars table only) |
