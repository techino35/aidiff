"""AI-generated code tracking and scoring logic using git history."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import git
from loguru import logger

from aidiff.analyzer import FileAnalysis, analyze_file

# Commit message patterns indicating AI involvement
COMMIT_AI_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\[AI\]", re.IGNORECASE),
    re.compile(r"\[Claude\]", re.IGNORECASE),
    re.compile(r"\[Copilot\]", re.IGNORECASE),
    re.compile(r"\[GPT\]", re.IGNORECASE),
    re.compile(r"\[ChatGPT\]", re.IGNORECASE),
    re.compile(r"\[Gemini\]", re.IGNORECASE),
    re.compile(r"Co-authored-by:\s*(Claude|Copilot|GitHub Copilot|ChatGPT|GPT|Gemini)", re.IGNORECASE),
    re.compile(r"generated\s+(by|with|using)\s+(AI|Claude|Copilot|GPT|ChatGPT|Gemini)", re.IGNORECASE),
    re.compile(r"ai[- ]assisted", re.IGNORECASE),
    re.compile(r"cursor|aider|cody", re.IGNORECASE),
]

AI_AUTHORS: list[re.Pattern[str]] = [
    re.compile(r"claude", re.IGNORECASE),
    re.compile(r"copilot", re.IGNORECASE),
    re.compile(r"dependabot", re.IGNORECASE),
    re.compile(r"renovate", re.IGNORECASE),
]

SUPPORTED_EXTENSIONS: set[str] = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".go", ".rs", ".rb",
    ".java", ".kt", ".swift", ".c", ".cpp", ".h", ".hpp",
    ".cs", ".php", ".vue", ".svelte", ".sh", ".bash",
}


@dataclass
class CommitInfo:
    """Information about a single commit's AI involvement."""

    sha: str
    message: str
    author: str
    date: str
    is_ai_commit: bool
    ai_indicators: list[str] = field(default_factory=list)


@dataclass
class RepoStats:
    """Aggregate statistics for the repository."""

    total_files: int
    total_lines: int
    ai_lines: int
    ai_ratio: float
    ai_commits: int
    total_commits: int
    ai_commit_ratio: float
    file_stats: list[dict[str, Any]] = field(default_factory=list)
    recent_commits: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class TrackingData:
    """Persistent tracking data stored in .aidiff/data.json."""

    scans: list[dict[str, Any]] = field(default_factory=list)
    last_scan: str | None = None
    repo_path: str | None = None


def get_repo(path: str | Path | None = None) -> git.Repo:
    """
    Get the git repository at the given path.

    Args:
        path: Path to the repository. Defaults to current directory.

    Returns:
        git.Repo instance.

    Raises:
        git.InvalidGitRepositoryError: If path is not a git repo.
    """
    repo_path = Path(path) if path else Path.cwd()
    return git.Repo(repo_path, search_parent_directories=True)


def classify_commit(commit: git.Commit) -> CommitInfo:
    """
    Classify a single commit as AI-involved or not.

    Args:
        commit: GitPython Commit object.

    Returns:
        CommitInfo with classification.
    """
    message = commit.message.strip()
    author_name = str(commit.author.name) if commit.author else ""
    indicators: list[str] = []

    # Check commit message
    for pat in COMMIT_AI_PATTERNS:
        match = pat.search(message)
        if match:
            indicators.append(f"commit message: {match.group()}")

    # Check author
    for pat in AI_AUTHORS:
        if pat.search(author_name):
            indicators.append(f"AI author: {author_name}")

    # Check co-author in message body
    if "co-authored-by:" in message.lower():
        for line in message.split("\n"):
            if "co-authored-by:" in line.lower():
                for pat in AI_AUTHORS:
                    if pat.search(line):
                        indicators.append(f"co-author: {line.strip()}")

    commit_date = datetime.fromtimestamp(commit.committed_date, tz=timezone.utc)

    return CommitInfo(
        sha=commit.hexsha[:8],
        message=message.split("\n")[0][:80],
        author=author_name,
        date=commit_date.isoformat(),
        is_ai_commit=len(indicators) > 0,
        ai_indicators=indicators,
    )


