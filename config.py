from pathlib import Path

api_id = 32295587
api_hash = "86517c938f1c4391a35379cf188b8567"

BASE_DIR = Path(__file__).resolve().parent
SESSION_DIR = BASE_DIR / "data"
SESSION_DIR.mkdir(parents=True, exist_ok=True)
SESSION_NAME = str(SESSION_DIR / "telegram_session")

SETTINGS_FILE = "settings.json"

OWNER_ONLY = True