"""aidiff CLI - Track AI-generated code in your codebase."""

from __future__ import annotations

import sys
from pathlib import Path

import typer
from loguru import logger
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from aidiff import __version__

# Configure loguru - suppress by default, enable with --verbose
logger.remove()

app = typer.Typer(
    name="aidiff",
    help="Track which lines in your codebase were written by AI.",
    no_args_is_help=True,
    add_completion=False,
)
console = Console()


def _setup_logging(verbose: bool) -> None:
    """Configure loguru based on verbosity."""
    if verbose:
        logger.add(sys.stderr, level="DEBUG")
    else:
        logger.add(sys.stderr, level="WARNING")


@app.callback()
def main(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
) -> None:
    """aidiff - git blame for AI-generated code."""
    _setup_logging(verbose)


@app.command()
def scan(
    path: str = typer.Argument(".", help="Repository path to scan"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Minimal output"),
) -> None:
    """Scan the repository and calculate AI-generation ratio."""
    from aidiff.tracker import scan_repo

    try:
        stats = scan_repo(path)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

    if quiet:
        console.print(f"AI ratio: {stats.ai_ratio * 100:.1f}%")
        return

    console.print()
    _print_stats(stats)


@app.command()
def status(
    path: str = typer.Argument(".", help="Repository path"),
) -> None:
    """Show current repository AI statistics."""
    from aidiff.tracker import scan_repo

    try:
        stats = scan_repo(path)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

    console.print()
    _print_stats(stats)


@app.command()
def track(
    file: str = typer.Argument(..., help="File to analyze"),
) -> None:
    """Show AI-generated lines in a specific file."""
    from aidiff.tracker import track_file

    file_path = Path(file)
    if not file_path.exists():
        console.print(f"[red]Error:[/red] File not found: {file}")
        raise typer.Exit(1)

    analysis = track_file(file_path)

    console.print()
    console.print(Panel(
        f"[bold]{analysis.path}[/bold]\n"
        f"Total lines: {analysis.total_lines}  |  "
        f"AI lines: {analysis.ai_lines}  |  "
        f"AI score: [{'red' if analysis.ai_score > 0.7 else 'yellow' if analysis.ai_score > 0.4 else 'green'}]"
        f"{analysis.ai_score * 100:.1f}%[/]",
        title="aidiff track",
    ))

    if not analysis.line_scores:
        return

    table = Table(show_header=True, header_style="bold")
    table.add_column("Line", justify="right", style="dim", width=6)
    table.add_column("Score", justify="right", width=8)
    table.add_column("Reasons", width=30)
    table.add_column("Code", overflow="fold")

    for ls in analysis.line_scores:
        if ls.score < 0.3:
            continue
        score_color = "red" if ls.score >= 0.7 else "yellow" if ls.score >= 0.5 else "dim"
        table.add_row(
            str(ls.line_number),
            f"[{score_color}]{ls.score:.2f}[/]",
            ", ".join(ls.reasons) if ls.reasons else "",
            ls.text.rstrip()[:80],
        )

    console.print(table)


@app.command()
def report(
    path: str = typer.Argument(".", help="Repository path"),
    output: str = typer.Option(None, "--output", "-o", help="Output path for HTML report"),
    no_open: bool = typer.Option(False, "--no-open", help="Don't open in browser"),
) -> None:
    """Generate an HTML report and open it in the browser."""
    from aidiff.reporter import generate_report, open_report
    from aidiff.tracker import scan_repo

    try:
        stats = scan_repo(path)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

    report_path = generate_report(stats, output)
    console.print(f"[green]Report generated:[/green] {report_path}")

    if not no_open:
        open_report(report_path)


@app.command()
def install(
    path: str = typer.Argument(".", help="Repository path"),
) -> None:
    """Install the aidiff pre-commit git hook."""
    from aidiff.hooks import install_hook

    try:
        hook_path = install_hook(path)
        console.print(f"[green]Hook installed:[/green] {hook_path}")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def uninstall(
    path: str = typer.Argument(".", help="Repository path"),
) -> None:
    """Remove the aidiff pre-commit git hook."""
    from aidiff.hooks import uninstall_hook

    try:
        removed = uninstall_hook(path)
        if removed:
            console.print("[green]Hook removed[/green]")
        else:
            console.print("[yellow]No aidiff hook found[/yellow]")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command(name="init-action")
def init_action(
    path: str = typer.Argument(".", help="Repository root path"),
) -> None:
    """Generate a GitHub Action workflow for AI code gating."""
    from aidiff.hooks import generate_github_action

    try:
        action_path = generate_github_action(path)
        console.print(f"[green]GitHub Action generated:[/green] {action_path}")
        console.print("Commit and push to enable AI code gating on PRs.")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def check(
    path: str = typer.Argument(".", help="Repository path"),
    ci: bool = typer.Option(False, "--ci", help="CI-friendly output"),
    threshold: float = typer.Option(70.0, "--threshold", "-t", help="AI ratio warning threshold (%)"),
) -> None:
    """Check AI ratio (for CI/CD integration)."""
    from aidiff.tracker import scan_repo

    try:
        stats = scan_repo(path)
    except Exception as e:
        if ci:
            print(f"Error: {e}")
        else:
            console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

    ratio_pct = stats.ai_ratio * 100

    if ci:
        print(f"AI ratio: {ratio_pct:.1f}%")
        print(f"Files: {stats.total_files}")
        print(f"Lines: {stats.total_lines}")
        print(f"AI lines: {stats.ai_lines}")
        print(f"AI commits: {stats.ai_commits}/{stats.total_commits}")
        if ratio_pct > threshold:
            print(f"WARNING: AI ratio {ratio_pct:.1f}% exceeds threshold {threshold}%")
        return

    _print_stats(stats)
    if ratio_pct > threshold:
        console.print(f"\n[yellow]Warning:[/yellow] AI ratio {ratio_pct:.1f}% exceeds threshold {threshold}%")


@app.command()
def version() -> None:
    """Show version."""
    console.print(f"aidiff {__version__}")


def _print_stats(stats) -> None:
    """Print formatted statistics."""
    ratio_color = "red" if stats.ai_ratio > 0.7 else "yellow" if stats.ai_ratio > 0.4 else "green"

    console.print(Panel(
        f"[bold]AI Code Ratio: [{ratio_color}]{stats.ai_ratio * 100:.1f}%[/][/bold]\n\n"
        f"  Files analyzed:  {stats.total_files}\n"
        f"  Total lines:     {stats.total_lines:,}\n"
        f"  AI lines:        {stats.ai_lines:,}\n"
        f"  AI commits:      {stats.ai_commits} / {stats.total_commits}\n"
        f"  AI commit ratio: {stats.ai_commit_ratio * 100:.1f}%",
        title="[bold]aidiff[/bold] status",
        border_style="blue",
    ))

    if stats.file_stats:
        table = Table(title="Top Files by AI Score", show_header=True, header_style="bold")
        table.add_column("File", style="cyan", overflow="fold")
        table.add_column("Lines", justify="right")
        table.add_column("AI Lines", justify="right")
        table.add_column("AI %", justify="right")

        for f in stats.file_stats[:15]:
            score_pct = f["ai_score"] * 100
            color = "red" if score_pct > 70 else "yellow" if score_pct > 40 else "green"
            table.add_row(
                f["path"],
                str(f["total_lines"]),
                str(f["ai_lines"]),
                f"[{color}]{score_pct:.1f}%[/]",
            )

        console.print(table)

    if stats.recent_commits:
        console.print()
        commit_table = Table(title="Recent Commits", show_header=True, header_style="bold")
        commit_table.add_column("SHA", style="dim", width=8)
        commit_table.add_column("AI?", width=4)
        commit_table.add_column("Message", overflow="fold")
        commit_table.add_column("Author", style="dim")

        for c in stats.recent_commits[:10]:
            ai_badge = "[bold magenta]AI[/]" if c["is_ai"] else ""
            commit_table.add_row(c["sha"], ai_badge, c["message"], c["author"])

        console.print(commit_table)
