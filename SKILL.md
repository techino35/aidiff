# aidiff - AI Code Tracker

## What
Python CLI tool that tracks AI-generated code in git repositories using hybrid detection (explicit tags, commit analysis, heuristic patterns).

## Commands
- `aidiff scan` - Scan repo, calculate AI ratio
- `aidiff status` - Full statistics with rich tables
- `aidiff track <file>` - Per-line AI scores
- `aidiff report` - HTML report with Chart.js graphs
- `aidiff install` - Git pre-commit hook
- `aidiff check --ci` - CI output
- `aidiff init-action` - Generate GitHub Action

## Stack
Python 3.10+, typer, rich, loguru, Jinja2, GitPython

## Location
`products/aidiff/`

## Install
```bash
cd products/aidiff
pip install -e .
```
