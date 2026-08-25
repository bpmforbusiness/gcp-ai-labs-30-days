# Day 7: Build Multi-Agent Systems with ADK

**Series:** 30 Labs, 30 Days · **Topic:** GCP AI · **Product:** Google ADK, Gemini
**Codelab:** [Build Multi-Agent Systems with ADK](https://codelabs.developers.google.com/codelabs/production-ready-ai-with-gc/3-developing-agents/build-a-multi-agent-system-with-adk)
**Date:** 2026-08-26 · **Status:** 🚧 In Progress

> 📘 **FOLLOW ALONG: [`LAB_MANUAL.md`](LAB_MANUAL.md)** — the complete step-by-step implementation manual (agent hierarchy, session state, SequentialAgent, LoopAgent, ParallelAgent, full code). Use it while doing this lab — every command and code block is copy-paste ready.

> 🔗 **Starter repo:** `git clone --depth 1 https://github.com/GoogleCloudPlatform/devrel-demos.git devrel-demos-multiagent-lab`

## 🧠 The AI Concept: From One Agent to a TEAM of Agents

**Day 6 built a single agent. Today, agents work together.** Instead of one complex prompt, ADK organizes agents into a **hierarchical tree** — a `root_agent` parent that transfers conversations to specialized sub-agents, which can themselves be parents. The parent decides where to send work (automatically via sub-agent `description`, or explicitly via `instruction`).

Then come the **workflow agents** — the real power:
- **`SequentialAgent`** — runs sub-agents one after another (research → write → save)
- **`LoopAgent`** — repeats a cycle until done (a "writer's room": researcher → screenwriter → critic, looping until the critic approves)
- **`ParallelAgent`** — fans out independent tasks concurrently (box office + casting research at the same time)

**Why it matters:** this is how real agentic systems work in production — a team of specialized agents collaborating, passing work through shared **session state** (key templating like `{ PLOT_OUTLINE? }`), each doing one thing reliably instead of one monolithic prompt doing everything badly.

## 🛠️ The Build (Step-by-step)

### What you'll build
1. **Travel planning agent** — parent + sub-agents with automatic and explicit transfers
2. **Movie pitch generator** — a "writer's room" with SequentialAgent → LoopAgent → ParallelAgent producing a full pitch file

### Key steps
1. **Setup:** Cloud Shell → `gcloud config set project` → enable `aiplatform.googleapis.com`
2. **Clone starter repo:** `devrel-demos.git` → move `adk_multiagent_systems` → `uv venv` + `uv pip install -r requirements.txt` → `.env` (VertexAI, project ID, `MODEL="gemini-2.5-flash"`) → copy to sub-dirs
3. **Agent hierarchy:** `parent_and_subagents/agent.py` — add `sub_agents=[travel_brainstormer, attractions_planner]` → test auto-transfer (description) → add explicit transfer instructions → test peer transfers
4. **Session state:** `save_attractions_to_state` tool writes to `tool_context.state["attractions"]` → read via `{ attractions? }` templating → inspect in ADK Web UI State tab
5. **SequentialAgent:** `workflow_agents` — greeter → film_concept_team (researcher → screenwriter → file_writer) → verify the written file + event graph
6. **LoopAgent:** add `critic` agent with `exit_loop` + `writers_room` LoopAgent (`max_iterations=5`) → watch the loop iterate until the critic approves
7. **ParallelAgent:** `box_office_researcher` + `casting_agent` in a `preproduction_team` ParallelAgent (each with `output_key`) → `file_writer` gathers all reports into one file

## 💰 Cost & Free Tier

**Less than $1 USD** for the whole lab. New users get the $300 Free Trial. Delete resources after (or keep for the next lab in the series).

## 📚 What I Learned
- *(to be filled after performing the lab)*

## ⚠️ Gotchas / Failures
- **Read agent files bottom-to-top** — sub-agents must be defined before being assigned to a parent
- `.env` must be **copied into sub-agent directories** (`parent_and_subagents/.env`, `workflow_agents/.env`) or agents can't authenticate
- `adk web` needs **Web Preview → Change Port → 8000** in Cloud Shell
- Use `adk web --reload_agents` for live reload while editing
- SequentialAgent gives **no intermediate messages** — it's normal, it only replies when the sequence completes
- If the loop/sequence fails: click **+ New Session** and retry
- `output_key` is how parallel agents save results for the gather agent
- *(add your own here)*

## 🚀 Beyond the Lab
- Add a `marketing_agent` (tagline writer) to `preproduction_team`
- Give `researcher` a Google Search API tool
- Explore `CustomAgent` for conditional workflows (run an agent only if a state key exists)
- Map the patterns to your BPM background: Sequential = process orchestration, Loop = human-in-the-loop reviews, Parallel = fan-out task distribution (Camunda speak!)
- *(add your own here)*

## 🎬 Video
[▶️ Watch Day 7](youtube-link)

---
*Built by [Abdul Qaadir](https://linktr.ee/bpmforbusiness) — 30 Labs, 30 Days on Google Cloud.*