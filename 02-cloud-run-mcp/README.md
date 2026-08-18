# Day 2: Secure MCP Server on Cloud Run

**Series:** 30 Labs, 30 Days · **Topic:** GCP AI · **Product:** Cloud Run, MCP (Model Context Protocol)
**Codelab:** [How to deploy a secure MCP server on Cloud Run](https://codelabs.developers.google.com/codelabs/cloud-run/how-to-deploy-a-secure-mcp-server-on-cloud-run)
**Date:** 2026-08-18 · **Status:** 🚧 In Progress

> 📘 **FOLLOW ALONG: [`LAB_MANUAL.md`](LAB_MANUAL.md)** — the complete step-by-step implementation manual (FastMCP zoo server, Dockerfile, Cloud Run deploy, Antigravity CLI connection, debugging). Use it while doing this lab — every command is copy-paste ready.

## 🧠 The AI Concept: MCP (Model Context Protocol)

MCP is the "USB-C for AI" — a standard way for LLMs to connect to external tools and data. Instead of every AI app building its own integration for every service, MCP defines one protocol: a server exposes **tools** (things the model can call), **resources** (content handed to it), and **prompts** (reusable instruction shorthands).

**Why it matters:** Anthropic created MCP in late 2024, and it became the industry standard for agent tool access. Google, OpenAI, and every major platform now support it. This lab deploys an MCP server as a **secure, authenticated production service** — the pattern you'd use to give your agents access to real business systems.

## 🛠️ The Build (GCP Walkthrough)

### What you'll build
- **Zoo MCP server** with FastMCP: `get_animals_by_species` + `get_animal_details` tools (data in memory)
- **Dockerfile** using `uv` to run the server
- Deployed to **Cloud Run with `--no-allow-unauthenticated`** (auth required!)
- Connected from **Antigravity CLI** with an identity token

### Key steps
1. Enable APIs: `run.googleapis.com`, `artifactregistry.googleapis.com`, `cloudbuild.googleapis.com`
2. `uv init` the Python project + `uv add fastmcp==2.12.4`
3. Write `server.py` — the FastMCP zoo server (34 animals, 8 species)
4. Write the `Dockerfile` (python:3.13-slim + uv)
5. Create `mcp-server-sa` service account + deploy:
   ```bash
   gcloud run deploy zoo-mcp-server \
     --service-account=mcp-server-sa@$GOOGLE_CLOUD_PROJECT.iam.gserviceaccount.com \
     --no-allow-unauthenticated \
     --region=us-west1 \
     --source=. \
     --labels=dev-tutorial=codelab-mcp
   ```
6. Grant yourself `roles/run.invoker` + write the Antigravity CLI `mcp_config.json` with your ID token
7. Test: `/mcp` → ask "Where can I find penguins?" → the CLI calls the remote tool

### Optional extras
- **Verify logs:** `gcloud run services logs read zoo-mcp-server` — see the tool call
- **MCP prompt:** add a `/find <animal>` slash command via `@mcp.prompt()`
- **Speed:** `agy --model=gemini-3.6-flash --effort=low` for faster responses

## 💰 Cost & Free Tier

This lab is marked **"Learning by doing - NO COST"** — Google provides free GCP credits to complete it. Cloud Run doesn't charge when idle; only Artifact Registry storage might incur a small cost.

## 📚 What I Learned
- *(to be filled after performing the lab)*

## ⚠️ Gotchas / Failures
- **ID token expiry** — the #1 failure: if you see "requires authentication but no OAuth configuration found," the ID_TOKEN expired. Re-run `gcloud auth print-identity-token` + rewrite mcp_config.json
- Visiting the URL directly → "Error Forbidden" is CORRECT (auth required)
- Artifact Registry repo creation prompt (Y/n) on first deploy
- *(add your own here)*

## 🚀 Beyond the Lab
- Connect the MCP server to an **ADK agent** (next lab in the series!)
- Swap in-memory data for a real database (Cloud SQL, Firestore, AlloyDB)
- Add more tools: business systems, internal APIs, CRMs
- *(add your own here)*

## 🎬 Video
[▶️ Watch Day 2](youtube-link)

---
*Built by [Abdul Qaadir](https://linktr.ee/bpmforbusiness) — 30 Labs, 30 Days on Google Cloud.*
