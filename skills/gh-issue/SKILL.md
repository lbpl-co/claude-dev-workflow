---
name: gh-issue
description: "MUST use when the message contains a GitHub issue reference — URL (github.com/.../issues/N) or number (#N) — regardless of other content in the message. This skill takes priority over any other skill when a GitHub issue is referenced. Reads issue status from GitHub Projects and adapts: analysis, development, or resume. Always confirms with the user before acting."
---

# Working on a GitHub Issue

**Announce at start:** "I'm using the /cdv:gh-issue skill."

## Overview

This skill reads the issue's current status from GitHub Projects and adapts its behaviour accordingly. It always confirms with the user before taking action.

```
User: "work on issue #123"
        │
        ▼
  Read issue + detect status
        │
        ├── Todo / In Analysis / No status → Analysis flow
        ├── In Progress                    → Development flow
        ├── In Review / Done               → Inform user, ask what to do
        └── Ambiguous                      → Ask user
```

**Things to keep updated on the issue (whenever relevant):**
- **Status** — move it forward as work progresses
- **Analysis comment** — post or update when analysis is done
- **Development plan comment** — post when dev approach is confirmed
- **Task Type** — set during analysis (Bug, Feature, Chore, etc.)
- **Size** — set during analysis (inferred from complexity)
- **Estimate** — set during analysis (numeric, inferred from size)
- **Iteration** — set when development starts
- **End date** — set when development starts

---

## Step 0 — Preflight checks

Before anything else, verify the required tools are available:

```bash
gh --version
```

**If `gh` is not installed:**
```
The GitHub CLI (gh) is required but not installed.

Install it:
  brew install gh          # macOS
  sudo apt install gh      # Ubuntu/Debian

Then authenticate:
  gh auth login
```
Stop and wait for the user to install.

**If `gh` is installed but not authenticated:**
```bash
gh auth status
```

If not logged in:
```
You're not logged in to GitHub. Run:
  gh auth login --scopes "read:org,repo,workflow,read:project,project"

Follow the browser prompt to authenticate.
```
Stop and wait for the user to authenticate.

**If `gh` is authenticated but missing `read:project` scope:**

Check the output of `gh auth status` for the Token scopes line. If `read:project` is not listed:
```
Your GitHub token is missing the "read:project" scope, which is needed
to read and update GitHub Projects status fields.

Re-authenticate with the required scope:
  gh auth login --scopes "read:org,repo,workflow,read:project,project"

This adds the scope on top of your existing ones.
```
Stop and wait for the user to re-authenticate.

**If `jq` is not installed:**
```
jq is required for reading GitHub Projects fields.

Install it:
  brew install jq          # macOS
  sudo apt install jq      # Ubuntu/Debian
```
Stop and wait for the user to install.

Once all checks pass, proceed.

---

## Step 1 — Identify the issue and confirm context

Extract owner, repo, and issue number from what the user provided:
- URL: `https://github.com/owner/repo/issues/123`
- Number only: check current directory's git remote. If ambiguous, ask.

**Always confirm with the user:**

```
I'll be working on issue #<N> in <owner>/<repo>.
Branch to work from: <default-branch>
Does that look right?
```

Wait for confirmation. If the user corrects the repo or branch, use their values.

---

## Step 2 — Read the issue

```bash
gh issue view <N> --repo <owner/repo> --comments
```

Read: title, body, existing comments, labels, assignees.

---

## Step 3 — Detect status

Use the commands in `github-status-helper.md` to read the current GitHub Projects status.

If the issue is not on a project board, tell the user and ask how to proceed.

Route based on status:

| Status | Go to |
|--------|-------|
| `Todo`, `In Analysis`, or no status | **Analysis flow** (Step 4) |
| `In Progress` | **Development flow** (Step 5) |
| `In Review` | Inform user: "This issue is In Review." Ask what they want to do. |
| `Done` | Inform user: "This issue is marked Done." Ask what they want to do. |

---

## Step 4 — Analysis flow

### 4a. Check for existing analysis

Scan issue comments for one starting with `## Analysis`. If found, present it to the user:

```
There's an existing analysis on this issue:
<summary of existing analysis>

Want me to proceed with this, revise it, or start fresh?
```

Wait for user input.

### 4b. Gather inputs

If doing a fresh analysis, make sure you have:
- The full issue description and any linked issues
- The repo and branch to look at (confirmed in Step 1)
- Any context from existing comments

Launch an Explore subagent to understand the codebase around the affected area.

### 4c. Draft analysis and confirm

Present the analysis to the user **before posting**:

```
Here's my analysis — let me know if this looks right before I post it:

## Analysis

**What's the issue:**
<1-3 sentences. Plain description of what's broken or what's needed.>

**Approaches considered:**
1. <Approach A> — <tradeoff>
2. <Approach B> — <tradeoff>

**Recommended approach:** <which one and why, in one sentence>

**Risks / open questions:**
- <genuine unknowns, things that need human input>
```

Wait for user confirmation or edits.

### 4d. Post analysis comment

```bash
gh issue comment <N> --repo <owner/repo> --body "<confirmed analysis>"
```

### 4e. Update project fields

After posting the analysis, update the project item with inferred values. Fetch available options first (use `github-status-helper.md` sections 7–8), then set:

- **Task Type** — infer from the issue: Bug, Feature, Chore, or whichever option best fits. Pick the closest available option.
- **Size** — infer from complexity: XS / S / M / L / XL (or whatever options the project has). Base on scope of change.
- **Estimate** — infer a numeric estimate from size (e.g. S→1, M→3, L→5, XL→8). Use the project's configured scale if visible.

Show the user what you're about to set and confirm:

