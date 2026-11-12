# aidiff

> Track which lines in your codebase were written by AI.

[![PyPI version](https://img.shields.io/pypi/v/aidiff.svg)](https://pypi.org/project/aidiff/)
[![PyPI downloads](https://img.shields.io/pypi/dm/aidiff.svg)](https://pypi.org/project/aidiff/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

---

**aidiff** is `git blame` for AI-generated code. It tracks, scores, and visualizes how much of your codebase was written by AI assistants like Copilot, Claude, ChatGPT, and Cursor.

## Why?

AI-generated code is becoming a significant portion of modern codebases. Studies show that [AI-assisted developers accept ~30% of suggestions](https://github.blog/2022-09-07-research-quantifying-github-copilots-impact-on-developer-productivity-and-happiness/), and that number is growing fast.

But **nobody tracks it**. This creates invisible technical debt:

- Which files are mostly AI-generated?
- Are AI-written functions getting proper review?
- What's your team's actual AI code ratio over time?

**aidiff** answers these questions.

## Quick Start

```bash
pip install aidiff

cd your-repo
aidiff scan          # Scan and show AI ratio
aidiff status        # Full statistics
aidiff report        # Generate HTML report
```

That's it. Three commands to understand your AI code footprint.

## How It Works

aidiff uses a **hybrid detection approach**:

1. **Explicit tags** - `# ai-generated`, `Co-authored-by: Claude`, `[AI]` in commits
2. **Commit analysis** - Patterns in commit messages indicating AI involvement
3. **Heuristic analysis** - Detects AI coding patterns:
   - Overly verbose variable names (`user_authentication_token_validation`)
   - Redundant comments (`# Initialize the result dictionary`)
   - Placeholder TODOs (`# TODO: Add error handling`)
   - Docstrings longer than the function body
   - Universal type hints on every function

## Commands

| Command | Description |
|---------|-------------|
| `aidiff scan` | Scan repo and calculate AI ratio |
| `aidiff status` | Show full statistics with tables |
| `aidiff track <file>` | Show AI-scored lines in a file |
| `aidiff report` | Generate HTML report with charts |
| `aidiff install` | Install pre-commit git hook |
| `aidiff check --ci` | CI-friendly output for pipelines |
| `aidiff init-action` | Generate GitHub Action workflow |

## HTML Report

`aidiff report` generates a beautiful, self-contained HTML report with:

- AI code ratio trends over time (Chart.js)
- File-by-file AI score heatmap
- Contributor AI usage breakdown
- Recent commit AI classification

## GitHub Action

```bash
aidiff init-action  # Generates .github/workflows/aigate.yml
```

This creates a GitHub Action that automatically comments on PRs with the AI code ratio, warning when it exceeds 70%.

## Git Hook

```bash
aidiff install  # Installs pre-commit hook
```

Automatically runs `aidiff scan` before each commit, keeping `.aidiff/data.json` up to date.

## Configuration

aidiff stores data in `.aidiff/data.json` in your repo root. This file is meant to be committed and shared with your team.

## Insiders

> Early supporters get priority features and direct input on the roadmap.

[Become a Sponsor](https://github.com/sponsors/techino35) to unlock:

- Custom detection rules
- Team dashboard
- Slack/Discord notifications
- Priority support

## License

MIT
