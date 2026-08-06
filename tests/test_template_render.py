import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import DashboardApp


def test_dashboard_template_renders_from_any_cwd():
    app = DashboardApp()
    with tempfile.TemporaryDirectory() as tmp_dir:
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_dir)
            html = app._render({
                "title": "Login",
                "show_login": True,
                "show_dashboard": False,
                "user": None,
                "dashboard": {},
                "error": None,
                "help_items": [],
                "pending_login": None,
                "require_2fa": False,
            })
        finally:
            os.chdir(old_cwd)

    assert "Telegram Control Panel" in html
    assert "Welcome back" in html
