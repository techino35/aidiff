"""HTML report generation using Jinja2 and Chart.js."""

from __future__ import annotations

import webbrowser
from datetime import datetime, timezone
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from loguru import logger

from aidiff.tracker import RepoStats


TEMPLATE_DIR = Path(__file__).parent / "templates"


def generate_report(stats: RepoStats, output_path: str | Path | None = None) -> Path:
    """
    Generate an HTML report from scan results.

    Args:
        stats: Repository scan statistics.
        output_path: Where to write the report. Defaults to .aidiff/report.html.

    Returns:
        Path to the generated HTML file.
    """
    if output_path is None:
        output_path = Path.cwd() / ".aidiff" / "report.html"

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=True,
    )
    template = env.get_template("report.html")

    # Prepare chart data
    top_files = stats.file_stats[:20]
    file_labels = [f["path"].split("/")[-1] for f in top_files]
    file_scores = [round(f["ai_score"] * 100, 1) for f in top_files]

    # Contributor stats from recent commits
    contributors: dict[str, dict[str, int]] = {}
    for c in stats.recent_commits:
        author = c["author"]
        if author not in contributors:
            contributors[author] = {"total": 0, "ai": 0}
        contributors[author]["total"] += 1
        if c["is_ai"]:
            contributors[author]["ai"] += 1

    contributor_labels = list(contributors.keys())
    contributor_ai_rates = [
        round(v["ai"] / max(v["total"], 1) * 100, 1)
        for v in contributors.values()
    ]

    # Commit timeline
    commit_labels = [c["sha"] for c in reversed(stats.recent_commits)]
    commit_ai = [1 if c["is_ai"] else 0 for c in reversed(stats.recent_commits)]

    html = template.render(
        generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        total_files=stats.total_files,
        total_lines=stats.total_lines,
        ai_lines=stats.ai_lines,
        ai_ratio=round(stats.ai_ratio * 100, 1),
        ai_commits=stats.ai_commits,
        total_commits=stats.total_commits,
        ai_commit_ratio=round(stats.ai_commit_ratio * 100, 1),
        file_stats=stats.file_stats[:30],
        recent_commits=stats.recent_commits,
        file_labels=file_labels,
        file_scores=file_scores,
        contributor_labels=contributor_labels,
        contributor_ai_rates=contributor_ai_rates,
        commit_labels=commit_labels,
        commit_ai=commit_ai,
    )

    output_path.write_text(html, encoding="utf-8")
    logger.info(f"Report generated: {output_path}")
    return output_path


def open_report(report_path: Path) -> None:
    """
    Open the generated report in the default browser.

    Args:
        report_path: Path to the HTML report.
    """
    webbrowser.open(f"file://{report_path.resolve()}")
