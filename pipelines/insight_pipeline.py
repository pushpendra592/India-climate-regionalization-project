"""
Generate cluster profiles and domain-specific insight outputs.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import PROCESSED_DIR, TABLES_DIR, REPORTS_DIR
from src.insights.agriculture import AgricultureInsights
from src.insights.energy import EnergyInsights
from src.insights.disaster_risk import DisasterRiskInsights
from src.insights.urban_planning import UrbanPlanningInsights
from src.utils.io_helpers import load_dataframe, save_dataframe
from src.utils.logger import get_logger
from src.utils.timer import Timer

logger = get_logger("insight_pipeline")


def _write_markdown_report(sections: dict[str, str], path):
    lines = ["# Weather Pattern Clustering Insight Report", ""]
    for title, body in sections.items():
        lines.append(f"## {title}")
        lines.append("")
        lines.append(body)
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def _table_preview(df, empty_message: str) -> str:
    if len(df) == 0:
        return empty_message
    return df.head(5).to_csv(index=False)


def run_insights():
    """Generate domain-specific summaries from clustered climate normals."""
    with Timer("Insight Pipeline"):
        clustered = load_dataframe(
            PROCESSED_DIR / "climate_normals_clustered.parquet",
            "clustered climate normals",
        )

        agriculture = AgricultureInsights().generate(clustered)
        energy = EnergyInsights().generate(clustered)
        disaster = DisasterRiskInsights().generate(clustered)
        urban = UrbanPlanningInsights().generate(clustered)

        save_dataframe(agriculture, TABLES_DIR / "agriculture_insights.parquet", "agriculture insights")
        save_dataframe(energy, TABLES_DIR / "energy_insights.parquet", "energy insights")
        save_dataframe(disaster, TABLES_DIR / "disaster_insights.parquet", "disaster insights")
        save_dataframe(urban, TABLES_DIR / "urban_insights.parquet", "urban insights")

        sections = {
            "Agriculture": _table_preview(agriculture, "No agriculture features available."),
            "Energy": _table_preview(energy, "No energy features available."),
            "Disaster Risk": _table_preview(disaster, "No disaster-risk features available."),
            "Urban Planning": _table_preview(urban, "No urban-planning features available."),
        }
        _write_markdown_report(sections, REPORTS_DIR / "insight_report.md")

        logger.info("Insight generation complete")
        return {
            "agriculture": agriculture,
            "energy": energy,
            "disaster": disaster,
            "urban": urban,
        }


if __name__ == "__main__":
    run_insights()
