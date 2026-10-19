from __future__ import annotations

import json
import os
from typing import Any
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError


def local_explanation(report: dict[str, Any]) -> str:
    lines = ["Local diagnostic summary (AI model was not used):"]

    for item in report.get("dependencies", []):
        name = item.get("name", "unknown package")
        status = item.get("status", "UNKNOWN").lower()
        lines.append(f"- Python package '{name}' is {status}.")

    lines.append(
        "Note: These checks are limited diagnostics, not a complete "
        "security or system health audit."
    )
    return "\n".join(lines)


def explain_report(report: dict[str, Any]) -> str:
    """Explain diagnostic findings using local Ollama, with a fallback."""
    base_url = os.getenv(
        "OLLAMA_BASE_URL", "http://172.19.224.1:11434"
    ).rstrip("/")
    model = os.getenv("OLLAMA_MODEL", "llama3.2:3b")

    prompt = (
        "You are a cautious Python and Linux troubleshooting assistant. "
        "Explain this diagnostic report in beginner-friendly language. "
        "Separate confirmed findings from possibilities. Do not suggest "
        "destructive commands or request secrets.\n\n"
        "Diagnostic report:\n"
        + json.dumps(report, indent=2, default=str)
    )

    payload = json.dumps({
        "model": model,
        "prompt": prompt,
        "stream": False,
    }).encode("utf-8")

    request = Request(
        f"{base_url}/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urlopen(request, timeout=120) as response:
            result = json.loads(response.read().decode("utf-8"))

        explanation = result.get("response", "").strip()
        if explanation:
            return "AI explanation (local Ollama model):\n\n" + explanation

        return local_explanation(report)

    except (URLError, HTTPError, TimeoutError, OSError, ValueError) as exc:
        return (
            "The local AI model could not be reached, so a basic explanation "
            "is shown instead.\n"
            f"Connection detail: {exc}\n\n"
            + local_explanation(report)
        )
