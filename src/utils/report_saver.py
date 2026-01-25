"""Save reports to filesystem."""

from pathlib import Path
from datetime import datetime
from src.models.report import DailyReport


def save_report(report: DailyReport, output_dir: str = "reports") -> Path:
    """Save daily report to markdown file.

    Args:
        report: Daily report to save
        output_dir: Output directory for reports

    Returns:
        Path to saved report file
    """
    # Create output directory if it doesn't exist
    reports_dir = Path(output_dir)
    reports_dir.mkdir(exist_ok=True)

    # Generate filename based on date
    date_str = report.date.strftime("%Y-%m-%d")
    filename = f"ai-news-brief-{date_str}.md"
    filepath = reports_dir / filename

    # Write report
    filepath.write_text(report.markdown_content, encoding="utf-8")

    return filepath
