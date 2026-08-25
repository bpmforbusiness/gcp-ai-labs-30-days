# Day 6: Building AI Agents with ADK — The Foundation

**Series:** 30 Labs, 30 Days · **Topic:** GCP AI · **Product:** Google ADK, Gemini
**Codelab:** [Building AI Agents with ADK: A Comprehensive Guide](https://codelabs.developers.google.com/codelabs/cloud-run/building-ai-agents-with-adk) · Short URL: `goo.gle/adk-foundation`
**Date:** 2026-08-25 · **Status:** ✅ Complete

> 🎬 **Watch the video:** [Day 6 — Build a Personal AI Agent on Google Cloud using ADK](https://youtu.be/IgDD7pkJ-c0)

> 📘 **FOLLOW ALONG: [`LAB_MANUAL.md`](LAB_MANUAL.md)** — the complete step-by-step implementation manual (env setup with `uv`, `adk create`, agent code, terminal + web UI run, troubleshooting). Use it while doing this lab — every command is copy-paste ready.

## 🧠 The AI Concept: What Makes an "Agent"

**An AI agent is a smart program that acts on your behalf** — it perceives its digital environment, makes decisions, and takes actions to reach a goal, with an LLM as its "brain." After Days 2-5 used ADK to build MCP-powered and BigQuery agents, **today is the clean foundation**: a bare conversational agent built from scratch, so you understand every moving part before adding tools.

**The build:** a **Personal Assistant Agent** — a single-agent conversational bot. Minimal but complete: one `agent.py` (Agent class + model + instruction), one `__init__.py` (package marker), one `.env` (credentials). This is the base you'll extend into the **Multi-Agent System (MAS)** in the next labs.

**Why it matters:** this is ADK from zero — the exact same framework you'll use for every advanced agent ahead. Master `adk create` + `adk run` + `adk web` now, and the rest of the series is additive.

## 🛠️ The Build (Step-by-step)

### What you'll build
- A **Personal Assistant Agent** (Gemini-powered conversational bot)
- Run it in the **terminal** (`adk run`) and the **web dev UI** (`adk web`)

### Key steps
1. **(Optional) Create a GCP project** (or use a provisioned one)
2. **Environment setup:**
   - `gcloud config set project <id>` + enable API `gcloud services enable aiplatform.googleapis.com`
   - `mkdir -p ai-agents-adk && cd ai-agents-adk`
   - **uv** (fast Rust-based package manager): `uv venv --python 3.12` + `source .venv/bin/activate` + `uv pip install --no-cache google-adk`
3. **Create the agent:** `adk create personal_assistant`
   - Model: `gemini-3.5-flash` · Backend: **Vertex AI** (option 2) · Project ID (verify) · Region: `global`
   - → generates `agent.py`, `__init__.py`, `.env`
4. **Explore the code:**
   - `agent.py` — imports `Agent`, sets `name`, `model="gemini-3.5-flash"`, `description`, `instruction` (the system prompt/persona)
   - `__init__.py` — `from . import agent` (makes it a package)
   - `.env` — `GOOGLE_GENAI_USE_ENTERPRISE=1`, `GOOGLE_CLOUD_PROJECT`, `GOOGLE_CLOUD_LOCATION`
5. **Run in terminal:** `adk run personal_assistant` → chat with `[user]:` prompt
6. **Run in web UI:** `adk web --allow_origins "regex:https://.*\.cloudshell\.dev"` → http://localhost:8000 → full chat UI + debug/event inspection

## 💰 Cost & Free Tier

Uses Vertex AI (Gemini) — minimal cost for a conversational lab; small or free under trial credits. Enabling + disabling the API avoids ongoing charges.

## 📚 What I Learned
- *(to be filled after performing the lab)*

## ⚠️ Gotchas / Failures
- **"API method requires billing"** → check Project ID in `.env`, link the trial billing account
- **"Vertex AI API has not been used"** → `gcloud services enable aiplatform.googleapis.com`
- Must `source .venv/bin/activate` again if the terminal closes
- `adk web` from Cloud Shell needs the `--allow_origins` flag to open in the web preview
- `uv` replaces `venv` (much faster)
- *(add your own here)*

## 🚀 Beyond the Lab
- Add **tools/functions** to the agent (function calling) — the next ADK step
- Hook it to **MCP** (revisit Day 2) or **BigQuery** (Day 5)
- **Multi-agent orchestration** (part 2 of this series: Multi-Agent System)
- *(add your own here)*

## 🎬 Video
[▶️ Watch Day 6](youtube-link)

---
*Built by [Abdul Qaadir](https://linktr.ee/bpmforbusiness) — 30 Labs, 30 Days on Google Cloud.*