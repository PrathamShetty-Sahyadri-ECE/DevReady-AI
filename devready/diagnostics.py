from __future__ import annotations

import importlib.metadata
import json
import os
import platform
import shutil
import socket
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_PACKAGES = ["requests", "numpy", "pandas"]
DEFAULT_HOSTS = [("example.com", 443)]


def _run(command: list[str], timeout: int = 5) -> dict[str, Any]:
    """Run a fixed diagnostic command and return its result safely."""
    try:
        result = subprocess.run(
            command, capture_output=True, text=True, timeout=timeout, check=False
        )
        return {
            "returncode": result.returncode,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
        }
    except FileNotFoundError:
        return {"returncode": 127, "stdout": "", "stderr": f"Command not found: {command[0]}"}
    except subprocess.TimeoutExpired:
        return {"returncode": 124, "stdout": "", "stderr": f"Command timed out: {' '.join(command)}"}
    except OSError as exc:
        return {"returncode": 1, "stdout": "", "stderr": str(exc)}


def check_python() -> dict[str, Any]:
    return {
        "python_version": platform.python_version(),
        "python_executable": sys.executable,
        "implementation": platform.python_implementation(),
    }


def check_system() -> dict[str, Any]:
    return {
        "system": platform.system(),
        "release": platform.release(),
        "machine": platform.machine(),
        "hostname": socket.gethostname(),
    }


def check_dependencies(packages: list[str] | None = None) -> list[dict[str, Any]]:
    packages = packages or DEFAULT_PACKAGES
    results = []
    for package in packages:
        try:
            installed_version = importlib.metadata.version(package)
            results.append({"name": package, "status": "INSTALLED", "version": installed_version})
        except importlib.metadata.PackageNotFoundError:
            results.append({"name": package, "status": "MISSING", "version": None})
        except Exception as exc:
            results.append({"name": package, "status": "ERROR", "detail": str(exc), "version": None})
    return results


def check_file_permissions(path: str = "main.py") -> dict[str, Any]:
    target = Path(path)
    return {
        "path": str(target.resolve()),
        "exists": target.exists(),
        "is_file": target.is_file(),
        "readable": os.access(target, os.R_OK),
        "writable": os.access(target, os.W_OK),
        "executable": os.access(target, os.X_OK),
    }


def check_project_files(paths: list[str] | None = None) -> list[dict[str, Any]]:
    paths = paths or ["main.py", "requirements.txt", "devready/diagnostics.py"]
    return [{"path": p, "exists": Path(p).is_file()} for p in paths]


def check_disk_space(path: str = ".") -> dict[str, Any]:
    total, used, free = shutil.disk_usage(path)
    gib = 1024 ** 3
    return {
        "path": str(Path(path).resolve()),
        "total_gb": round(total / gib, 2),
        "used_gb": round(used / gib, 2),
        "free_gb": round(free / gib, 2),
        "free_percent": round((free / total) * 100, 1) if total else 0,
    }


def check_network(hosts: list[tuple[str, int]] | None = None, timeout: float = 4.0) -> list[dict[str, Any]]:
    hosts = hosts or DEFAULT_HOSTS
    results = []
    for host, port in hosts:
        started = time.perf_counter()
        try:
            with socket.create_connection((host, port), timeout=timeout):
                results.append({
                    "host": host, "port": port, "status": "SUCCESS",
                    "latency_ms": round((time.perf_counter() - started) * 1000, 1),
                    "error": None,
                })
        except OSError as exc:
            results.append({
                "host": host, "port": port, "status": "FAILED",
                "latency_ms": None, "error": str(exc),
            })
    return results


def check_linux_identity() -> dict[str, Any]:
    if platform.system() != "Linux":
        return {"supported": False, "message": "Linux identity checks are only available on Linux."}

    identity = _run(["id"])
    groups = _run(["groups"])
    sudo_membership = "sudo" in groups["stdout"].split()
    systemctl_path = shutil.which("systemctl")
    nfs_mounts = _run(["findmnt", "-t", "nfs,nfs4", "-n", "-o", "SOURCE,TARGET,FSTYPE"])

    return {
        "supported": True,
        "identity": identity["stdout"] if identity["returncode"] == 0 else identity["stderr"],
        "groups": groups["stdout"] if groups["returncode"] == 0 else groups["stderr"],
        "sudo_group_member": sudo_membership,
        "systemctl_available": bool(systemctl_path),
        "systemctl_path": systemctl_path,
        "nfs_mounts": nfs_mounts["stdout"].splitlines() if nfs_mounts["returncode"] == 0 and nfs_mounts["stdout"] else [],
        "nfs_check_note": "No listed NFS mounts does not prove NFS is broken; this only reports currently mounted NFS filesystems.",
    }


def run_diagnostics() -> dict[str, Any]:
    """Run checks and collect each result into one JSON-serializable report."""
    report: dict[str, Any] = {
        "app": "DevReady AI",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "python": check_python(),
        "system": check_system(),
        "dependencies": check_dependencies(),
        "file_permissions": check_file_permissions("main.py"),
        "project_files": check_project_files(),
        "disk": check_disk_space("."),
        "network": check_network(),
        "linux": check_linux_identity(),
    }
    return report


def summarize(report: dict[str, Any]) -> dict[str, int]:
    dependency_missing = sum(item.get("status") == "MISSING" for item in report.get("dependencies", []))
    project_missing = sum(not item.get("exists", False) for item in report.get("project_files", []))
    network_failed = sum(item.get("status") == "FAILED" for item in report.get("network", []))
    permission_problems = 0
    permissions = report.get("file_permissions", {})
    if permissions.get("exists"):
        permission_problems = sum(not permissions.get(key, False) for key in ("readable", "writable"))
    else:
        permission_problems = 1
    return {
        "missing_dependencies": dependency_missing,
        "missing_project_files": project_missing,
        "failed_network_checks": network_failed,
        "file_permission_issues": permission_problems,
    }


def save_json_report(report: dict[str, Any], filename: str = "devready_report.json") -> str:
    path = Path(filename)
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return str(path.resolve())
