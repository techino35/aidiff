"""Git hook management for aidiff."""

from __future__ import annotations

import stat
from pathlib import Path

import git
from loguru import logger

PRE_COMMIT_HOOK = """\
#!/bin/sh
# aidiff pre-commit hook
# Automatically tracks AI-generated code on each commit

echo "[aidiff] Scanning staged changes..."

# Run aidiff scan in background-friendly mode
if command -v aidiff > /dev/null 2>&1; then
    aidiff scan --quiet 2>/dev/null || true
    echo "[aidiff] Scan complete."
else
    echo "[aidiff] Warning: aidiff not installed. Run: pip install aidiff"
fi

# Always allow commit (non-blocking)
exit 0
"""

GITHUB_ACTION_TEMPLATE = """\
name: AI Code Gate
on:
  pull_request:
    types: [opened, synchronize]

permissions:
  pull-requests: write
  contents: read

jobs:
  ai-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install aidiff
        run: pip install aidiff

      - name: Run AI scan
        id: scan
        run: |
          OUTPUT=$(aidiff check --ci)
          echo "result<<EOF" >> $GITHUB_OUTPUT
          echo "$OUTPUT" >> $GITHUB_OUTPUT
          echo "EOF" >> $GITHUB_OUTPUT

      - name: Comment on PR
        if: always()
        uses: actions/github-script@v7
        with:
          script: |
            const output = `${{ steps.scan.outputs.result }}`;
            const lines = output.split('\\n');
            let aiRatio = 0;
            for (const line of lines) {
              const match = line.match(/AI ratio:\\s*([\\d.]+)%/);
              if (match) aiRatio = parseFloat(match[1]);
            }

            let body = `## aidiff AI Code Report\\n\\n`;
            body += `\`\`\`\\n${output}\\n\`\`\`\\n\\n`;

            if (aiRatio > 70) {
              body += `> **Warning**: AI-generated code ratio is ${aiRatio}% (threshold: 70%)\\n`;
              body += `> Consider adding more human review for this PR.`;
            } else {
              body += `AI code ratio: ${aiRatio}% (within threshold)`;
            }

            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: body
            });
"""


def install_hook(repo_path: str | Path | None = None) -> Path:
    """
    Install the aidiff pre-commit hook.

    Args:
        repo_path: Path to the git repository.

    Returns:
        Path to the installed hook file.
    """
    repo = git.Repo(repo_path or Path.cwd(), search_parent_directories=True)
    hooks_dir = Path(repo.git_dir) / "hooks"
    hooks_dir.mkdir(exist_ok=True)

    hook_path = hooks_dir / "pre-commit"

    if hook_path.exists():
        existing = hook_path.read_text(encoding="utf-8")
        if "aidiff" in existing:
            logger.info("aidiff hook already installed")
            return hook_path
        # Append to existing hook
        logger.info("Appending aidiff to existing pre-commit hook")
        with open(hook_path, "a", encoding="utf-8") as f:
            f.write("\n\n# --- aidiff hook ---\n")
            f.write(PRE_COMMIT_HOOK.split("#!/bin/sh\n", 1)[1])
    else:
        hook_path.write_text(PRE_COMMIT_HOOK, encoding="utf-8")

    # Make executable
    hook_path.chmod(hook_path.stat().st_mode | stat.S_IEXEC)
    logger.info(f"Installed pre-commit hook: {hook_path}")
    return hook_path


def uninstall_hook(repo_path: str | Path | None = None) -> bool:
    """
    Remove the aidiff pre-commit hook.

    Args:
        repo_path: Path to the git repository.

    Returns:
        True if hook was removed.
    """
    repo = git.Repo(repo_path or Path.cwd(), search_parent_directories=True)
    hook_path = Path(repo.git_dir) / "hooks" / "pre-commit"

    if not hook_path.exists():
        logger.info("No pre-commit hook found")
        return False

    content = hook_path.read_text(encoding="utf-8")
    if "aidiff" not in content:
        logger.info("aidiff hook not found in pre-commit")
        return False

    # If it's only our hook, remove the file
    if content.strip() == PRE_COMMIT_HOOK.strip():
        hook_path.unlink()
        logger.info("Removed aidiff pre-commit hook")
    else:
        # Remove our section
        lines = content.split("# --- aidiff hook ---")
        hook_path.write_text(lines[0].rstrip() + "\n", encoding="utf-8")
        logger.info("Removed aidiff section from pre-commit hook")

    return True


def generate_github_action(output_dir: str | Path | None = None) -> Path:
    """
    Generate the GitHub Action workflow file.

    Args:
        output_dir: Base directory (defaults to repo root).

    Returns:
        Path to the generated workflow file.
    """
    base = Path(output_dir) if output_dir else Path.cwd()
    workflow_dir = base / ".github" / "workflows"
    workflow_dir.mkdir(parents=True, exist_ok=True)

    action_path = workflow_dir / "aigate.yml"
    action_path.write_text(GITHUB_ACTION_TEMPLATE, encoding="utf-8")
    logger.info(f"Generated GitHub Action: {action_path}")
    return action_path
