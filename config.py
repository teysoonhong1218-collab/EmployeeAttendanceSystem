import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# ── Database URL ──────────────────────────────────────────────
SQLITE_URL = "sqlite:///" + os.path.join(BASE_DIR, "attendance.db")
DB_URL = os.environ.get("DATABASE_URL", SQLITE_URL)


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "sme-attendance-secret-key-2026")
    SQLALCHEMY_DATABASE_URI = DB_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {}
    COMPANY_NAME = "TechVenture Solutions Sdn Bhd"
    COMPANY_SHORT = "TechVenture"
    WORK_START_HOUR = 9
    WORK_END_HOUR = 18
    LATE_THRESHOLD_MINUTES = 15
