# Day 10: Visualize Your AI Assistant Memory (Gemini + Cloud SQL pgvector)

**Series:** 30 Labs, 30 Days · **Topic:** GCP AI · **Product:** Cloud SQL, Gemini, pgvector
**Codelab:** [Visualize your AI assistant memory with Gemini and Cloud SQL pgvector](https://codelabs.developers.google.com/next26/postgres-visual-memory-agent)
**Date:** 2026-09-01 · **Status:** 🚧 In Progress

> 🎬 **Thumbnail:** `screenshots/day10_thumbnail.png` (1280×720, staged for broadcast when video goes live)

> 📘 **FOLLOW ALONG: [`LAB_MANUAL.md`](LAB_MANUAL.md)** — the complete step-by-step implementation manual (Cloud SQL setup, pgvector schema, semantic retrieval, memory extraction, run + visualize). Use it while doing this lab — every command is copy-paste ready.

> 🔗 **Starter repo:** `git clone https://github.com/GoogleCloudPlatform/devrel-demos.git` → `cd devrel-demos/codelabs/visual-memory-postgres-demo`

## 🧠 The AI Concept: AGENTS THAT REMEMBER

**Day 9 taught AI to retrieve from a vector DB. Today we give an agent a *living memory* of ITS OWN users.**

The **Living Memory Demo** does two things agents need but often lack:
1. **Extracts memories** — every user message passes through `gemini-2.5-flash`, which pulls out structured **FACTS / PREFerences / IMPLICIT traits** (e.g. "user likes hiking") as JSON, embeds each with `gemini-embedding-001`, and stores them in Cloud SQL.
2. **Uses them via RAG** — before answering, the app embeds the current question and runs `ORDER BY embedding <=> $2::vector LIMIT 5` to pull the *most semantically relevant* past memories. Personalized answers, without loading all history.

**The kicker — full visualization:** an "AI Cortex Data Visualizer" renders memories as **color-coded nodes in a vector space**. You literally *watch* the AI build a persona in ~30 seconds: facts, preferences, implicit traits appearing as you talk.

**Why it matters:** this is the "memory layer" of real assistant apps — and Day 10 directly extends Day 9: I showed vector retrieval in AlloyDB; today's the same idea in Cloud SQL, PLUS live extraction + visualization. Agents now have persistent, personalized memory.

## 🛠️ The Build (Step-by-step)

### What you'll deploy
- **Cloud SQL for PostgreSQL** instance (`POSTGRES_16`) with **pgvector**
- A **Living Memory** Node.js chat app with the memory visualizer
- **Cloud SQL Auth Proxy** (secure local connection)

### Key steps
1. **Setup:** enable `sqladmin` + `aiplatform` APIs → clone `devrel-demos` → `npm install`
2. **Cloud SQL:** set env vars → create instance (`living-memory-db`, POSTGRES_16, 1 cpu) → create DB (`living_memory`) → app user (`memory_app`) → start **Cloud SQL Auth Proxy** → apply `schema.sql` (enables `vector` extension + creates users/conversations/messages/memories tables + **HNSW index** on `memories.embedding`)
3. **Semantic retrieval:** examine `/api/chat` — embed question → `ORDER BY embedding <=> $2::vector LIMIT 5`
4. **Memory extraction:** `extractMemoriesAsync` — `gemini-2.5-flash` → JSON memories → embedded + inserted
5. **Run:** `npm run seed` → `node server.js` → Web Preview on port **3000** → chat + watch the visualizer build edges
6. **Clean up:** delete instance + `rm -rf ~/devrel-demos`

## 💰 Cost & Free Tier

**Less than $5 USD** (~60 min). Delete the Cloud SQL instance after to stop billing.

## 📚 What I Learned
- *(to be filled after performing the lab)*

## ⚠️ Gotchas / Failures
- Cloud SQL instance creation takes **5-10 minutes** — don't assume it's stuck
- The **Auth Proxy must be running** before `psql` can reach the instance; watch for "proxy has started successfully"
- `psql < schema.sql` enables the `vector` extension — Cloud SQL needs POSTGRES + enable `cloud_sql` configuration (the demo handles it)
- The `gemini-embedding-001` model must be accessible (Vertex AI enabled); uses `outputDimensionality: 768`
- Memory extraction uses `gemini-2.5-flash` and is **non-deterministic** — JSON parse failures are caught silently (the `try/catch`)
- Web Preview port is **3000**, not the default — change port in Cloud Shell preview
- *(add your own here)*

## 🚀 Beyond the Lab
- Customize the `extractionPrompt` to extract domain-specific data (e.g., customer preferences for a BPM use case)
- Wire this memory layer into an ADK agent → agents with cross-session memory
- Add message-recency weighting to the similarity query (memory decay)
- Use the `category` field to segment retrieval (Travel vs Hobby vs Persona)
- Map to your BPM brain: memory = "case data + customer context" that agents carry across a workflow lifecycle
- *(add your own here)*

## 🎬 Video
[▶️ Watch Day 10](youtube-link)

---
*Built by [Abdul Qaadir](https://linktr.ee/bpmforbusiness) — 30 Labs, 30 Days on Google Cloud.*