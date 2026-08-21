# Day 5: Google Trends Analyst Agent with BigQuery MCP

**Series:** 30 Labs, 30 Days · **Topic:** GCP AI · **Product:** ADK, BigQuery MCP, Cloud Run
**Codelab:** [Build a Google Trends Analyst Agent with BigQuery MCP](https://codelabs.developers.google.com/codelabs/cloud-run/build-google-trends-analyst-agent-with-bigquery-mcp)
**Date:** 2026-08-21 · **Status:** 🚧 In Progress

> 📘 **FOLLOW ALONG: [`LAB_MANUAL.md`](LAB_MANUAL.md)** — the complete step-by-step implementation manual (ADK setup, BigQuery MCP enablement, agent code, local run, Cloud Run deploy). Use it while doing this lab — every command is copy-paste ready.

## 🧠 The AI Concept: An Agent That Queries Live Data via MCP

**In Day 2 you built an MCP server; in Day 5 you flip it — your agent now USES a managed MCP server** to query Google Trends' real public dataset. The BigQuery MCP server exposes SQL tools the agent can call dynamically (task discovery: the agent figures out which tables/fields it needs on its own).

**The magic:** the agent is grounded in **live, real-world data** (what's trending right now across regions/countries), not stale training data. This is the pattern for data-analyst agents: an LLM with tools pointing at your analytics warehouse — "answer my question with a SQL query against BigQuery."

**Why it matters:** this is enterprise AI in its purest form — natural language in, real data out, with the agent doing the schema discovery and query-writing. You'll see the agent handle the trickier parts (billing-project mapping, schema discovery via `SELECT * LIMIT 0` instead of erroring permission-checks).

## 🛠️ The Build (Step-by-step)

### What you'll build
- A Google Trends analyst agent (ADK `LlmAgent`) wired to **BigQuery MCP** managed server
- It dynamically discovers + calls tools to query `bigquery-public-data.google_trends`
- Tested locally (ADK Web), then deployed to **Cloud Run**

### Key steps
1. **Setup:** create project, set `GOOGLE_CLOUD_PROJECT` + `GOOGLE_GENAI_USE_VERTEXAI=1`, authenticate (gcloud auth + application-default), enable APIs (run, cloudbuild, artifactregistry, bigquery, aiplatform)
2. **Enable MCP for BigQuery:** `gcloud beta services mcp enable bigquery.googleapis.com`
3. **Write the agent** (`google_trends/agent.py`):
   - `LlmAgent(model="gemini-3-flash-preview")` with tools `[get_todays_date, bq_tools]`
   - `McpToolset` pointing at the BigQuery MCP streamable HTTP endpoint, with OAuth2 bearer auth headers via `google.auth`
   - Instruction prompt: billing-project mapping, **schema discovery via `SELECT * FROM table LIMIT 0`**, dataset constraint, Markdown output
4. **Run locally:** venv → `pip install google-auth google-adk[mcp]` → `adk web` (port 8000) → ask: top USA trends, rising France trends, top 3 California trends last week, etc.
5. **Deploy to Cloud Run:**
   - Grant the compute SA: `roles/aiplatform.user`, `roles/mcp.toolUser`, `roles/bigquery.jobUser`, `roles/bigquery.dataViewer`
   - `Dockerfile` (python:3.11-slim, non-root user, ADK web on 8080)
   - `gcloud run deploy google-trends-agent --source . --region us-west1 ...` → Service URL UI
   - Verify with `gcloud logging read`

## 💰 Cost & Free Tier

~15-20 min, "less than $5" per the codelab. BigQuery public dataset queries are cheap; ADK Web local is free; Cloud Run nearly free at low traffic.

## 📚 What I Learned
- *(to be filled after performing the lab)*

## ⚠️ Gotchas / Failures
- **BigQuery MCP must be explicitly enabled** (`gcloud beta services mcp enable bigquery.googleapis.com`) or the agent has no SQL tools
- **CRITICAL:** don't call `get_table_info`/`list_table_ids` in this dataset — they trigger permission errors. The agent instruction forces `SELECT * FROM table LIMIT 0` for schema discovery (this is a real codelab trap)
- Must set **billing project** when executing SQL (mapped via instruction prompt)
- `GOOGLE_GENAI_USE_VERTEXAI=1` routes to Vertex (IAM auth) instead of needing a Gemini API key
- Cloud Run SA needs 4 roles (aiplatform, mcp.toolUser, bigquery.jobUser, bigquery.dataViewer)
- Cloud Shell → `adk web --allow_origins="*"`
- *(add your own here)*

## 🚀 Beyond the Lab
- Swap Google Trends for **your own BigQuery analytics** (internal data → analyst agent)
- Add monitoring/alerting: agent watches a trend topic and posts when it spikes
- Schedule trend reports to Telegram/WhatsApp (your pipeline!)
- *(add your own here)*

## 🎬 Video
[▶️ Watch Day 5](youtube-link)

---
*Built by [Abdul Qaadir](https://linktr.ee/bpmforbusiness) — 30 Labs, 30 Days on Google Cloud.*