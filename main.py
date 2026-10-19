from __future__ import annotations

import argparse
import json
from pathlib import Path

from devready.diagnostics import run_diagnostics, save_json_report, summarize
from devready.llm_explainer import explain_report


def print_report(report: dict) -> None:
    print(f"\n=== {report['app']} ===")
    print("Timestamp (UTC):", report["timestamp_utc"])
    print("\n--- Python ---")
    print("Version:", report["python"]["python_version"])
    print("Executable:", report["python"]["python_executable"])
    print("\n--- Operating System ---")
    for key, value in report["system"].items():
        print(f"{key.replace('_', ' ').title()}: {value}")
    print("\n--- Dependencies ---")
    for item in report["dependencies"]:
        version = f" (version {item['version']})" if item.get("version") else ""
        print(f"{item['name']}: {item['status']}{version}")
    print("\n--- File Permissions ---")
    for key, value in report["file_permissions"].items():
        print(f"{key.replace('_', ' ').title()}: {value}")
    print("\n--- Project Files ---")
    for item in report["project_files"]:
        print(f"{item['path']}: {'FOUND' if item['exists'] else 'MISSING'}")
    print("\n--- Disk Space ---")
    for key, value in report["disk"].items():
        print(f"{key.replace('_', ' ').title()}: {value}")
    print("\n--- Network ---")
    for item in report["network"]:
        print(f"{item['host']}:{item['port']} - {item['status']}")
        if item.get("latency_ms") is not None:
            print("  Latency:", item["latency_ms"], "ms")
        if item.get("error"):
            print("  Reason:", item["error"])
    print("\n--- Linux Administration ---")
    linux = report["linux"]
    if not linux.get("supported"):
        print(linux.get("message"))
    else:
        print("Identity:", linux.get("identity"))
        print("Groups:", linux.get("groups"))
        print("Sudo group member:", linux.get("sudo_group_member"))
        print("systemctl available:", linux.get("systemctl_available"))
        print("systemctl path:", linux.get("systemctl_path"))
        print("NFS mounts:", linux.get("nfs_mounts") or "No NFS mounts detected")
        print(linux.get("nfs_check_note"))
    print("\n--- Issue Summary ---")
    for key, value in summarize(report).items():
        print(f"{key.replace('_', ' ').title()}: {value}")
    print("\nEnvironment check completed.")


def main() -> None:
    parser = argparse.ArgumentParser(description="DevReady AI development environment diagnostics")
    parser.add_argument("--json", action="store_true", help="Save report to devready_report.json")
    parser.add_argument("--explain", action="store_true", help="Explain findings using OpenAI API if configured")
    args = parser.parse_args()

    report = run_diagnostics()
    print_report(report)

    if args.json:
        print("\nJSON report saved to:", save_json_report(report))

    if args.explain:
        print("\n--- Explanation ---")
        print(explain_report(report))


if __name__ == "__main__":
    main()