```
I'll update these project fields:
  Task Type → <value>
  Size      → <value>
  Estimate  → <value>

OK to apply?
```

Apply on confirmation using `github-status-helper.md` sections 7 and 8.

If a field isn't present on this project, skip it silently.

### 4f. Update status → In Analysis

Use `github-status-helper.md` commands to set status to `In Analysis` (if not already).

### 4g. STOP

```
Analysis posted to issue #<N>. Project fields updated. Status set to "In Analysis".
Review at: https://github.com/<owner>/<repo>/issues/<N>

When you're ready to develop, say "develop" or "develop #<N>".
```

Do NOT write implementation code. Do NOT create a branch. Wait for the user.

---

## Step 5 — Development flow

### 5a. Assess current state

Check what exists:
- Is there a feature branch? (`git branch -a | grep issues/<N>`)
- Are there commits on it?
- Is there an open PR?

Present your assessment:

```
Current state for issue #<N>:
- Analysis: <exists / missing>
- Branch: <exists with X commits / doesn't exist>
- PR: <open at URL / none>

<What I recommend doing next and why>

Want me to proceed?
```

Wait for confirmation.

### 5b. Post development plan (if not already posted)

Scan comments for one starting with `## Development Plan`. If none exists, draft one and confirm with user before posting:

```
Here's the development plan — let me know before I post:

## Development Plan

**Changes:**
- <Component/class/model being added or modified> — <what and why>
- <API endpoint> — <what changes>
- <DB model> — <migration needed?>

**Task list:**
1. <concrete step>
2. <concrete step>
3. <concrete step>

**Acceptance criteria:**
- <what "done" looks like, from the issue or inferred>

**Key test cases:**
- <important scenario to test>
- <edge case worth covering>
```

```bash
gh issue comment <N> --repo <owner/repo> --body "<confirmed dev plan>"
```

### 5c. Create branch (if not already created)

```bash
git checkout -b issues/<N>-<short-description> <base-branch>
git push -u origin issues/<N>-<short-description>
```

Update the `branch_link` custom attribute on the issue:

```bash
# Get the item ID and field ID for branch_link using github-status-helper.md pattern
# Then update:
gh project item-edit \
  --project-id <project-node-id> \
  --id <item-node-id> \
  --field-id <branch-link-field-id> \
  --text "issues/<N>-<short-description>"
```

### 5d. Update status and project fields → In Progress

Use `github-status-helper.md` commands to set status to `In Progress` (if not already).

Also set **Iteration** and **End date** if not already filled:

- **Iteration** — list available iterations (section 10 of `github-status-helper.md`) and ask the user which one this work belongs to. If there is only one active iteration, default to it and confirm.
- **End date** — ask the user for the target completion date (or suggest the end of the current iteration if known).

Show combined prompt:

```
Before I start — a couple of project fields to set:
  Iteration → <list available options, or suggest active one>
  End date  → <suggest iteration end date, or ask>

Confirm or adjust:
```

Apply using sections 9 and 10 of `github-status-helper.md`. Skip any field already set.

### 5e. Post start comment

```bash
gh issue comment <N> --repo <owner/repo> --body "🚧 Starting implementation on branch \`issues/<N>-<short-description>\`."
```

### 5f. Implement

Follow test-driven development: write tests first, then implementation.

### 5g. Post milestone comments

After each significant milestone (tests passing, key component done):

```bash
gh issue comment <N> --repo <owner/repo> --body "✓ <milestone description>"
```

One sentence per milestone.

### 5h. Screenshot (if UI changed)

If the change affects visible UI:

```bash
screencapture -x /tmp/issue-<N>-screenshot.png

curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  -F "file=@/tmp/issue-<N>-screenshot.png" \
  "https://uploads.github.com/repos/<owner>/<repo>/issues/assets" \
  | jq -r '.url'
```

### 5i. Finish branch and create PR

Finish the branch: ensure all tests pass, commit all changes, push to remote.
Include `Closes #<N>` in the PR body so GitHub auto-closes the issue on merge.

### 5j. Post completion comment

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

### 5k. Update status → In Review

Use `github-status-helper.md` commands to set status to `In Review`.

---

## Quick Reference

| Status | Action |
|--------|--------|
| Todo / In Analysis / None | Analyse → post analysis → set In Analysis → STOP |
| In Progress | Assess state → dev plan → implement → PR → set In Review |
| In Review / Done | Inform user, ask what to do |

## Issue attributes to keep updated

| Attribute | When to update |
|-----------|---------------|
| **Status** | At each phase transition (In Analysis → In Progress → In Review) |
| **Analysis comment** | After analysis is confirmed by user |
| **Development plan comment** | Before starting implementation, confirmed by user |
| **Task Type** | End of analysis — infer from issue type |
| **Size** | End of analysis — infer from complexity |
| **Estimate** | End of analysis — infer from size |
| **Iteration** | When development starts — ask user |
| **End date** | When development starts — ask user or default to iteration end |

## Red Flags

- **Never** act without confirming with the user first
- **Never** post analysis or dev plan without user review
- **Never** skip asking about repo and branch when there's any ambiguity
- **Never** use labels to track workflow state — use GitHub Projects Status field
- **Never** push code without first posting the start comment
- **Never** claim "done" without a PR link in the completion comment
- **Never** write verbose AI-speak — keep comments concise and human-readable

## Requirements

- `gh` CLI authenticated with required scopes: `gh auth login --scopes "read:org,repo,workflow,read:project,project"`
- `GITHUB_TOKEN` env var set (for screenshot uploads)
- Issue must be on a GitHub Projects board (for status tracking)
- `jq` installed (for parsing project field IDs)
