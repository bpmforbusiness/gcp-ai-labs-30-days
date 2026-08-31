# Day 8: Getting Started with A2A Protocol

**Series:** 30 Labs, 30 Days · **Topic:** GCP AI · **Product:** A2A Protocol, ADK, Cloud Run, Agent Engine
**Codelab:** [Getting Started with Agent2Agent (A2A) Protocol: A Purchasing Concierge](https://codelabs.developers.google.com/intro-a2a-purchasing-concierge)
**Date:** 2026-08-29 · **Status:** 🚧 In Progress

> 📘 **FOLLOW ALONG: [`LAB_MANUAL.md`](LAB_MANUAL.md)** — the complete step-by-step implementation manual (A2A server/client structure, Agent Cards, Cloud Run + Agent Engine deploy, full source explanations). Use it while doing this lab — every command and code block is copy-paste ready.

> 🔗 **Starter repo:** `git clone https://github.com/alphinside/purchasing-concierge-intro-a2a-codelab-starter.git purchasing-concierge-a2a`

## 🧠 The AI Concept: Agents Talking to Agents (A2A)

**Day 7 built a TEAM of agents inside one framework (ADK). Today: agents from DIFFERENT frameworks talk to each other — over the network.**

The **Agent2Agent (A2A) protocol** complements MCP:
- **MCP** (Days 2 & 5) = connect agents to *tools and data*.
- **A2A** = let *agents collaborate as agents* — multi-turn, back-and-forth dialogue, like a real conversation.

Per the official spec: **use MCP for tools, A2A for agents.** Agents advertise their capabilities via an **Agent Card** (a digital "business card" at `/.well-known/agent.json`), and communicate over **JSON-RPC**.

**The killer demo in this lab:** a **Purchasing Concierge** (ADK, deployed on Agent Engine) that orders food from a **Burger Agent** (CrewAI) and a **Pizza Agent** (LangGraph) — both deployed as A2A servers on Cloud Run. **Three completely different frameworks, zero shared code, fully interoperable.** The burger agent even asks for confirmation mid-order (human-in-the-loop), and A2A handles it like a natural conversation.

## 🛠️ The Build (Step-by-step)

### What you'll deploy
1. 🍔 **Burger Agent** (CrewAI) → A2A server on **Cloud Run**
2. 🍕 **Pizza Agent** (LangGraph) → A2A server on **Cloud Run**
3. 🛒 **Purchasing Concierge** (ADK) → A2A client on **Vertex AI Agent Engine**

### Key steps
1. **Setup:** Cloud Shell → `gcloud config set project` → clone starter repo → `uv sync --frozen` → enable `aiplatform / run / cloudbuild / cloudresourcemanager` APIs
2. **Burger agent:** `gcloud run deploy burger-agent --source remote_seller_agents/burger_agent ...` → add `HOST_OVERRIDE` (the Cloud Run URL) so the Agent Card's `url` is reachable → verify at `/.well-known/agent.json`
3. **Pizza agent:** same deployment + `HOST_OVERRIDE`
4. **Concierge:** `gcloud storage buckets create gs://purchasing-concierge-{project}` → fill `.env` (seller URLs, staging bucket) → `uv run deploy_to_agent_engine.py` → capture the Agent Engine resource name → update `.env` → `bash test_agent_engine.sh`
5. **Test UI:** `uv run purchasing_concierge_ui.py` → chat: "Show me burger and pizza menu" / "I want to order 1 bbq chicken pizza and 1 spicy cajun burger"

### Core concepts implemented
- **Agent Card** — `AgentCard`, `AgentCapabilities`, `AgentSkill`, I/O modes, URL (served at `/.well-known/agent.json`)
- **Task & Agent Executor** — `AgentExecutor`, `DefaultRequestHandler`, `InMemoryTaskStore`, `A2AStarletteApplication`
- **Agent Engine deploy** — ADK agent deployed without a Dockerfile via `vertexai.agent_engines`
- **JSON-RPC** — the message/task interchange (`message/send`)

## 💰 Cost & Free Tier

Cloud Run + Agent Engine + Vertex AI usage. Keep it cheap by **deleting the services/project right after** the test (see Lab Manual §9). New users get the $300 free trial.

## 📚 What I Learned
- *(to be filled after performing the lab)*

## ⚠️ Gotchas / Failures
- The Agent Card's `url` defaults to `http://0.0.0.0:8080/` — **you MUST add the `HOST_OVERRIDE` env var** (the real Cloud Run URL) or external clients can't reach the server
- Need **billing** enabled (trial billing account) before Agent Engine deploys
- `gcloud run deploy` will prompt **Y** to create a container repository for source-based deploys
- `uv sync --frozen` expects the exact locked deps — don't add packages here
- Agent Engine deploy needs `aiplatform.googleapis.com` enabled
- Concierge `.env` must point to the real seller Cloud Run URLs, else the client can't discover them
- *(add your own here)*

## 🚀 Beyond the Lab
- Add a **third seller agent** (e.g., a Coffee agent using the Day-1 barista pattern!) and wire it into the concierge
- Try the **streaming** A2A capability (agent card declares `streaming: true`)
- Explore A2A **push notifications** / task progress in a long-running task
- Map to your BPM brain: A2A = cross-organization agent interoperability (like a service mesh for agents) — think federated multi-agent workflow across vendors
- *(add your own here)*

## 🎬 Video
[▶️ Watch Day 8](youtube-link)

---
*Built by [Abdul Qaadir](https://linktr.ee/bpmforbusiness) — 30 Labs, 30 Days on Google Cloud.*