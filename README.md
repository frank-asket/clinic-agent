---
title: Clinic Agent
emoji: 🏥
colorFrom: green
colorTo: blue
sdk: docker
app_port: 7860
pinned: false
short_description: Streamlit + LangGraph clinic booking demo (OpenAI + SQLite)
---

<div align="center">

# Clinic Agent

**Conversational appointment booking demo** — a Streamlit chat UI, a LangGraph agent, OpenAI for language and intent, and SQLite for schedules and records.

[![Live demo — Hugging Face Space](https://img.shields.io/badge/🤗_Hugging_Face-Live-demo-FFD21F?style=for-the-badge&logo=huggingface&logoColor=000)](https://huggingface.co/spaces/franck-asket/clinic-agent)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-UI-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io/)
[![LangGraph](https://img.shields.io/badge/LangGraph-Agent-1C3C3C?style=for-the-badge)](https://github.com/langchain-ai/langgraph)

[**Open the live app →**](https://huggingface.co/spaces/franck-asket/clinic-agent)

</div>

> The YAML block at the very top is [Hugging Face Spaces](https://huggingface.co/docs/hub/spaces) metadata for the Docker Space ([`Dockerfile`](Dockerfile)). It does not change local development.

---

## Highlights

| | |
| :--- | :--- |
| **Patient experience** | Guided chat to pick speciality, doctor, slot, and confirm booking |
| **Agent runtime** | LangGraph graph with checkpoints and structured conversation state |
| **LLM** | OpenAI (e.g. `gpt-4o-mini`) for wording and ambiguous intent |
| **Data** | SQLite — doctors, customers bookings, optional staff alert queue |
| **Hosted demo** | [**Hugging Face Space**](https://huggingface.co/spaces/franck-asket/clinic-agent) — Docker-based; set `OPENAI_API_KEY` in Space secrets |

---

## Quick start

**Requirements:** Python 3.10+ (3.11+ recommended), [OpenAI API key](https://platform.openai.com/api-keys) as `OPENAI_API_KEY`.

**Install (recommended — uv):**

```bash
cd clinic-agent
uv sync
cp .env.example .env
# Edit .env — set OPENAI_API_KEY
```

**Install (venv + pip):**

```bash
cd clinic-agent
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

The repo includes [`.vscode/settings.json`](.vscode/settings.json) so **Cursor / VS Code** can use `.venv/bin/python` as the default interpreter.

---

## Run locally

**Patients — public chat**

```bash
uv run streamlit run app.py
```

**Staff — doctor alerts (separate process / URL)**

```bash
uv run streamlit run admin_app.py --server.port 8502
```

With an activated venv, use `streamlit run …` directly.

The UI initializes the database on startup (`data/db.py`). SQLite lives at `data/clinic.db`.

Set **`ADMIN_ACCESS_PASSWORD`** in `.env` before exposing `admin_app.py` on a network. If unset, local admin still runs but warns that the URL is not gated.

---

## Live demo (Hugging Face)

**App:** [huggingface.co/spaces/franck-asket/clinic-agent](https://huggingface.co/spaces/franck-asket/clinic-agent)

The Space runs the **patient** app only (`app.py` on port **7860** via Docker). It does **not** start `admin_app.py`.

1. Open [Space settings → Variables and secrets](https://huggingface.co/spaces/franck-asket/clinic-agent/settings).
2. Add a **secret** named **`OPENAI_API_KEY`** ([create a key](https://platform.openai.com/api-keys) if needed).
3. Wait for the build to show **Running**, then use the **App** tab.

**Deploy / sync from CLI** (with [`hf` CLI](https://huggingface.co/docs/huggingface_hub/guides/cli) authenticated):

```bash
hf repos create YOUR_USERNAME/clinic-agent --repo-type space --space-sdk docker --exist-ok
git remote add huggingface https://huggingface.co/spaces/YOUR_USERNAME/clinic-agent.git
git push huggingface main
```

SQLite on the Space is **ephemeral** unless you use [persistent storage](https://huggingface.co/docs/hub/spaces-storage) or an external database — treat the hosted instance as a **demo**.

---

## Environment variables

| Variable | Description |
| -------- | ----------- |
| `OPENAI_API_KEY` | OpenAI API key for GPT calls |
| `ADMIN_ACCESS_PASSWORD` | Optional gate for `admin_app.py` only |

See [`.env.example`](.env.example).

---

## Project layout

| Path | Role |
| ---- | ---- |
| `app.py` | Public entry — patient booking chat |
| `admin_app.py` | Staff entry — doctor alerts |
| `ui/chat_ui.py` | Streamlit patient UI |
| `ui/admin_ui.py` | Streamlit staff UI |
| `agents/booking_agent.py` | LangGraph graph, state, message handling |
| `services/booking_service.py` | Slots and bookings |
| `services/doctor_service.py` | Doctors and specialities |
| `data/db.py` | SQLite schema and seed data |
| `services/notification_service.py` | Queue alerts after confirmed bookings |

---

## Optional: LangGraph diagram

Export a PNG of the graph (needs [Graphviz](https://graphviz.org/) on the host, e.g. `brew install graphviz` on macOS):

```bash
pip install pygraphviz   # after Graphviz is installed; see requirements.txt
python agents/save_langgraph_flow.py
```

Output: `agents/langgraph_flow.png`.

---

## Troubleshooting

### `ModuleNotFoundError: No module named 'langgraph'`

You are likely using **system Python** instead of the project **`.venv`**.

- Prefer **`uv run streamlit run app.py`**, or activate `.venv` first.
- In the editor: **Python: Select Interpreter** → `clinic-agent/.venv/bin/python`.
