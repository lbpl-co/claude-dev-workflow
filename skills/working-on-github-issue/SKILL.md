---
name: working-on-github-issue
description: Use when the user asks to work on a GitHub issue (by number or URL). Enforces a two-phase workflow — Analyse first, then Develop — and keeps the issue updated throughout.
---

# Working on a GitHub Issue

**Announce at start:** "I'm using the working-on-github-issue skill."

## Overview

Every GitHub issue goes through two phases before the branch is merged:

```
Phase 1 — Analyse   →   Phase 2 — Develop
  Read issue               Set status → In Develop
  Explore codebase         Create branch
  Post analysis comment    Implement (TDD)
  Set status               Post progress updates
  STOP & wait              Screenshot if UI changed
                           Create PR (Closes #N)
                           Post completion comment
                           Set status → In Review
```

**Hard rule:** Never write implementation code until an analysis comment exists on the issue.

---

## Step 1 — Identify the Issue

Extract owner, repo, and issue number from what the user provided:
- URL: `https://github.com/owner/repo/issues/123`
- Number only: ask the user for the repo if not obvious from context or `CLAUDE.md`

```bash
gh issue view <N> --repo <owner/repo> --comments
```

Read: title, body, existing comments, labels, assignees.

---

## Step 2 — Detect Phase

Scan existing comments for one that starts with `## Analysis` (posted by Claude in a prior session).

- **No analysis comment found** → go to **Phase 1**
- **Analysis comment found** → go to **Phase 2**

---

## Phase 1 — Analyse

### 2a. Explore the codebase

Launch an Explore subagent focused on the affected area. Look for:
- Files mentioned in the issue
- Related components, hooks, utilities
- Existing patterns to reuse

### 2b. Post analysis comment

```bash
gh issue comment <N> --repo <owner/repo> --body "$(cat <<'EOF'
## Analysis

**Scope:** <what this change touches — files, components, APIs>

**Approach:** <how we plan to solve it — key decisions, alternatives considered>

**Files to change:**
- `path/to/file.ts` — <reason>
- `path/to/other.tsx` — <reason>

**Risks / open questions:**
- <any unknowns, edge cases, or things that need human input>
EOF
)"
```

### 2c. Set issue status → In Develop

Use the commands in `github-status-helper.md` to update the GitHub Projects status field.
If the issue is not on a project board, skip this step and note it in the analysis comment.

### 2d. STOP

Inform the user:

```
Analysis posted to issue #<N>. Status set to "In Develop".

Review the analysis at: https://github.com/<owner>/<repo>/issues/<N>

Say "develop" (or "develop #<N>") to begin implementation.
```

Do NOT write any implementation code. Do NOT create a branch. Wait for the user.

---

## Phase 2 — Develop

### 3a. Set status → In Develop (if not already set)

Run the `gh project item-edit` command from `github-status-helper.md`.

### 3b. Create branch and worktree

Use the `superpowers:using-git-worktrees` skill to create an isolated branch named `issues/<N>`.

### 3c. Post start comment

```bash
gh issue comment <N> --repo <owner/repo> --body "🚧 Starting implementation on branch \`issues/<N>\`."
```

### 3d. Implement

Use the `superpowers:test-driven-development` skill. Write tests first, then implementation.

### 3e. Post milestone comments

After each significant milestone (e.g., tests passing, key component done), post a brief progress comment:

```bash
gh issue comment <N> --repo <owner/repo> --body "<milestone description> ✓"
```

Keep it short — one sentence per milestone is enough.

### 3f. Screenshot (if UI changed)

If the change affects any visible UI:

```bash
# Capture
screencapture -x /tmp/issue-<N>-screenshot.png

# Upload to GitHub (returns a URL usable in comments without auth)
curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  -F "file=@/tmp/issue-<N>-screenshot.png" \
  "https://uploads.github.com/repos/<owner>/<repo>/issues/assets" \
  | jq -r '.url'
```

Save the returned URL for the completion comment.

### 3g. Finish branch

Use the `superpowers:finishing-a-development-branch` skill.
When creating the PR, include `Closes #<N>` in the PR body so GitHub auto-links and closes the issue on merge.

### 3h. Post completion comment

```bash
gh issue comment <N> --repo <owner/repo> --body "$(cat <<'EOF'
## Implementation Complete

**PR:** <PR URL>

**What changed:**
- <bullet 1>
- <bullet 2>

**Tests:** <N> passing

**Screenshot:** ![preview](<screenshot-url>)
EOF
)"
```

Omit the Screenshot line if no UI changes.

### 3i. Set status → In Review

Use the commands in `github-status-helper.md` to update status to `In Review`.

---

## Quick Reference

| Phase | Trigger | Key output |
|-------|---------|-----------|
| 1 — Analyse | "work on issue #N" | Analysis comment + status update + STOP |
| 2 — Develop | "develop" | Branch + implementation + PR + completion comment + status → In Review |

## Red Flags

- **Never** skip Phase 1 even if the issue seems trivial
- **Never** use `gh issue edit --label` to track workflow state — use GitHub Projects Status field
- **Never** push code without first posting the start comment (3c)
- **Never** claim "done" without a PR link in the completion comment
