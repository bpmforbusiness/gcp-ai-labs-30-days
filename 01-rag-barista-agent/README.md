# Day 1: RAG AI Barista Agent — Streamlit + Google ADK + Cloud Run

**Series:** 30 Labs, 30 Days · **Topic:** GCP AI · **Product:** ADK, Cloud Run, Gemini 3.5 Flash
**Codelab:** [Deploy a RAG AI Agent in Streamlit using Google ADK and Cloud Run](https://codelabs.developers.google.com/codelabs/cloud-run/build-streamlit-rag-agent-google-adk-cloud-run)
**Written by:** Smitha Kolan, Balaji Subramaniam, Tianzi Cai · **Updated:** Aug 12, 2026
**Date:** 2026-08-16 · **Status:** 🚧 In Progress

## 🧠 The AI Concept: RAG (Retrieval-Augmented Generation)

A coffee shop AI Barista that recommends menu items — without hallucinating drinks that don't exist.

**RAG = Retrieve → Augment → Generate:**
1. **Retrieve:** the agent loads real menu data (`menu.json`) via a custom tool
2. **Augment:** the retrieved data is fed into the LLM as context alongside the user's question
3. **Generate:** Gemini 3.5 Flash answers grounded ONLY in that data

The agent can't invent a "Unicorn Latte" because it's not in the menu — the tool grounds every answer in reality. This is the core enterprise pattern for preventing AI hallucination.

## 🛠️ The Build (GCP Walkthrough)

### What you'll build
- `menu.json` — mock menu data source (8 items: coffee, pastries, allergens, tags, prices)
- `agent.py` — ADK `LlmAgent` with a `get_menu()` Python tool
- `app.py` — Streamlit chat UI managing conversation history
- Deployed to **Cloud Run** via source-based deployment

### Setup
```bash
# 1. Create a GCP project + enable billing
# 2. Cloud Shell
gcloud auth list
gcloud config get project
gcloud config set project <YOUR_PROJECT_ID>

# 3. Enable APIs
gcloud services enable \
  run.googleapis.com \
  aiplatform.googleapis.com \
  cloudbuild.googleapis.com

# 4. Project vars + region
export PROJECT_ID=$(gcloud config get-value project)
export REGION=[insert-region-here]   # use closest region

# 5. Working dir
mkdir coffee-barista-agent && cd coffee-barista-agent
```

### Step 1 — Create the mock menu data source
`menu.json` with 8 items — name, description, price, tags, allergens. The agent reads this at runtime via a custom tool so it can't hallucinate non-existent items.

### Step 2 — Build the ADK agent
```text
# requirements.txt
google-adk==2.2.0
streamlit==1.56.0
```

`agent.py` — define `get_menu()` tool, pass it to an `LlmAgent` (Gemini 3.5 Flash).

### Step 3 — Streamlit UI
Wrap the agent in a chat app with conversation history management.

### Step 4 — Deploy to Cloud Run
Source-based deployment → the app gets a public HTTPS URL.

### Step 5 — Test RAG behavior
Ask about allergens ("does the pumpkin latte have dairy?") → the agent answers from the grounded menu data.

### Optional — Firestore Vector Search
Ground the agent in Firestore instead of local JSON:
1. Enable Firestore API + initialize database
2. Seed Firestore with menu data
3. Create Firestore Vector Index
4. Grant Firestore access to the service account
5. Update code + redeploy + verify

## 💰 Cost & Free Tier

**Estimated cost: < $1.00 USD** (codelab estimate). Cloud Run + Gemini Flash are both free-tier friendly for a small demo. Firestore has a generous free tier (1 GiB storage, 50K reads/day).

## 💬 Key Discussions from the Lab (the "why")

- **Local JSON vs. Live Databases:** JSON = fast for prototypes. Production = Cloud Firestore / AlloyDB / Cloud SQL so managers can update items/prices/allergens without rebuilding the container.
- **Model Tradeoffs & Retrieval Token Efficiency:** choose the right model size for the task; RAG keeps token usage grounded and efficient.
- **Memory State & Production Stores:** conversation history needs a real store at scale.
- **Deploying Containers vs. Source, and IAM Security:** source-based deploy is fastest for demos; containers give control; always least-privilege IAM.

## 📚 What I Learned
- *(to be filled after performing the lab)*

## ⚠️ Gotchas / Failures
- *(to be filled — this is the gold for hiring managers)*

## 🚀 Beyond the Lab
- *(to be filled: auth, monitoring, scaling ideas)*

## 🎬 Video
[▶️ Watch Day 1](youtube-link)

---
*Built by [Abdul Qaadir](https://linktr.ee/bpmforbusiness) — 30 Labs, 30 Days on Google Cloud.*
