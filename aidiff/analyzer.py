"""Heuristic analysis engine for detecting AI-generated code patterns."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

from loguru import logger


@dataclass
class LineScore:
    """Score for a single line of code."""

    line_number: int
    text: str
    score: float  # 0.0 = human, 1.0 = definitely AI
    reasons: list[str] = field(default_factory=list)


@dataclass
class FileAnalysis:
    """Analysis result for a single file."""

    path: str
    total_lines: int
    ai_lines: int
    ai_score: float  # 0.0-1.0 aggregate
    line_scores: list[LineScore] = field(default_factory=list)


# --- Explicit tag patterns ---

EXPLICIT_AI_TAGS: list[re.Pattern[str]] = [
    re.compile(r"#\s*ai[- ]generated", re.IGNORECASE),
    re.compile(r"#\s*@ai\b", re.IGNORECASE),
    re.compile(r"#\s*generated\s+by\s+(claude|copilot|gpt|chatgpt|gemini|ai)", re.IGNORECASE),
    re.compile(r"//\s*ai[- ]generated", re.IGNORECASE),
    re.compile(r"//\s*@ai\b", re.IGNORECASE),
    re.compile(r"//\s*generated\s+by\s+(claude|copilot|gpt|chatgpt|gemini|ai)", re.IGNORECASE),
]

# --- Heuristic patterns ---

PLACEHOLDER_COMMENTS: list[re.Pattern[str]] = [
    re.compile(r"#\s*TODO:\s*(Add|Implement|Handle)\s+", re.IGNORECASE),
    re.compile(r"#\s*FIXME:\s*(Add|Implement|Handle)\s+", re.IGNORECASE),
    re.compile(r"#\s*NOTE:\s*This\s+(is|function|class|method)\s+", re.IGNORECASE),
]

OBVIOUS_COMMENTS: list[re.Pattern[str]] = [
    re.compile(r"#\s*This\s+(is\s+a|function|class|method|variable)\s+", re.IGNORECASE),
    re.compile(r"#\s*(Initialize|Create|Set up|Define)\s+the\s+", re.IGNORECASE),
    re.compile(r"#\s*(Return|Returns)\s+the\s+(result|value|output)", re.IGNORECASE),
    re.compile(r"#\s*(Check|Validate|Verify)\s+(if|that|whether)\s+", re.IGNORECASE),
    re.compile(r"#\s*Loop\s+(through|over)\s+", re.IGNORECASE),
    re.compile(r"#\s*Import\s+(necessary|required)\s+", re.IGNORECASE),
]

VERBOSE_VARIABLE_PATTERN = re.compile(
    r"\b[a-z]+(?:_[a-z]+){4,}\b"  # 5+ word snake_case variables
)

TYPE_HINT_PATTERN = re.compile(
    r"def\s+\w+\s*\(.*:.*\)\s*->"
)

DOCSTRING_START = re.compile(r'^\s*("""|\'\'\')')


def _is_comment_line(line: str) -> bool:
    """Check if a line is a comment."""
    stripped = line.strip()
    return stripped.startswith("#") or stripped.startswith("//")


def _is_blank(line: str) -> bool:
    """Check if a line is blank."""
    return len(line.strip()) == 0


def analyze_file(file_path: str | Path, content: str | None = None) -> FileAnalysis:
    """
    Analyze a single file for AI-generated code patterns.

    Args:
        file_path: Path to the file.
        content: Optional pre-loaded content. If None, reads from disk.

    Returns:
        FileAnalysis with per-line scores.
    """
    path = Path(file_path)
    if content is None:
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except (OSError, UnicodeDecodeError) as e:
            logger.warning(f"Cannot read {file_path}: {e}")
            return FileAnalysis(path=str(file_path), total_lines=0, ai_lines=0, ai_score=0.0)

    lines = content.splitlines()
    if not lines:
        return FileAnalysis(path=str(file_path), total_lines=0, ai_lines=0, ai_score=0.0)

    line_scores = _score_lines(lines)

    # Contextual boost: clusters of AI-scored lines reinforce each other
    _apply_cluster_boost(line_scores)

    ai_lines = sum(1 for ls in line_scores if ls.score >= 0.5)
    total_code_lines = sum(1 for l in lines if not _is_blank(l))
    ai_score = ai_lines / max(total_code_lines, 1)

    return FileAnalysis(
        path=str(file_path),
        total_lines=len(lines),
        ai_lines=ai_lines,
        ai_score=round(ai_score, 4),
        line_scores=line_scores,
    )


