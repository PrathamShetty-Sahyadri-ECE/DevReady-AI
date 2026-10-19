# DevReady AI 🩺

A beginner-friendly Python and Linux **development-environment diagnostics tool**.
DevReady AI inspects your local environment, reports potential problems, and can
explain findings in plain language using a locally running AI model (Ollama).

---

## What it does

DevReady AI runs the following checks and outputs a structured report:

| Check | Details |
|---|---|
| **Python** | Version, executable path, implementation (CPython / PyPy) |
| **Operating system** | Platform, release, machine architecture, hostname |
| **Dependencies** | Installed / missing status and version for `requests`, `numpy`, `pandas` |
| **File permissions** | Readable / writable / executable flags on `main.py` |
| **Project files** | Existence check for `main.py`, `requirements.txt`, `devready/diagnostics.py` |
| **Disk space** | Total, used, and free GB + free percentage |
| **Network** | TCP connectivity to `example.com:443` with latency measurement |
| **Linux identity** | `id`, `groups`, sudo-group membership, `systemctl` path, NFS mount list |

Results can be:

- Printed to the **terminal** (CLI)
- Viewed in an interactive **Streamlit dashboard**
- Exported as a **JSON report**
- Explained in plain language by a **local Ollama AI model**

---

## Safety and limitations

- DevReady AI is a **diagnostic helper**, not a complete security audit or production monitoring system.
- A successful network check means a TCP handshake to `example.com:443` completed — it does not verify every internet service.
- Sudo group membership is reported, not validated as a full privilege audit.
- The NFS check lists currently mounted NFS filesystems; it does not verify an NFS server or attempt to mount anything.
- The AI model **only explains** collected results. It does not run shell commands or perform automatic remediation.
- Never commit API keys, secrets, or credentials to source control.

---

## Architecture

```text
devready-ai/
├── main.py                 # CLI entry point
├── app.py                  # Streamlit dashboard entry point
├── requirements.txt        # Python dependencies
├── .env.example            # Template for environment variable configuration
├── .gitignore
└── devready/               # Core package
    ├── __init__.py
    ├── diagnostics.py      # All environment checks (Python, OS, disk, network, Linux)
    └── llm_explainer.py    # Ollama REST API integration for AI explanation
```

**Data flow:**

```
main.py / app.py
     │
     ▼
devready/diagnostics.py  ──►  structured JSON report dict
     │
     ▼  (--explain / "Explain findings" button)
devready/llm_explainer.py  ──►  POST /api/generate  ──►  Ollama (local)
                                      │
                                      ▼
                               llama3.2:3b response
                               (falls back to built-in text summary if unreachable)
```

---

## Prerequisites

- **Python 3.11 – 3.14**
- **Ubuntu / WSL2** (for Linux-specific checks; all other checks work on any OS)
- **Ollama** running locally — required only for the `--explain` / "Explain findings" feature

---

## Setup

Clone the repository and create a virtual environment:

```bash
git clone https://github.com/PrathamShetty-Sahyadri-ECE/devready-ai.git
cd devready-ai
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

On **Windows** (PowerShell):

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

---

## Running the CLI

```bash
# Activate your virtual environment first
source .venv/bin/activate

# Print a full diagnostic report to the terminal
python main.py

# Save the report as JSON  (writes devready_report.json)
python main.py --json

# Ask the local AI model to explain the findings
python main.py --explain
```

> `--json` and `--explain` can be combined:
> ```bash
> python main.py --json --explain
> ```

---

## Running the Streamlit dashboard

```bash
source .venv/bin/activate
streamlit run app.py
```

Open the URL shown in the terminal (usually `http://localhost:8501`).

1. Click **"Run diagnostics"** to scan the environment.
2. Click **"Explain findings"** to get an AI-generated plain-language explanation.
3. Click **"Download JSON report"** to save the full report as a file.

---

## Local AI explanation — Ollama + Llama 3.2

The `--explain` flag and the "Explain findings" button call a locally running
[Ollama](https://ollama.com) instance via its REST API.
**No data is sent to any external service.**

### Install Ollama and pull the model

**On Linux / WSL2:**

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3.2:3b
ollama serve          # starts the server on port 11434
```

**On Windows** (if running Ollama on the Windows host):

Download and install Ollama from [ollama.com](https://ollama.com), then in PowerShell:

```powershell
ollama pull llama3.2:3b
# Ollama starts automatically as a Windows service after installation
```

---

### Scenario A — Ollama running in the same environment as DevReady AI

If both Ollama and DevReady AI run inside WSL2 (or both on Windows):

```bash
export OLLAMA_BASE_URL="http://localhost:11434"
python main.py --explain
```

---

### Scenario B — Ollama on Windows, DevReady AI inside WSL2

When Ollama runs on the **Windows host** and DevReady AI runs **inside WSL2**,
you must point the app at the Windows host IP visible from within WSL2.

Find your WSL2 host gateway IP:

```bash
ip route show default | awk '{print $3}'
# typically something like 172.19.224.1
```

Then export the variable before running:

```bash
export OLLAMA_BASE_URL="http://172.19.224.1:11434"
python main.py --explain
```

> **Default value:** The app already defaults to `http://172.19.224.1:11434`.
> If your gateway IP is the same, no configuration is needed.
> Run the command above to confirm your specific IP.

---

### Environment variables

| Variable | Default | Description |
|---|---|---|
| `OLLAMA_BASE_URL` | `http://172.19.224.1:11434` | Full base URL of the Ollama server |
| `OLLAMA_MODEL` | `llama3.2:3b` | Ollama model name to use for explanations |

Copy `.env.example` to `.env` and edit as needed, or export the variables directly in your shell:

```bash
export OLLAMA_BASE_URL="http://localhost:11434"
export OLLAMA_MODEL="llama3.2:3b"
```

> **Never commit your `.env` file.** It is already listed in `.gitignore`.

If Ollama is unreachable, the app falls back to a built-in text summary — it never crashes.

---

## Technologies used

| Technology | Role |
|---|---|
| Python 3.11+ | Core language |
| [Streamlit](https://streamlit.io) | Interactive web dashboard |
| [Ollama](https://ollama.com) | Local LLM server |
| Llama 3.2 (3B) | AI explanation model |
| `importlib.metadata` | Dependency version detection |
| `subprocess` | Linux identity commands (`id`, `groups`, `findmnt`) |
| `socket` | TCP connectivity checks |
| `shutil` | Disk usage |
| `urllib.request` | Ollama REST API calls (stdlib only, no extra HTTP library) |

---

## Suggested future improvements

- Add `pytest` tests for individual check functions.
- Add a user-approved, allowlisted remediation layer (e.g. `pip install <missing>`).
- Add safe NFS server reachability checks using a user-supplied hostname.
- Add logging with configurable verbosity levels.
- Add a GitHub Actions CI workflow.
- Support configurable dependency lists via CLI flags or a config file.