def get_tracked_files(repo: git.Repo) -> list[Path]:
    """
    Get all tracked source files in the repository.

    Args:
        repo: GitPython Repo object.

    Returns:
        List of file paths (relative to repo root).
    """
    repo_root = Path(repo.working_dir)
    tracked: list[Path] = []

    try:
        items = repo.head.commit.tree.traverse()
    except ValueError:
        logger.warning("Empty repository or no commits yet")
        return tracked

    for item in items:
        if item.type == "blob":
            file_path = repo_root / item.path
            if file_path.suffix in SUPPORTED_EXTENSIONS and file_path.exists():
                tracked.append(file_path)

    return tracked


def scan_repo(path: str | Path | None = None, max_commits: int = 100) -> RepoStats:
    """
    Scan the repository for AI-generated code.

    Args:
        path: Path to the repository.
        max_commits: Maximum number of recent commits to analyze.

    Returns:
        RepoStats with full analysis.
    """
    repo = get_repo(path)
    repo_root = Path(repo.working_dir)
    logger.info(f"Scanning repository: {repo_root}")

    # Analyze commits
    commits: list[CommitInfo] = []
    try:
        for commit in repo.iter_commits(max_count=max_commits):
            commits.append(classify_commit(commit))
    except ValueError:
        logger.warning("No commits found")

    ai_commits = sum(1 for c in commits if c.is_ai_commit)

    # Analyze files
    tracked_files = get_tracked_files(repo)
    logger.info(f"Analyzing {len(tracked_files)} source files")

    file_analyses: list[FileAnalysis] = []
    for fp in tracked_files:
        analysis = analyze_file(fp)
        if analysis.total_lines > 0:
            file_analyses.append(analysis)

    total_lines = sum(fa.total_lines for fa in file_analyses)
    ai_lines = sum(fa.ai_lines for fa in file_analyses)

    file_stats = [
        {
            "path": str(Path(fa.path).relative_to(repo_root)),
            "total_lines": fa.total_lines,
            "ai_lines": fa.ai_lines,
            "ai_score": fa.ai_score,
        }
        for fa in file_analyses
    ]
    file_stats.sort(key=lambda x: x["ai_score"], reverse=True)

    recent_commits = [
        {
            "sha": c.sha,
            "message": c.message,
            "author": c.author,
            "date": c.date,
            "is_ai": c.is_ai_commit,
            "indicators": c.ai_indicators,
        }
        for c in commits[:10]
    ]

    stats = RepoStats(
        total_files=len(file_analyses),
        total_lines=total_lines,
        ai_lines=ai_lines,
        ai_ratio=round(ai_lines / max(total_lines, 1), 4),
        ai_commits=ai_commits,
        total_commits=len(commits),
        ai_commit_ratio=round(ai_commits / max(len(commits), 1), 4),
        file_stats=file_stats,
        recent_commits=recent_commits,
    )

    # Save tracking data
    _save_scan(repo_root, stats)

    return stats


def track_file(file_path: str | Path) -> FileAnalysis:
    """
    Track AI-generated lines in a specific file.

    Args:
        file_path: Path to the file to analyze.

    Returns:
        FileAnalysis with per-line scores.
    """
    return analyze_file(file_path)


def _save_scan(repo_root: Path, stats: RepoStats) -> None:
    """
    Save scan results to .aidiff/data.json.

    Args:
        repo_root: Repository root path.
        stats: Scan results to save.
    """
    data_dir = repo_root / ".aidiff"
    data_dir.mkdir(exist_ok=True)
    data_file = data_dir / "data.json"

    tracking = TrackingData()
    if data_file.exists():
        try:
            raw = json.loads(data_file.read_text(encoding="utf-8"))
            tracking = TrackingData(**raw)
        except (json.JSONDecodeError, TypeError):
            logger.warning("Corrupted data.json, starting fresh")

    now = datetime.now(timezone.utc).isoformat()
    scan_entry = {
        "timestamp": now,
        "total_files": stats.total_files,
        "total_lines": stats.total_lines,
        "ai_lines": stats.ai_lines,
        "ai_ratio": stats.ai_ratio,
        "ai_commits": stats.ai_commits,
        "total_commits": stats.total_commits,
    }

    tracking.scans.append(scan_entry)
    tracking.last_scan = now
    tracking.repo_path = str(repo_root)

    # Keep last 100 scans
    if len(tracking.scans) > 100:
        tracking.scans = tracking.scans[-100:]

    data_file.write_text(
        json.dumps(asdict(tracking), indent=2, default=str),
        encoding="utf-8",
    )
    logger.debug(f"Saved scan data to {data_file}")
