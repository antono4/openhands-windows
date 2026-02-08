# GPTOSS + OpenHands (Windows)

This repo gives you a **local OpenHands agent** on Windows that connects to your **local OpenAI-compatible model server** (e.g., `gpt-oss-120b` on `http://localhost:8000/v1`).
One command sets everything up: `setup.bat`.

---

**What You Get**

- A ready-to-run OpenHands agent container.
- A Windows-friendly CLI to chat and run code: `open hand/openhands_cli.py`
- Automatic cleanup of runtime containers after each CLI session.
- A workspace mounted from this repo into the agent (`/workspace`).

---

**Requirements**

- Windows 10/11
- Docker Desktop (running)
- Python 3.9+ (for the CLI)
- A local OpenAI-compatible model server at `http://localhost:8000/v1` (default auto-detect model id: `gpt-oss-120b`).

If your model endpoint is different, you can override it with env vars before running setup:

```
set LLM_MODEL=your-model-id
set LLM_BASE_URL=http://host.docker.internal:8000/v1
set LLM_API_KEY=local-llm
```

---

**Quick Start (One Command Setup)**

From the repo root:

```
setup.bat
```

When it finishes, run the CLI:

```
python "open hand\openhands_cli.py"
```

---

**Scripts**

```
setup.bat
cleanup.bat
```

---

**CLI Usage**

Interactive:

```
python "open hand\openhands_cli.py"
```

One-shot:

```
python "open hand\openhands_cli.py" --once "Run the command 'date' and reply with the exact output."
```

Keep runtime container running (no auto cleanup):

```
python "open hand\openhands_cli.py" --no-auto-stop
```

---

**Important Behavior Notes**

- The agent runs **inside a Linux container**.
- Use Linux commands (`ls`, `cat`, `ps`, `bash`), not Windows commands.
- The repo is mounted into the container at `/workspace`.
- After each CLI session, the runtime container is automatically removed to avoid RAM buildup.

---

**PostgreSQL Example (from agent)**

If Postgres is running on Windows, the agent can connect to it through:
`host.docker.internal`

Example command for the agent:

```
apt-get update && apt-get install -y postgresql-client
psql "postgresql://ata_user:ata_password@host.docker.internal:5432/ata_local_db" \
  -c "SELECT current_user, current_database(), version(), now();"
```

---

**What `setup.bat` Does**

- Ensures Docker is installed and running (tries to install with winget if missing).
- Detects the model id from `http://localhost:8000/v1/models`.
- Computes the correct Docker mount path for this repo.
- Starts `openhands-app` with the correct env and volume mount.
- Applies the runtime timeout patch and restarts the container.
- Cleans old runtime containers to prevent memory buildup.

---

**Move This Repo?**

If you move this folder to another location, just run:

```
setup.bat
```

It will remount the new path automatically.

---

**Troubleshooting**

- **Docker not running:** Start Docker Desktop, then rerun `setup.bat`.
- **Model not reachable:** Ensure your local server is running at `http://localhost:8000/v1`.
- **No responses:** Wait for Docker and the model server to fully load, then try again.
- **Commands failing:** Remember, the agent uses Linux commands inside the container.

---

**Cleanup (Manual)**

Preferred (script):

```
cleanup.bat
```

Stop and remove the main container:

```
docker rm -f openhands-app
```

Remove any leftover runtime containers:

```
docker ps -aq --filter "name=openhands-runtime-" | % { docker rm -f $_ }
```

---

If you want extra automation (startup scripts, shortcuts, Windows host tool access), just ask.
