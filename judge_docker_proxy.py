#!/usr/bin/env python3

import argparse
import http.client
import http.server
import os
import re
import socket
from pathlib import Path


ALLOWED_ROUTES = (
    ("GET", re.compile(r"^/(v[0-9.]+/)?_ping(?:\?.*)?$")),
    ("GET", re.compile(r"^/(v[0-9.]+/)?version(?:\?.*)?$")),
    ("GET", re.compile(r"^/(v[0-9.]+/)?info(?:\?.*)?$")),
    ("POST", re.compile(r"^/v[0-9.]+/containers/create(?:\?.*)?$")),
    ("GET", re.compile(r"^/v[0-9.]+/containers/[^/]+/json(?:\?.*)?$")),
    ("POST", re.compile(r"^/v[0-9.]+/containers/[^/]+/start(?:\?.*)?$")),
    ("POST", re.compile(r"^/v[0-9.]+/containers/[^/]+/wait(?:\?.*)?$")),
    ("GET", re.compile(r"^/v[0-9.]+/containers/[^/]+/logs(?:\?.*)?$")),
    ("DELETE", re.compile(r"^/v[0-9.]+/containers/[^/]+(?:\?.*)?$")),
)


def resolve_socket_path(explicit_socket):
    if explicit_socket:
        return explicit_socket

    docker_host = os.environ.get("DOCKER_HOST", "").strip()
    if docker_host.startswith("unix://"):
        return docker_host.replace("unix://", "", 1)

    colima_socket = Path.home() / ".colima" / "default" / "docker.sock"
    if colima_socket.exists():
        return str(colima_socket)

    return "/var/run/docker.sock"


class UnixHTTPConnection(http.client.HTTPConnection):
    def __init__(self, socket_path):
        super().__init__("localhost")
        self.socket_path = socket_path

    def connect(self):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.connect(self.socket_path)


class DockerProxyHandler(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.0"
    socket_path = ""

    def do_GET(self):
        self.forward()

    def do_POST(self):
        self.forward()

    def do_DELETE(self):
        self.forward()

    def forward(self):
        self.close_connection = True
        if not self.is_allowed():
            self.send_error(403, "Forbidden")
            return

        content_length = int(self.headers.get("Content-Length", "0") or "0")
        body = self.rfile.read(content_length) if content_length else None

        headers = {}
        for key, value in self.headers.items():
            lower_key = key.lower()
            if lower_key in {"host", "connection", "content-length"}:
                continue
            headers[key] = value
        if body is not None:
            headers["Content-Length"] = str(len(body))

        conn = UnixHTTPConnection(self.socket_path)
        try:
            try:
                conn.request(self.command, self.path, body=body, headers=headers)
                resp = conn.getresponse()
            except OSError as exc:
                self.send_error(502, f"Docker socket is not reachable: {exc}")
                return

            self.send_response(resp.status, resp.reason)
            for key, value in resp.getheaders():
                if key.lower() in {"connection", "keep-alive", "proxy-connection", "transfer-encoding"}:
                    continue
                self.send_header(key, value)
            self.send_header("Connection", "close")
            self.end_headers()

            while True:
                chunk = resp.read(65536)
                if not chunk:
                    break
                self.wfile.write(chunk)
            self.wfile.flush()
        finally:
            conn.close()

    def is_allowed(self):
        return any(
            method == self.command and pattern.match(self.path)
            for method, pattern in ALLOWED_ROUTES
        )

    def log_message(self, fmt, *args):
        super().log_message(fmt, *args)


def parse_args():
    parser = argparse.ArgumentParser(description="Restricted local Docker API proxy for judge workers.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=int(os.environ.get("JUDGE_DOCKER_PROXY_PORT", "23750")))
    parser.add_argument("--socket", default=os.environ.get("JUDGE_DOCKER_SOCKET", ""))
    return parser.parse_args()


def main():
    args = parse_args()
    socket_path = resolve_socket_path(args.socket)
    if not os.path.exists(socket_path):
        raise FileNotFoundError(f"Docker socket not found: {socket_path}")

    DockerProxyHandler.socket_path = socket_path
    server = http.server.ThreadingHTTPServer((args.host, args.port), DockerProxyHandler)
    print(f"Judge Docker proxy listening on http://{args.host}:{args.port} -> {socket_path}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
