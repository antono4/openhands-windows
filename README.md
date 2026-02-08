# OpenHands Windows Bridge

> **Run OpenHands AI coding agent on Windows with local LLM models**

A complete Windows integration for [OpenHands](https://github.com/All-Hands-AI/OpenHands) that enables seamless operation with local OpenAI-compatible model servers. One-command setup, automatic Docker configuration, and intelligent container lifecycle management.

[![Windows](https://img.shields.io/badge/Windows-10%2F11-0078D6?logo=windows&logoColor=white)](https://www.microsoft.com/windows)
[![Docker](https://img.shields.io/badge/Docker-Required-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## Why This Exists

OpenHands is a powerful AI coding agent, but running it on Windows with local models requires:
- Complex Docker path translations (Windows → Docker POSIX paths)
- Manual container lifecycle management
- Custom runtime patches for Windows port ranges
- Network configuration for Docker Desktop's `host.docker.internal`

This project solves all of that with **one command**.

---

## Features

- **One-Command Setup**: `setup.bat` handles everything automatically
- **Local LLM Integration**: Connect to any OpenAI-compatible server (default: `localhost:8000`)
- **Automatic Path Translation**: Windows paths converted to Docker-compatible mounts
- **Container Lifecycle Management**: Auto-cleanup prevents RAM buildup
- **Windows Runtime Patch**: Custom `docker_runtime.py` with Windows-optimized port ranges
- **Interactive CLI**: Simple Python client for conversational interactions
- **Model Auto-Detection**: Automatically finds your local model ID
- **Persistent Workspace**: Repository mounted as `/workspace` inside the container

---

## Quick Start

### Prerequisites

- **Windows 10/11**
- **Docker Desktop** (running)
- **Python 3.9+**
- **Local LLM server** at `http://localhost:8000/v1` (OpenAI-compatible)

### Installation

```bash
# Clone the repository
git clone https://github.com/Mhrnqaruni/openhands-windows.git
cd openhands-windows

# Run setup (installs Docker if missing, configures everything)
setup.bat
```

That's it! Setup will:
1. Check/install Docker Desktop
2. Auto-detect your local model
3. Convert Windows paths to Docker format
4. Start OpenHands container with correct configuration
5. Apply Windows runtime patch
6. Clean up old containers

### Usage

**Interactive Mode:**
```bash
python "open hand\openhands_cli.py"
```

**One-Shot Command:**
```bash
python "open hand\openhands_cli.py" --once "Create a Python script that prints 'Hello World'"
```

**Keep Container Running (no auto-cleanup):**
```bash
python "open hand\openhands_cli.py" --no-auto-stop
```

**Direct LLM Testing:**
```bash
python chat.py
```

---

## How It Works

### 1. Automatic Setup (`setup.bat`)

```batch
setup.bat performs 7 critical steps:
├─ Check Docker installation (auto-install via winget if missing)
├─ Detect local LLM model from /v1/models endpoint
├─ Convert Windows path to Docker POSIX format
│  Example: C:\Users\You\project → /run/desktop/mnt/host/c/Users/You/project
├─ Start openhands-app container with proper env vars
├─ Patch docker_runtime.py with Windows port ranges
├─ Restart container to apply patch
└─ Clean up old runtime containers
```

### 2. Custom Docker Runtime Patch

The included `docker_runtime.py` modifies OpenHands to use Windows-compatible port ranges:

```python
# Standard OpenHands (causes conflicts on Windows)
EXECUTION_SERVER_PORT_RANGE = (30000, 39999)

# Our Windows patch
if os.name == 'nt' or platform.release().endswith('microsoft-standard-WSL2'):
    EXECUTION_SERVER_PORT_RANGE = (30000, 34999)
    VSCODE_PORT_RANGE = (35000, 39999)
    APP_PORT_RANGE_1 = (40000, 44999)
    APP_PORT_RANGE_2 = (45000, 49151)
```

### 3. CLI Client (`openhands_cli.py`)

- **Event Polling**: Monitors OpenHands API for agent responses
- **Automatic Cleanup**: Removes runtime containers after each session
- **Conversation Management**: Handles persistent conversation state
- **Error Recovery**: Graceful handling of timeouts and network issues

---

## Configuration

### Custom Model/Endpoint

```batch
# Set before running setup.bat
set LLM_MODEL=your-model-id
set LLM_BASE_URL=http://host.docker.internal:8000/v1
set LLM_API_KEY=your-api-key

setup.bat
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_MODEL` | Auto-detected | Model ID from `/v1/models` |
| `LLM_BASE_URL` | `http://host.docker.internal:8000/v1` | LLM server endpoint |
| `LLM_API_KEY` | `local-llm` | API key for authentication |
| `OPENHANDS_URL` | `http://localhost:3000` | OpenHands server URL |

---

## Examples

### Connect to PostgreSQL from Agent

Your agent runs inside a Linux container, so Windows services are accessible via `host.docker.internal`:

```bash
# From inside the agent
apt-get update && apt-get install -y postgresql-client
psql "postgresql://user:password@host.docker.internal:5432/mydb" -c "SELECT version();"
```

### Access Windows Files

The repository is automatically mounted at `/workspace`:

```bash
# Agent can read/write files in your repo
ls /workspace
cat /workspace/README.md
```

---

## Technical Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Windows Host                           │
│                                                              │
│  ┌──────────────┐         ┌─────────────────────────────┐  │
│  │  setup.bat   │────────▶│  Docker Desktop             │  │
│  └──────────────┘         │                             │  │
│                           │  ┌───────────────────────┐  │  │
│  ┌──────────────┐         │  │ openhands-app         │  │  │
│  │ CLI Client   │◀───────▶│  │ :3000 (API)           │  │  │
│  │ (Python)     │  HTTP   │  │                       │  │  │
│  └──────────────┘         │  │ + docker_runtime.py   │  │  │
│                           │  │   (patched)           │  │  │
│                           │  └───────┬───────────────┘  │  │
│                           │          │ spawns           │  │
│                           │          ▼                  │  │
│  ┌──────────────┐         │  ┌───────────────────────┐  │  │
│  │ Local LLM    │◀────────┼──│ openhands-runtime-*   │  │  │
│  │ :8000        │  API    │  │ (auto-cleaned)        │  │  │
│  └──────────────┘         │  └───────────────────────┘  │  │
│                           └─────────────────────────────┘  │
│                                                              │
│  /workspace ──────────────▶ mounted into containers         │
└─────────────────────────────────────────────────────────────┘
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| **Docker not running** | Start Docker Desktop, wait for it to be ready, then rerun `setup.bat` |
| **Model not reachable** | Ensure your LLM server is running at `http://localhost:8000/v1` |
| **No agent responses** | Check Docker logs: `docker logs openhands-app` |
| **Commands failing in agent** | Remember the agent uses **Linux commands** (`ls`, `cat`, not `dir`, `type`) |
| **Port conflicts** | Stop other services using ports 3000, 30000-49151 |
| **Path not found** | If you move the repo, just run `setup.bat` again to remount |

---

## Cleanup

```batch
# Recommended: Use cleanup script
cleanup.bat

# Manual cleanup
docker rm -f openhands-app
docker ps -aq --filter "name=openhands-runtime-" | ForEach-Object { docker rm -f $_ }
```

---

## Project Structure

```
openhands-windows/
├── setup.bat                 # One-command setup script
├── cleanup.bat               # Container cleanup script
├── chat.py                   # Direct LLM testing utility
├── open hand/
│   ├── openhands_cli.py      # CLI client for OpenHands
│   ├── docker_runtime.py     # Windows-patched runtime
│   └── .venv/                # Python virtual environment
└── README.md
```

---

## How This Differs from Standard OpenHands

| Feature | Standard OpenHands | This Project |
|---------|-------------------|--------------|
| **Windows Support** | Manual setup required | One-command automation |
| **Path Translation** | Manual configuration | Automatic Windows→Docker conversion |
| **Local Models** | Cloud-focused | Optimized for local LLM servers |
| **Container Cleanup** | Manual | Automatic lifecycle management |
| **Port Ranges** | Linux-optimized | Windows-compatible ranges |
| **Setup Time** | 30+ minutes | < 5 minutes |

---

## Contributing

Contributions welcome! Areas for improvement:

- [ ] Support for WSL2 without Docker Desktop
- [ ] GUI wrapper for non-technical users
- [ ] Automatic LLM server detection (vLLM, Ollama, etc.)
- [ ] Windows service integration
- [ ] Multi-model switching

---

## License

MIT License - See [LICENSE](LICENSE) for details

---

## Acknowledgments

- [OpenHands](https://github.com/All-Hands-AI/OpenHands) - The underlying AI coding agent
- Built for Windows users who want local LLM control
- Special thanks to the Docker and Python communities

---

## Author

**Mehran Gharuni** - [GitHub](https://github.com/Mhrnqaruni)

*Built as part of demonstrating advanced Windows/Docker integration skills and local LLM deployment expertise.*

---

**Star this repo if it helped you run OpenHands on Windows!**
