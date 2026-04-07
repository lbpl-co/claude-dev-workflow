# pr-review — Local PR Reviewer

Review Bitbucket pull requests locally using [PR-Agent](https://github.com/qodo-ai/pr-agent) + [Ollama](https://ollama.ai) (Gemma 4).

No cloud LLM API keys needed — everything runs on your machine.

---

## Prerequisites

- **Python 3.10+**
- **Ollama** installed and running ([ollama.ai](https://ollama.ai))
- **Gemma 4** model pulled: `ollama pull gemma4`
- **Bitbucket Cloud** account with an App Password

---

## Quick Start

### 1. Setup

```bash
cd pr-review
make setup
```

This creates a virtualenv, installs dependencies, and copies the secrets template.

### 2. Configure secrets

Edit `config/.secrets.toml` with your Bitbucket App Password:

```toml
[ollama]
api_base = "http://localhost:11434"

[bitbucket]
username = "your-bitbucket-username"
app_password = "your-bitbucket-app-password"
```

**Create an App Password:**
Bitbucket → Avatar → Personal settings → App passwords → Create
- Scopes: **Repositories: Read**, **Pull requests: Read + Write**

### 3. Start Ollama with extended context

PR diffs need a large context window. Start Ollama with:

```bash
OLLAMA_CONTEXT_LENGTH=131072 ollama serve
```

### 4. Activate and run

```bash
source .venv/bin/activate

# Review a PR (default)
pr-review https://bitbucket.org/myworkspace/myrepo/pull-requests/42

# Suggest improvements
pr-review https://bitbucket.org/myworkspace/myrepo/pull-requests/42 improve

# Describe the PR
pr-review https://bitbucket.org/myworkspace/myrepo/pull-requests/42 describe

# Ask a question about the PR
pr-review https://bitbucket.org/myworkspace/myrepo/pull-requests/42 ask "any security issues?"
```

---

## Commands

| Command | What it does |
|---------|-------------|
| `review` | Full code review with inline comments posted to Bitbucket |
| `improve` | Suggests code improvements (with committable suggestions) |
| `describe` | Auto-generates PR title and description |
| `ask "..."` | Answers a specific question about the PR |

---

## Using a different model

```bash
# Use any Ollama model
pr-review <url> review --model ollama/codellama
pr-review <url> review --model ollama/llama3
```

Make sure the model is pulled first: `ollama pull <model-name>`

---

## Configuration

| File | Purpose |
|------|---------|
| `config/configuration.toml` | PR-Agent settings (model, timeouts, review instructions) |
| `config/.secrets.toml` | Your tokens (gitignored) |
| `config/.secrets.toml.example` | Template for secrets (committed) |

### Custom review instructions

Edit `config/configuration.toml` and uncomment:

```toml
[pr_reviewer]
extra_instructions = "Focus on security, error handling, and test coverage."
```

---

## Troubleshooting

**"Cannot reach Ollama"**
- Start Ollama: `OLLAMA_CONTEXT_LENGTH=131072 ollama serve`

**"Model not found"**
- Pull it: `ollama pull gemma4`

**"Bitbucket credentials not configured"**
- Edit `config/.secrets.toml` with your username and app password
- Or set `export BITBUCKET_USERNAME=x` and `export BITBUCKET_APP_PASSWORD=y`

**Review times out on large PRs**
- Increase timeout in `config/configuration.toml`: `ai_timeout = 600`

**Poor review quality**
- Enable `duplicate_examples = true` in config (already set by default)
- Try a larger model: `--model ollama/llama3`

---

## Known Limitations

| Issue | Detail |
|-------|--------|
| Context window | Must start Ollama with `OLLAMA_CONTEXT_LENGTH=131072` |
| Speed | Local models are slower than cloud APIs — large PRs may take minutes |
| Structured output | Local models may occasionally produce malformed JSON responses |
| Inline comments | Bitbucket API supports single-line comments only, not multi-line ranges |
