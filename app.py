import json
import os
import socket
from http.cookies import SimpleCookie
from urllib.parse import parse_qs, urlparse
from wsgiref.simple_server import make_server
from wsgiref.util import setup_testing_defaults

from jinja2 import Environment, FileSystemLoader

from panel_web import (
    authenticate_user,
    create_session,
    create_user,
    destroy_session,
    ensure_defaults,
    get_logs,
    get_session_user,
    list_music_archive,
    list_users,
    read_panel_settings,
    record_music_archive,
    update_password,
    write_panel_settings,
    append_log,
    set_two_factor,
    validate_password,
)


class DashboardApp:
    def __init__(self):
        self.host = os.getenv("HOST", "0.0.0.0")
        self.port = int(os.getenv("PORT", "8000"))
        self.jinja_env = Environment(loader=FileSystemLoader("templates"), autoescape=True)

    def _find_available_port(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind((self.host, 0))
            return sock.getsockname()[1]

    def _render(self, context):
        template = self.jinja_env.get_template("dashboard.html")
        return template.render(**context)

    def _set_cookie(self, headers, name, value):
        cookie = SimpleCookie()
        cookie[name] = value
        cookie[name]["path"] = "/"
        cookie[name]["httponly"] = True
        cookie[name]["samesite"] = "Lax"
        headers.append(("Set-Cookie", cookie.output(header="").strip()))

    def _delete_cookie(self, headers, name):
        cookie = SimpleCookie()
        cookie[name] = ""
        cookie[name]["path"] = "/"
        cookie[name]["expires"] = "Thu, 01 Jan 1970 00:00:00 GMT"
        headers.append(("Set-Cookie", cookie.output(header="").strip()))

    def _parse_cookies(self, environ):
        cookie_header = environ.get("HTTP_COOKIE", "")
        if not cookie_header:
            return {}
        cookie = SimpleCookie()
        cookie.load(cookie_header)
        return {key: morsel.value for key, value in cookie.items()}

    def _get_user(self, environ):
        cookies = self._parse_cookies(environ)
        token = cookies.get("panel_session")
        if not token:
            return None
        return get_session_user(token)

    def _handle_login(self, environ, start_response):
        if environ["REQUEST_METHOD"] == "POST":
            length = int(environ.get("CONTENT_LENGTH", "0"))
            body = environ["wsgi.input"].read(length).decode("utf-8")
            data = parse_qs(body)
            login_value = data.get("login", [""])[0]
            password = data.get("password", [""])[0]
            otp = data.get("otp", [""])[0]
            user = validate_password(login_value, password)
            if user and user.get("telegram_2fa_enabled"):
                if otp:
                    user = authenticate_user(login_value, password, otp=otp)
                if user:
                    token = create_session(user.get("username"), user.get("role", "user"))
                    headers = []
                    self._set_cookie(headers, "panel_session", token)
                    append_log("security", "Successful login", {"username": login_value}, user=login_value)
                    return self._redirect(start_response, headers, "/")
                append_log("security", "Failed login attempt", {"username": login_value}, user=login_value)
                return self._render_page(start_response, "Login", {"show_login": True, "require_2fa": True, "pending_login": login_value, "error": "Invalid 2FA code"}, status=401)
            if user:
                token = create_session(user.get("username"), user.get("role", "user"))
                headers = []
                self._set_cookie(headers, "panel_session", token)
                append_log("security", "Successful login", {"username": login_value}, user=login_value)
                return self._redirect(start_response, headers, "/")
            append_log("security", "Failed login attempt", {"username": login_value}, user=login_value)
            return self._render_page(start_response, "Login", {"show_login": True, "error": "Invalid credentials"}, status=401)
        return self._render_page(start_response, "Login", {"show_login": True, "require_2fa": False, "pending_login": None, "error": None}, status=200)

    def _redirect(self, start_response, headers, location):
        status = "302 Found"
        headers.append(("Location", location))
        return self._response(start_response, status, headers, b"")

    def _render_page(self, start_response, title, context, status=200):
        payload = {
            "title": title,
            "show_login": False,
            "show_dashboard": False,
            "user": None,
            "dashboard": {},
            "error": None,
            "help_items": [],
            **context,
        }
        body = self._render(payload)
        return self._response(start_response, f"{status} OK", [("Content-Type", "text/html; charset=utf-8")], body.encode("utf-8"))

    def _response(self, start_response, status, headers, body):
        start_response(status, headers)
        return [body]

    def _build_dashboard_context(self, user):
        settings = read_panel_settings()
        modules = settings.get("modules", {})
        dashboard = {
            "user": user,
            "modules": modules,
            "module_count": len(modules),
            "active_modules": sum(1 for value in modules.values() if value),
            "archive": list_music_archive(),
            "users": list_users(),
            "logs": get_logs(limit=12),
            "settings": settings,
        }
        return {
            "show_login": False,
            "show_dashboard": True,
            "user": user,
            "dashboard": dashboard,
            "help_items": [
                {"title": "Dashboard", "body": "Inspect system health, module state, and recent activity from one place."},
                {"title": "Music Archive", "body": "Review archive entries, add new tracks, and keep your music collection organized."},
                {"title": "Settings", "body": "Enable or disable panel modules without touching the Telegram automation logic."},
                {"title": "Users", "body": "Create and manage user accounts for secure access to the dashboard."},
            ],
        }

    def __call__(self, environ, start_response):
        setup_testing_defaults(environ)
        path = urlparse(environ.get("PATH_INFO", "/")).path
        method = environ.get("REQUEST_METHOD", "GET")
        user = self._get_user(environ)

        if path == "/login" and method == "GET":
            return self._render_page(start_response, "Login", {"show_login": True, "error": None, "user": None}, 200)
        if path == "/login" and method == "POST":
            return self._handle_login(environ, start_response)
        if path == "/logout":
            headers = []
            token = self._parse_cookies(environ).get("panel_session")
            if token:
                destroy_session(token)
            self._delete_cookie(headers, "panel_session")
            return self._redirect(start_response, headers, "/login")

        if not user:
            headers = []
            self._delete_cookie(headers, "panel_session")
            return self._redirect(start_response, headers, "/login")

        if path == "/api/modules":
            return self._json_response(start_response, read_panel_settings().get("modules", {}))
        if path == "/api/archive":
            return self._json_response(start_response, list_music_archive())
        if path == "/api/logs":
            return self._json_response(start_response, get_logs(limit=80))
        if path == "/api/settings" and method == "POST":
            length = int(environ.get("CONTENT_LENGTH", "0"))
            body = environ["wsgi.input"].read(length).decode("utf-8")
            data = parse_qs(body)
            settings = read_panel_settings()
            for key, values in data.items():
                if key.startswith("module_"):
                    module_name = key[len("module_"):]
                    settings.setdefault("modules", {})[module_name] = values[0] == "on"
            write_panel_settings(settings)
            append_log("feature", "Updated module settings", {"modules": settings.get("modules", {})}, user=user.get("username"))
            return self._redirect(start_response, [], "/")
        if path == "/api/archive" and method == "POST":
            length = int(environ.get("CONTENT_LENGTH", "0"))
            body = environ["wsgi.input"].read(length).decode("utf-8")
            data = parse_qs(body)
            title = data.get("title", [""])[0]
            url = data.get("url", [""])[0]
            record_music_archive(title, url=url, source="web")
            append_log("music", "Added music archive entry", {"title": title}, user=user.get("username"))
            return self._redirect(start_response, [], "/")
        if path == "/api/users" and method == "POST":
            if user.get("role") != "admin":
                return self._json_response(start_response, {"error": "Forbidden"}, 403)
            length = int(environ.get("CONTENT_LENGTH", "0"))
            body = environ["wsgi.input"].read(length).decode("utf-8")
            data = parse_qs(body)
            username = data.get("username", [""])[0]
            password = data.get("password", [""])[0]
            role = data.get("role", ["user"])[0]
            telegram_username = data.get("telegram_username", [""])[0]
            telegram_2fa_enabled = data.get("telegram_2fa_enabled", ["off"])[0] == "on"
            two_factor_code = data.get("two_factor_code", [""])[0]
            created = create_user(username, password, role=role, telegram_username=telegram_username)
            if created:
                set_two_factor(username, enabled=telegram_2fa_enabled, code=two_factor_code or None)
            return self._json_response(start_response, {"ok": created is not None, "user": created})
        if path == "/api/password" and method == "POST":
            length = int(environ.get("CONTENT_LENGTH", "0"))
            body = environ["wsgi.input"].read(length).decode("utf-8")
            data = parse_qs(body)
            password = data.get("password", [""])[0]
            update_password(user.get("username"), password)
            return self._json_response(start_response, {"ok": True})
        if path == "/api/help":
            return self._json_response(start_response, {"help": [
                {"title": "Dashboard", "body": "Use the overview to inspect module health, archive activity, and recent logs."},
                {"title": "Music Archive", "body": "Add or review archived tracks, and use the built-in archive table to manage your collection."},
                {"title": "Settings", "body": "Toggle modules and review the current panel configuration from the settings section."},
            ]})
        if path == "/":
            context = self._build_dashboard_context(user)
            return self._render_page(start_response, "Dashboard", context, 200)
        return self._render_page(start_response, "Not Found", {"user": user, "error": "Page not found"}, 404)

    def _json_response(self, start_response, payload, status=200):
        body = json.dumps(payload).encode("utf-8")
        headers = [("Content-Type", "application/json; charset=utf-8")]
        return self._response(start_response, f"{status} OK", headers, body)

    def run(self):
        ensure_defaults()
        try:
            with make_server(self.host, self.port, self) as httpd:
                print(f"Web dashboard running on http://{self.host}:{self.port}")
                httpd.serve_forever()
        except OSError:
            self.port = self._find_available_port()
            with make_server(self.host, self.port, self) as httpd:
                print(f"Web dashboard running on http://{self.host}:{self.port}")
                httpd.serve_forever()


def main():
    app = DashboardApp()
    app.run()


if __name__ == "__main__":
    main()
