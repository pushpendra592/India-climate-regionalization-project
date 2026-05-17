"""
Central configuration for the entire project.
Change settings here — everything else adapts.
"""

from pathlib import Path
from dotenv import load_dotenv
import os

# ── Load environment variables ──
load_dotenv()

# ── Project Paths ──
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
INTERIM_DIR = DATA_DIR / "interim"
PROCESSED_DIR = DATA_DIR / "processed"
EXTERNAL_DIR = DATA_DIR / "external"
OUTPUT_DIR = PROJECT_ROOT / "outputs"
FIGURES_DIR = OUTPUT_DIR / "figures"
MODELS_DIR = OUTPUT_DIR / "models"
REPORTS_DIR = OUTPUT_DIR / "reports"
TABLES_DIR = OUTPUT_DIR / "tables"

# ── Create directories if they don't exist ──
for dir_path in [
    RAW_DIR / "nasa_power",
    INTERIM_DIR,
    PROCESSED_DIR,
    EXTERNAL_DIR,
    FIGURES_DIR,
    MODELS_DIR,
    REPORTS_DIR,
    TABLES_DIR,
]:
    dir_path.mkdir(parents=True, exist_ok=True)

# ── Time Range ──
START_DATE = "2000-01-01"
END_DATE = "2024-12-31"

# ── API Configuration ──
NASA_POWER_BASE_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"

# Rate limiting
NASA_POWER_REQUESTS_PER_SECOND = 2
API_MAX_RETRIES = 3
API_RETRY_DELAY = 5  # seconds

# ── ML Configuration ──
RANDOM_STATE = 42
K_RANGE = range(3, 16)  # For elbow method
TEST_SIZE = 0.2

# ── Logging ──
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = PROJECT_ROOT / "logs" / "project.log"
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
