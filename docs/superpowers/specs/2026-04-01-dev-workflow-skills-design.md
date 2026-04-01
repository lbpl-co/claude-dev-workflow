# Dev Workflow Skills Design
**Date:** 2026-04-01
**Skills:** `working-on-jira-ticket`, `create-pr`, `review-pr`

---

## Context

This plugin (`claude-dev-workflow`) already ships a `working-on-github-issue` skill that enforces a two-phase Analyse → Develop workflow against GitHub Issues + Bitbucket PRs.

These three new skills extend the plugin for teams that use:
- **JIRA** as their issue tracker (some teams org-wide)
- **Bitbucket** for code and PRs (all teams)
- **GitHub Issues** for some project-level tracking (existing skill covers this)

---

## Architecture

The three skills are independent but composable. `working-on-jira-ticket` invokes `create-pr` as its final sub-step, mirroring how the existing github-issue skill invokes `finishing-a-development-branch`. `create-pr` and `review-pr` both work standalone.

```
working-on-jira-ticket
  └── Phase 1: Analyse  →  STOP
  └── Phase 2: Develop  →  invokes create-pr

create-pr          (standalone or called by working-on-jira-ticket)
review-pr          (fully standalone)
```

**Branch naming convention:** `feature/PROJ-123-short-description`

---

## Skill 1: `working-on-jira-ticket`

### Trigger
User says: "work on PROJ-123", "pick up ticket PROJ-123", or similar.

### Phase Detection
Scan existing JIRA comments for one starting with `## Analysis` (posted by Claude in a prior session).
- No analysis comment → Phase 1
- Analysis comment found → Phase 2

### Phase 1 — Analyse

**Step 1: Read ticket (all fields)**
Read via Atlassian MCP:
- Title, description, acceptance criteria
- Story points, sprint, labels
- Linked issues (blocks/blocked-by)
- Existing comments

**Step 2: Explore codebase**
Launch an Explore subagent focused on areas mentioned in the ticket. Look for affected files, existing patterns, related components.

**Step 3: Post analysis comment to JIRA**
```
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

**Step 4: Transition ticket → In Progress**
Update JIRA ticket status to `In Progress` via Atlassian MCP.

**Step 5: STOP**
Tell the user:
```
Analysis posted to PROJ-123. Status set to "In Progress".

Review the analysis at: <JIRA base URL from Atlassian MCP>/browse/PROJ-123

Say "develop" (or "develop PROJ-123") to begin implementation.
```
Do NOT write any implementation code. Do NOT create a branch.

### Phase 2 — Develop

**Step 1: Create branch**
Branch name: `feature/PROJ-123-<short-description-from-title>` (kebab-case, max 5 words from title).

**Step 2: Post JIRA start comment**
```
🚧 Starting implementation on branch `feature/PROJ-123-...`.
```

**Step 3: Implement**
Use `superpowers:test-driven-development`. Write tests first, then implementation.

**Step 4: Post milestone comments**
After each significant milestone, post a one-sentence JIRA comment:
```
✓ <milestone description>
```

**Step 5: Invoke `create-pr`**
Pass the JIRA ticket ID automatically. `create-pr` handles the Bitbucket PR creation.

**Step 6: Post completion comment to JIRA**
```
## Implementation Complete

**PR:** <Bitbucket PR URL>

**What changed:**
- <bullet 1>
- <bullet 2>

**Tests:** <N> passing
```

**Step 7: Transition ticket → In Review**
Update JIRA ticket status to `In Review` via Atlassian MCP.

### Requirements
- Atlassian MCP configured with JIRA access
- Branch push access to Bitbucket

---

## Skill 2: `create-pr`

### Trigger
- Standalone: "create pr", "create a PR", "open a PR"
- Invoked by `working-on-jira-ticket` (ticket ID passed automatically)

### Steps

**Step 1: Read context**
- Current branch name
- Last N commits (`git log`)
- Diff summary (files changed, lines added/removed)

**Step 2: JIRA ticket**
- If called from `working-on-jira-ticket`: ticket ID already known
- If called standalone: ask developer for optional JIRA ticket ID (e.g. `PROJ-123`). Can be skipped.

**Step 3: Generate PR content**

Title format: `[PROJ-123] Short description` (omit ticket prefix if no ticket provided)

Body:
```markdown
## Summary
<2-4 bullet points describing what changed and why>

## Test plan
- [ ] <test step 1>
- [ ] <test step 2>

## JIRA
[PROJ-123](<JIRA base URL from Atlassian MCP>/browse/PROJ-123)
```
(Omit JIRA section if no ticket provided. JIRA base URL is resolved from the Atlassian MCP configuration at runtime.)

**Step 4: Show draft in terminal**
Print the full PR title + body for the developer to review.

**Step 5: Post to Bitbucket**
Create PR via Bitbucket MCP. Target branch: detected from repo's default branch via Bitbucket MCP; falls back to `main`.

**Step 6: Return PR URL**
Print the Bitbucket PR URL to terminal.

### Requirements
- Bitbucket MCP configured
- Developer must be on a feature branch (not `main`)

---

## Skill 3: `review-pr`

### Trigger
"review PR 42", "review https://bitbucket.org/.../pull-requests/42", "review this PR"

### Steps

**Step 1: Identify PR**
Extract workspace, repo slug, and PR number from what the user provided. If only a number is given and context is ambiguous, ask for the repo.

**Step 2: Fetch PR**
Via Bitbucket MCP:
- PR metadata (title, description, author, target branch)
- Full diff
- Existing comments (to avoid duplicating feedback)

**Step 3: Analyse**
Review for:
- **Correctness:** Does the code do what the PR claims?
- **Edge cases:** Unhandled inputs, error paths, concurrency
- **Test coverage:** Are the right things tested? Are tests meaningful?
- **Naming and clarity:** Is the code easy to follow?
- **Security:** Injection, auth gaps, secrets in code, OWASP top 10
- **Performance:** Obvious inefficiencies in hot paths

**Step 4: Print review to terminal**
```
## PR Review — #42: <title>

### Summary
<2-3 sentence overview of the change and overall quality>

### Issues (blocking)
- `path/to/file.ts:42` — <description of problem and suggested fix>

### Suggestions (non-blocking)
- `path/to/file.ts:88` — <improvement suggestion>

### Nits
- <minor style/naming items>

### Verdict
**Approve** / **Request Changes** / **Needs Discussion**
<one-sentence rationale>
```

**Step 5: Ask to post**
```
Post these comments to Bitbucket? (y/n)
```

**Step 6: Post to Bitbucket (if yes)**
Post inline comments at the relevant file+line positions via Bitbucket MCP. Submit the review with the verdict.

### Requirements
- Bitbucket MCP configured
- Read access to the target repository

---

## Skill Interactions

| Scenario | Skills used |
|----------|-------------|
| Full JIRA ticket flow | `working-on-jira-ticket` → (invokes) `create-pr` |
| Quick PR without ticket | `create-pr` standalone |
| Reviewing someone else's PR | `review-pr` standalone |
| Reviewing your own PR before merge | `review-pr` standalone |

---

## What is NOT in scope

- GetOutline doc updates (separate skill, needs custom MCP)
- GitHub Issues workflow (covered by existing `working-on-github-issue` skill)
- Slack notifications
- Automated merge after review approval
