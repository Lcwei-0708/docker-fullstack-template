import http.client
import json
import socket
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import quote

DOCKER_SOCK = "/var/run/docker.sock"
LISTEN_HOST = "0.0.0.0"
LISTEN_PORT = 9100
API = "v1.41"


class UnixHTTPConnection(http.client.HTTPConnection):
    def __init__(self, sock_path: str, timeout: float = 5.0) -> None:
        super().__init__("localhost", timeout=timeout)
        self._sock_path = sock_path

    def connect(self) -> None:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(self.timeout)
        sock.connect(self._sock_path)
        self.sock = sock


def docker_get(path: str) -> object:
    conn = UnixHTTPConnection(DOCKER_SOCK)
    try:
        conn.request("GET", f"/{API}{path}")
        resp = conn.getresponse()
        body = resp.read()
        if resp.status >= 400:
            raise RuntimeError(f"docker {path} -> {resp.status}")
        return json.loads(body.decode("utf-8"))
    finally:
        conn.close()


def escape_label(value: str) -> str:
    return (
        value.replace("\\", "\\\\")
        .replace("\n", "\\n")
        .replace('"', '\\"')
    )


def working_set(memory_stats: dict) -> int:
    """Match `docker stats` MEM USAGE: cgroup usage minus page cache."""
    usage = int(memory_stats.get("usage") or 0)
    stats = memory_stats.get("stats") or {}
    # cgroup v1 uses total_inactive_file; v2 uses inactive_file.
    inactive = stats.get("total_inactive_file")
    if inactive is None:
        inactive = stats.get("inactive_file")
    inactive = int(inactive or 0)
    if usage >= inactive:
        return usage - inactive
    return usage


def blkio_bytes(blkio_stats: dict, op: str) -> int:
    total = 0
    for entry in blkio_stats.get("io_service_bytes_recursive") or []:
        if str(entry.get("op", "")).lower() == op:
            total += int(entry.get("value") or 0)
    return total


def network_bytes(networks: dict, field: str) -> int:
    return sum(int((iface or {}).get(field) or 0) for iface in (networks or {}).values())


def collect_metrics() -> str:
    containers = docker_get("/containers/json")
    lines: list[str] = [
        "# HELP container_cpu_usage_seconds_total Cumulative CPU time.",
        "# TYPE container_cpu_usage_seconds_total counter",
        "# HELP container_memory_working_set_bytes Current memory working set.",
        "# TYPE container_memory_working_set_bytes gauge",
        "# HELP container_memory_limit_bytes Cgroup memory limit (docker stats MEM LIMIT).",
        "# TYPE container_memory_limit_bytes gauge",
        "# HELP container_fs_reads_bytes_total Cumulative disk reads.",
        "# TYPE container_fs_reads_bytes_total counter",
        "# HELP container_fs_writes_bytes_total Cumulative disk writes.",
        "# TYPE container_fs_writes_bytes_total counter",
        "# HELP container_network_receive_bytes_total Cumulative network receive.",
        "# TYPE container_network_receive_bytes_total counter",
        "# HELP container_network_transmit_bytes_total Cumulative network transmit.",
        "# TYPE container_network_transmit_bytes_total counter",
    ]
    for container in containers:
        cid = container.get("Id") or ""
        name = (container.get("Names") or ["/unknown"])[0].lstrip("/")
        labels = container.get("Labels") or {}
        service = labels.get("com.docker.compose.service", "")
        project = labels.get("com.docker.compose.project", "")
        try:
            stats = docker_get(
                f"/containers/{quote(cid, safe='')}/stats?stream=false&one-shot=true"
            )
        except Exception:
            continue
        label = (
            f'name="{escape_label(name)}",'
            f'container_label_com_docker_compose_service="{escape_label(service)}",'
            f'container_label_com_docker_compose_project="{escape_label(project)}"'
        )
        cpu_ns = int(
            ((stats.get("cpu_stats") or {}).get("cpu_usage") or {}).get("total_usage")
            or 0
        )
        lines.append(
            f"container_cpu_usage_seconds_total{{{label}}} {cpu_ns / 1_000_000_000}"
        )
        memory_stats = stats.get("memory_stats") or {}
        lines.append(
            f"container_memory_working_set_bytes{{{label}}} {working_set(memory_stats)}"
        )
        lines.append(
            f"container_memory_limit_bytes{{{label}}} {int(memory_stats.get('limit') or 0)}"
        )
        blkio = stats.get("blkio_stats") or {}
        lines.append(
            f"container_fs_reads_bytes_total{{{label}}} {blkio_bytes(blkio, 'read')}"
        )
        lines.append(
            f"container_fs_writes_bytes_total{{{label}}} {blkio_bytes(blkio, 'write')}"
        )
        nets = stats.get("networks") or {}
        lines.append(
            f"container_network_receive_bytes_total{{{label}}} {network_bytes(nets, 'rx_bytes')}"
        )
        lines.append(
            f"container_network_transmit_bytes_total{{{label}}} {network_bytes(nets, 'tx_bytes')}"
        )
    lines.append("")
    return "\n".join(lines)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args) -> None:
        return

    def do_GET(self) -> None:
        if self.path.split("?", 1)[0] == "/healthz":
            body = b"ok\n"
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if self.path.split("?", 1)[0] != "/metrics":
            self.send_error(404)
            return
        try:
            body = collect_metrics().encode("utf-8")
            self.send_response(200)
            self.send_header(
                "Content-Type", "text/plain; version=0.0.4; charset=utf-8"
            )
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except Exception as exc:
            msg = f"exporter_error {exc}\n".encode("utf-8")
            self.send_response(500)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(msg)))
            self.end_headers()
            self.wfile.write(msg)


def main() -> None:
    server = ThreadingHTTPServer((LISTEN_HOST, LISTEN_PORT), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    thread.join()


if __name__ == "__main__":
    main()
