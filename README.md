---
title: Clinic Agent
emoji: 🏥
colorFrom: green
colorTo: blue
sdk: docker
app_port: 7860
pinned: false
---

# Clinic Agent

A demo **clinic appointment booking** assistant: a **Streamlit** chat UI drives a **LangGraph** agent that talks to **OpenAI** (for intent and wording) and a local **SQLite** database for doctors, customers, and bookings.

The block above is **[Hugging Face Spaces](https://huggingface.co/docs/hub/spaces) metadata** (YAML front matter). **Hugging Face** hosts this app as a **Docker Space** ([`Dockerfile`](Dockerfile)); it does not affect local `streamlit run` usage.

## Requirements

- Python 3.10+ (3.11+ recommended)
- An [OpenAI API key](https://platform.openai.com/api-keys) (`OPENAI_API_KEY`). Without it, the app may fall back to more limited behavior for some steps.

## Setup

**Recommended (uv):** creates `.venv` and installs all dependencies (including `langgraph`).

```bash
cd clinic-agent
uv sync
cp .env.example .env
# Edit .env and set OPENAI_API_KEY
```

**Alternative (venv + pip):**

```bash
cd clinic-agent
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

The repo includes [`.vscode/settings.json`](.vscode/settings.json) so **Cursor/VS Code** uses `.venv/bin/python` as the default interpreter. Reload the window or pick that interpreter if the status bar still shows another Python (for example Homebrew 3.14).

## Run the app

**Public booking (patients):** only the chat UI is served — there is no link to staff screens in this process.

```bash
uv run streamlit run app.py
```

**Staff — doctor alerts (confidential):** run as a **separate** Streamlit app on another port (or another host). Patients should only receive the booking URL, not the admin URL.

```bash
uv run streamlit run admin_app.py --server.port 8502
```

With an activated venv, use `streamlit run app.py` and `streamlit run admin_app.py --server.port 8502` the same way.

The UI initializes the database on startup (see `data/db.py`). The SQLite file is stored as `data/clinic.db`.

**Note:** Use `streamlit run` so the Streamlit server and session behave correctly.

### Hugging Face Spaces

The Space uses the **Docker** SDK ([`Dockerfile`](Dockerfile)) because the Hub only allows `gradio`, `docker`, or `static` as native SDK types. The container runs **`app.py`** (patient chat) on port **7860**. The staff **`admin_app.py`** is not started in the Space; run it separately if you need it.

1. On [Hugging Face](https://huggingface.co), use **Spaces → New Space** (or **Create new Space** on your profile) with **Docker** as the SDK, or push this repo to a Space Git remote (see below).
2. Open the Space **Settings → Variables and secrets** and add a **secret** named **`OPENAI_API_KEY`** with your [OpenAI API key](https://platform.openai.com/api-keys). Secrets are available as environment variables at runtime (no `.env` file in the image).

**CLI:** with the [Hugging Face CLI](https://huggingface.co/docs/huggingface_hub/guides/cli) logged in, create the Space and push:

```bash
hf repos create YOUR_USERNAME/clinic-agent --repo-type space --space-sdk docker --exist-ok
git remote add huggingface https://huggingface.co/spaces/YOUR_USERNAME/clinic-agent.git
git push huggingface main
```

SQLite data on the Space filesystem is **demo-only** (can be lost on restart or rebuild unless you add [persistent storage](https://huggingface.co/docs/hub/spaces-storage)). For production, use managed storage or your own host.

### Admin — doctor alerts

After a patient completes booking, a row is queued in `doctor_booking_alerts`. Staff open **`admin_app.py`** (dark “Staff portal” UI): review pending alerts, copy the suggested message for email/SMS, then **Mark as notified to doctor**. Automatic email/SMS is not included; staff use their own channels.

Set **`ADMIN_ACCESS_PASSWORD`** in `.env` before exposing `admin_app.py` on a network. If it is unset, the admin app still works locally but shows a warning that the URL is not password-protected.

## Environment variables

| Variable                   | Description                                        |
|----------------------------|----------------------------------------------------|
| `OPENAI_API_KEY`           | OpenAI API key for GPT calls                       |
| `ADMIN_ACCESS_PASSWORD`    | Optional: staff gate for `admin_app.py` only       |

See `.env.example` for a template.

## Project layout

| Path | Role |
|------|------|
| `app.py` | Public entry: patient booking chat only |
| `admin_app.py` | Staff entry: doctor alerts (separate URL/port) |
| `ui/chat_ui.py` | Streamlit patient UI |
| `ui/admin_ui.py` | Streamlit staff UI (distinct theme + optional password) |
| `agents/booking_agent.py` | LangGraph graph, state, and message processing |
| `services/booking_service.py` | Slots and booking persistence |
| `services/doctor_service.py` | Doctor and speciality lookups |
| `data/db.py` | SQLite schema and seed data |
| `services/notification_service.py` | Queue alert after each confirmed booking |

## Optional: export the LangGraph diagram

To save a PNG of the graph (requires [Graphviz](https://graphviz.org/) on your system, e.g. `brew install graphviz` on macOS):

```bash
pip install pygraphviz   # after Graphviz is installed; see comment in requirements.txt
python agents/save_langgraph_flow.py
```

Output is written to `agents/langgraph_flow.png`.

## Troubleshooting

### `ModuleNotFoundError: No module named 'langgraph'`

You are almost certainly running the app with **system Python** instead of the project **`.venv`**. `langgraph` is installed only in that venv.

- Use **`uv run streamlit run app.py`**, or activate `.venv` first, then `streamlit run app.py`.
- In the editor, set the Python interpreter to **`clinic-agent/.venv/bin/python`** (Command Palette → “Python: Select Interpreter”).
