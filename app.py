"""Web application for the MCP Server List dashboard."""

import asyncio
import json
import mimetypes
import threading
import time
from collections import deque
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

from src.router import MCPRouter


PROJECT_ROOT = Path(__file__).resolve().parent
FRONTEND_ROOT = PROJECT_ROOT / "frontend"
CONFIG_PATH = PROJECT_ROOT / "config" / "mcp_servers.json"
SENSITIVE_HEADERS = {"authorization", "cookie", "proxy-authorization", "set-cookie"}


class ActivityLog:
    """Keep a bounded, thread-safe record of HTTP and MCP activity."""

    def __init__(self, limit=200):
        self._events = deque(maxlen=limit)
        self._lock = threading.Lock()

    def add(self, event):
        with self._lock:
            self._events.appendleft(event)

    def snapshot(self):
        with self._lock:
            events = list(self._events)
        return {"events": events, "total": len(events)}


activity_log = ActivityLog()


def serialize_value(value):
    """Convert MCP response objects into JSON-compatible values."""
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if hasattr(value, "__dict__"):
        return value.__dict__
    return value


class DashboardHandler(BaseHTTPRequestHandler):
    """Serve the dashboard and its small JSON API."""

    router = MCPRouter(CONFIG_PATH)

    def handle_one_request(self):
        started_at = time.perf_counter()
        self._response_status = HTTPStatus.OK
        try:
            super().handle_one_request()
        finally:
            activity_log.add(self.request_event(started_at))

    def send_response(self, code, message=None):
        self._response_status = code
        super().send_response(code, message)

    def request_event(self, started_at):
        path = getattr(self, "path", "")
        parsed = urlparse(path)
        server_key, operation = self.mcp_context(parsed.path)
        headers = {
            key.lower(): "[redacted]" if key.lower() in SENSITIVE_HEADERS else value
            for key, value in getattr(self, "headers", {}).items()
        }
        return {
            "id": f"{time.time_ns():x}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "kind": "mcp" if operation else "http",
            "method": getattr(self, "command", "UNKNOWN"),
            "path": path or parsed.path,
            "status": int(getattr(self, "_response_status", HTTPStatus.INTERNAL_SERVER_ERROR)),
            "duration_ms": round((time.perf_counter() - started_at) * 1000, 2),
            "client": self.client_address[0] if self.client_address else "unknown",
            "protocol": {
                "version": getattr(self, "request_version", "unknown"),
                "headers": headers,
                "content_length": int(headers.get("content-length", "0") or 0),
                "content_type": headers.get("content-type"),
            },
            "mcp": {
                "server_key": server_key,
                "operation": operation,
                "request_payload": getattr(self, "_request_payload", None),
            } if operation else None,
        }

    @staticmethod
    def mcp_context(path):
        if not path.startswith("/api/servers/"):
            return None, None
        remainder = path.removeprefix("/api/servers/")
        if remainder.endswith("/tools"):
            return unquote(remainder.removesuffix("/tools")), "list_tools"
        if remainder.endswith("/execute"):
            return unquote(remainder.removesuffix("/execute")), "execute_tool"
        return None, None

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/servers":
            return self.send_json(self.server_catalog())
        if parsed.path == "/api/monitor":
            return self.send_json(activity_log.snapshot())
        if parsed.path.startswith("/api/servers/") and parsed.path.endswith("/tools"):
            server_key = unquote(parsed.path.removeprefix("/api/servers/").removesuffix("/tools"))
            return self.send_tools(server_key)
        return self.send_frontend(parsed.path)

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path.startswith("/api/servers/") and parsed.path.endswith("/execute"):
            server_key = unquote(parsed.path.removeprefix("/api/servers/").removesuffix("/execute"))
            return self.execute_tool(server_key)
        self.send_error(HTTPStatus.NOT_FOUND, "Endpoint not found")

    def server_catalog(self):
        servers = []
        for key in self.router.list_servers():
            info = self.router.get_server_info(key)
            servers.append(
                {
                    "key": key,
                    "command": info["command"],
                    "description": info.get("description", ""),
                    "status": "configured",
                    "has_credentials": bool(info.get("env")),
                }
            )
        return {"servers": servers, "total": len(servers)}

    def send_tools(self, server_key):
        try:
            tools = asyncio.run(self.router.list_tools(server_key))
            payload = {
                "server_key": server_key,
                "tools": [serialize_value(tool) for tool in tools],
            }
            return self.send_json(payload)
        except Exception as error:
            return self.send_json({"error": str(error)}, HTTPStatus.BAD_GATEWAY)

    def execute_tool(self, server_key):
        try:
            length = int(self.headers.get("Content-Length", "0"))
            body = json.loads(self.rfile.read(length) or b"{}")
            self._request_payload = body
            result = asyncio.run(
                self.router.execute_tool(
                    server_key,
                    body["tool_name"],
                    body.get("arguments", {}),
                )
            )
            return self.send_json({"result": serialize_value(result)})
        except (KeyError, json.JSONDecodeError) as error:
            return self.send_json({"error": str(error)}, HTTPStatus.BAD_REQUEST)
        except Exception as error:
            return self.send_json({"error": str(error)}, HTTPStatus.BAD_GATEWAY)

    def send_frontend(self, path):
        relative_path = "index.html" if path == "/" else path.removeprefix("/")
        file_path = (FRONTEND_ROOT / relative_path).resolve()
        if FRONTEND_ROOT not in file_path.parents or not file_path.is_file():
            return self.send_error(HTTPStatus.NOT_FOUND, "File not found")
        content_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
        content = file_path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def send_json(self, payload, status=HTTPStatus.OK):
        content = json.dumps(payload, ensure_ascii=False, default=serialize_value).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def log_message(self, format, *args):
        print(f"[dashboard] {self.address_string()} - {format % args}")


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", 8000), DashboardHandler)
    print("MCP Server List dashboard: http://127.0.0.1:8000")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nDashboard stopped.")
    finally:
        server.server_close()