def analyze_files(paths: Sequence[str | Path]) -> list[FileAnalysis]:
    """
    Analyze multiple files.

    Args:
        paths: File paths to analyze.

    Returns:
        List of FileAnalysis results.
    """
    results: list[FileAnalysis] = []
    for p in paths:
        results.append(analyze_file(p))
    return results


def _score_lines(lines: list[str]) -> list[LineScore]:
    """Score each line for AI-generation probability."""
    scores: list[LineScore] = []
    in_docstring = False
    docstring_start_line = -1
    func_line_count = 0
    comment_block_size = 0

    for i, line in enumerate(lines):
        score = 0.0
        reasons: list[str] = []

        stripped = line.strip()

        # Track docstring blocks
        if DOCSTRING_START.match(stripped):
            if in_docstring:
                in_docstring = False
                docstring_length = i - docstring_start_line
                if docstring_length > func_line_count and func_line_count > 0:
                    score += 0.3
                    reasons.append("docstring longer than function body")
            else:
                in_docstring = True
                docstring_start_line = i
                # Check for single-line docstring
                if stripped.count('"""') >= 2 or stripped.count("'''") >= 2:
                    in_docstring = False

        if in_docstring:
            score += 0.1
            reasons.append("inside docstring")

        # Explicit AI tags (high confidence)
        for pat in EXPLICIT_AI_TAGS:
            if pat.search(line):
                score = 1.0
                reasons.append("explicit AI tag")
                break

        # Placeholder comments
        for pat in PLACEHOLDER_COMMENTS:
            if pat.search(line):
                score = max(score, 0.7)
                reasons.append("placeholder comment")
                break

        # Obvious/redundant comments
        for pat in OBVIOUS_COMMENTS:
            if pat.search(line):
                score = max(score, 0.6)
                reasons.append("obvious comment")
                break

        # Verbose variable names
        if VERBOSE_VARIABLE_PATTERN.search(line):
            score = max(score, 0.4)
            reasons.append("verbose variable name")

        # Type hints on function defs
        if TYPE_HINT_PATTERN.search(line):
            score = max(score, 0.2)
            reasons.append("type-hinted function")

        # Comment block detection
        if _is_comment_line(stripped):
            comment_block_size += 1
            if comment_block_size >= 4:
                score = max(score, 0.4)
                reasons.append("long comment block")
        else:
            comment_block_size = 0

        # Track function body length for docstring ratio
        if stripped.startswith("def ") or stripped.startswith("async def "):
            func_line_count = 0
        elif not _is_blank(stripped) and not in_docstring and not _is_comment_line(stripped):
            func_line_count += 1

        scores.append(LineScore(
            line_number=i + 1,
            text=line,
            score=round(min(score, 1.0), 3),
            reasons=reasons,
        ))

    return scores


def _apply_cluster_boost(scores: list[LineScore], window: int = 5, threshold: float = 0.3) -> None:
    """
    Boost scores when nearby lines also have elevated AI scores.
    Clusters of AI-like code are more likely to be AI-generated.

    Args:
        scores: Line scores to modify in place.
        window: Window size for cluster detection.
        threshold: Minimum average score in window to trigger boost.
    """
    if len(scores) < window:
        return

    for i in range(len(scores)):
        start = max(0, i - window // 2)
        end = min(len(scores), i + window // 2 + 1)
        neighborhood = scores[start:end]
        avg = sum(s.score for s in neighborhood) / len(neighborhood)

        if avg >= threshold and scores[i].score > 0:
            boost = min(0.15, avg * 0.2)
            scores[i].score = round(min(scores[i].score + boost, 1.0), 3)
            if "cluster boost" not in scores[i].reasons:
                scores[i].reasons.append("cluster boost")
