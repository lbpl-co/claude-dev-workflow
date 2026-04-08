# Developer Setup Guide

Get CDV (Claude Dev Workflow) commands working in ~15 minutes.

> **Quick start:** After installing the plugin (steps 1-2), run `/cdv:setup` in any Claude session for interactive guided setup. The rest of this document is for manual setup.

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

Two steps:

```bash
# Add the marketplace (one-time)
claude plugin marketplace add lbpl-co/claude-dev-workflow

# Install the plugin
claude plugin install cdv@lead-cdv --scope user
```

> **Project-only install:** Use `--scope project` instead of `--scope user` to limit to one project.

Verify:
```bash
claude plugin list
# Expected: "cdv" appears under User (or Project), status: enabled
```

Start a new Claude session and run `/cdv:setup` for interactive guided setup. Or continue below for manual setup.

Start a **new** Claude session after installing — plugins load at startup.

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

## 5. GitHub token (`/cdv:issue` only)

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

## 7. Verify

Open a terminal, start Claude, and run:

```
/cdv:setup
```

This checks all your integrations and tells you what's working.

Or test individual commands:

| Command | What to type | Expected |
|---------|-------------|----------|
| `/cdv:issue` | `/cdv:issue #1` | Reads GitHub issue, checks status, confirms with you |
| `/cdv:jira` | `/cdv:jira PROJ-123` | Reads JIRA ticket, posts analysis |
| `/cdv:pr` | `/cdv:pr` (on a feature branch) | Drafts and creates PR on Bitbucket |
| `/cdv:review` | `/cdv:review 42` | Fetches diff, prints structured review |

---

## Quick reference

| Command | Needs |
|---------|-------|
| `/cdv:setup` | Nothing — helps you set up everything else |
| `/cdv:issue` | `gh` CLI + `GITHUB_TOKEN` + `jq` |
| `/cdv:jira` | JIRA MCP (step 3) + Bitbucket MCP (step 4) |
| `/cdv:pr` | Bitbucket MCP (step 4) |
| `/cdv:review` | Bitbucket MCP (read + write) |

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
