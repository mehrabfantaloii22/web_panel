import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from panel_web import create_user, authenticate_user, set_two_factor, verify_two_factor_code, ensure_defaults, read_panel_settings


def test_two_factor_flow(tmp_path, monkeypatch):
    monkeypatch.setattr('panel_web.AUTH_FILE', tmp_path / 'users.json')
    monkeypatch.setattr('panel_web.SESSION_FILE', tmp_path / 'sessions.json')
    monkeypatch.setattr('panel_web.ARCHIVE_FILE', tmp_path / 'music_archive.json')
    monkeypatch.setattr('panel_web.LOGS_FILE', tmp_path / 'logs.json')
    monkeypatch.setattr('panel_web.SETTINGS_FILE', tmp_path / 'settings.json')
    ensure_defaults()
    user = create_user('demo', 'secret', role='user', telegram_username='demo')
    assert user is not None
    set_two_factor('demo', '123456')
    assert verify_two_factor_code('demo', '123456') is True
    assert verify_two_factor_code('demo', '000000') is False
    assert authenticate_user('demo', 'secret') is None
    auth = authenticate_user('demo', 'secret', otp='123456')
    assert auth is not None
