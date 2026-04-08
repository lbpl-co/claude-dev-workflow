---
name: setup
description: "Interactive onboarding for Claude Dev Workflow. Helps users pick which integrations they need (GitHub Issues, JIRA, Bitbucket) and walks through setup step by step. Use /cdv:setup to run."
---

# CDV Setup

**Announce at start:** "Running /cdv:setup — let's get you set up."

## Step 1 — Ask what they use

```
Welcome to Claude Dev Workflow (CDV) setup!

Which integrations does your team use? I'll only set up what you need.

1. GitHub Issues   → /cdv:issue (needs: gh CLI + GITHUB_TOKEN)
2. JIRA            → /cdv:jira  (needs: JIRA MCP server)
3. Bitbucket PRs   → /cdv:pr + /cdv:review (needs: Bitbucket MCP server)
4. All of the above

Pick one or more (e.g., "1 and 3" or "all"):
```

Wait for the user's selection. Map their choice to a list of integrations to set up.

---

## Step 2 — Check current state

For each selected integration, check what's already configured. Run checks silently and build a status report.

### GitHub Issues check

```bash
gh --version 2>/dev/null
```

```bash
gh auth status 2>&1
```

```bash
echo $GITHUB_TOKEN | head -c 4
```

```bash
which jq 2>/dev/null
```

Status:
- `gh` CLI: installed / **not installed**
- `gh` auth: logged in / **not logged in**
- `GITHUB_TOKEN`: set / **not set**
- `jq`: installed / **not installed**

### JIRA check

Try calling the JIRA MCP tool `jira_get_issue` with a dummy key to see if the tool exists and auth works. If the tool is not found, JIRA MCP is not configured.

Status:
- JIRA MCP: configured / **not configured**

### Bitbucket check

Try calling a Bitbucket MCP tool (e.g., list repos) to see if the tool exists and auth works. If the tool is not found, Bitbucket MCP is not configured.

Status:
- Bitbucket MCP (read): configured / **not configured**
- Bitbucket MCP (write): configured / **not configured**

### Show status

```
Current status:

  GitHub Issues:
    ✓ gh CLI installed
    ✗ gh not authenticated
    ✗ GITHUB_TOKEN not set
    ✓ jq installed

  JIRA:
    ✗ JIRA MCP not configured

  Bitbucket:
    ✓ Bitbucket MCP (read) configured
    ✗ Bitbucket MCP (write) not configured

I'll walk you through fixing the ✗ items. Ready?
```

Wait for confirmation.

---

## Step 3 — Walk through each missing item

Go through each failing check **one at a time**, in order. After each step, verify it worked before moving to the next.

### GitHub: Install gh CLI

```
Install the GitHub CLI:

  brew install gh          # macOS
  sudo apt install gh      # Ubuntu/Debian

Let me know when it's installed.
```

Wait. Then verify: `gh --version`

### GitHub: Authenticate gh

```
Authenticate with GitHub:

  gh auth login

Follow the browser prompt. Let me know when done.
```

Wait. Then verify: `gh auth status`

### GitHub: Set GITHUB_TOKEN

```
Create a GitHub Personal Access Token:

1. Go to GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Click "Generate new token (classic)"
3. Note: "claude-code", Scope: "repo"
4. Copy the token

Then add to your shell profile:

  echo 'export GITHUB_TOKEN="your-token-here"' >> ~/.zshrc
  source ~/.zshrc

Paste your token and I'll help you set it up, or let me know when done.
```

Wait. Then verify: check `$GITHUB_TOKEN` is set.

### GitHub: Install jq

```
Install jq (needed for GitHub Projects field parsing):

  brew install jq          # macOS
  sudo apt install jq      # Ubuntu/Debian

Let me know when installed.
```

Wait. Then verify: `which jq`

### JIRA: Configure MCP

```
Set up the JIRA MCP server:

1. Get a JIRA API token:
   https://id.atlassian.com/manage-profile/security/api-tokens
   Click "Create API token", label it "claude-code", copy it.

2. Find your Atlassian subdomain:
   If JIRA is at https://acme.atlassian.net, your subdomain is "acme".

3. Add to ~/.claude/settings.json under "mcpServers":

   "mcp-atlassian": {
     "command": "npx",
     "args": ["-y", "@sooperset/mcp-atlassian"],
     "env": {
       "JIRA_URL": "https://your-org.atlassian.net",
       "JIRA_USERNAME": "you@yourcompany.com",
       "JIRA_API_TOKEN": "your-api-token"
     }
   }

4. Restart Claude (settings load at startup).

Let me know when done — I'll verify the connection.
```

Wait for user. Then verify by calling `jira_get_issue` or similar. If it fails, help debug.

### Bitbucket: Configure MCP (write)

```
Set up the Bitbucket MCP server for creating PRs and posting comments:

1. Create a Bitbucket App Password:
   Bitbucket → Avatar → Personal settings → App passwords → Create
   Label: "claude-code"
   Scopes: Repositories (Read), Pull requests (Read + Write)

2. Find your workspace slug:
   It's in your Bitbucket URLs: bitbucket.org/<workspace>/...

3. Add to ~/.claude/settings.json under "mcpServers":

   "mcp-server-atlassian-bitbucket": {
     "command": "npx",
     "args": ["-y", "@aashari/mcp-server-atlassian-bitbucket"],
     "env": {
       "ATLASSIAN_SITE_NAME": "your-workspace",
       "ATLASSIAN_USER_EMAIL": "you@yourcompany.com",
       "ATLASSIAN_API_TOKEN": "your-app-password"
     }
   }

4. Restart Claude (settings load at startup).

Let me know when done — I'll verify the connection.
```

Wait for user. Then verify by calling a Bitbucket MCP tool. If it fails, help debug.

---

## Step 4 — Final summary

After all items are configured, show the final status:

```
Setup complete!

  ✓ GitHub Issues  — gh authenticated, GITHUB_TOKEN set, jq installed
  ✓ JIRA           — MCP configured and connected
  ✓ Bitbucket      — MCP (read + write) configured

Available commands:
  /cdv:issue #123                    — work on a GitHub issue
  /cdv:jira PROJ-123                 — work on a JIRA ticket
  /cdv:pr                            — create a Bitbucket PR
  /cdv:review 42                     — review a Bitbucket PR
  /cdv:setup                         — run this setup again

Run /cdv:setup anytime to check status or add more integrations.
```

Only show the commands relevant to what was configured.

---

## Notes

- Walk through one item at a time. Don't dump all instructions at once.
- After each step, verify before moving on. If verification fails, help debug.
- If the user says "skip" for any item, skip it and note it in the final summary.
- If everything is already configured, say so and show the available commands.
- Never ask the user to edit files you could check programmatically — check first, only ask them to act on what's actually missing.
