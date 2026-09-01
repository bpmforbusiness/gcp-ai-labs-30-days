# Day 9: Getting Started with Vector Embeddings with AlloyDB AI

**Series:** 30 Labs, 30 Days · **Topic:** GCP AI · **Product:** AlloyDB, Vertex AI (Gemini embeddings)
**Codelab:** [Getting started with Vector Embeddings with AlloyDB AI](https://codelabs.developers.google.com/alloydb-ai-embedding)
**Date:** 2026-08-31 · **Status:** 🚧 In Progress

> 🎬 **Thumbnail:** `screenshots/day9_thumbnail.png` (1280×720, placed for broadcast when video goes live)

> 📘 **FOLLOW ALONG: [`LAB_MANUAL.md`](LAB_MANUAL.md)** — the complete step-by-step implementation manual (AlloyDB cluster deploy, GCE VM + psql, embeddings, similarity search, LLM enrichment, ScaNN index). Use it while doing this lab — every command is copy-paste ready.

## 🧠 The AI Concept: Embeddings + Vector Search = RAG Memory

**Till now we built agents that *reason*.** Today we give them **memory and retrieval** — by turning words into **vectors** (numbers that capture *meaning*) and searching them by **semantic similarity**, not keywords.

This is the retrieval side of RAG (connects back to Day 1's coffee barista). The core ideas:
- **Embeddings** — a `text-embedding-005` model converts each product description into a 768-dimensional vector that encodes meaning.
- **Vector search** — `embedding <=> embedding('text-embedding-005', 'query')` finds rows whose vectors are *close* (cosine distance), so "what kind of fruit trees grow well here?" surfaces **Cherry Tree, Meyer Lemon, Toyon** — semantically relevant, not keyword-matched.
- **LLM enrichment** — feed the top vector results (as JSON) to a Gemini model *inside the same SQL* and get a natural, friendly answer. **Full RAG in one query.**
- **Indexing at scale** — a **ScaNN** approximate-nearest-neighbor index keeps search fast on millions of vectors.

**Why it matters:** this is how real agentic apps do grounded, fact-based answers over business data — exactly what enterprise RAG needs (and your BPM brain sees it as "processes retrieving the right knowledge, semantically").

## 🛠️ The Build (Step-by-step)

### What you'll deploy
- **AlloyDB** cluster + primary instance (PostgreSQL + vectors)
- **GCE VM** with a `psql` client (AlloyDB is private-only)
- **AlloyDB Studio** (web SQL interface) + **Vertex AI** integration

### Key steps
1. **Setup:** enable APIs (alloydb, compute, cloudresourcemanager, servicenetworking, aiplatform)
2. **Deploy AlloyDB:** create `psa-range` private IP + VPC peering → create cluster (`--subscription-type=TRIAL` if first) → create primary instance
3. **Connect:** deploy GCE `instance-1` → install `postgresql-client` → `psql` to the instance
4. **Prepare DB:** grant `roles/aiplatform.user` to the AlloyDB service agent → `CREATE DATABASE quickstart_db` → enable `google_ml_integration` + `vector` extensions → import Cymbal data (products/inventory/stores)
5. **Embeddings:** verify speed flag → `ALTER TABLE ... ADD COLUMN embedding vector(768)` → `CALL ai.initialize_embeddings(model_id=>'text-embedding-005', ...)`
6. **Similarity search:** the `<=>` cosine-distance query over store 1583 ("fruit trees") → Cherry Tree wins
7. **LLM enrichment:** JSON output → Gemini Enterprise Agent Platform Studio prompt → OR register `gemini-3.6-flash` + run the full RAG query with `google_ml.predict_row`
8. **Vector index:** `CREATE EXTENSION alloydb_scann` → ScaNN index → verify with `EXPLAIN (analyze)`

## 💰 Cost & Free Tier

**Less than $3 USD** for the lab. New users get the $300 Free Trial. Delete cluster/backups/VM after (see Lab Manual §11).

## 📚 What I Learned
- *(to be filled after performing the lab)*

## ⚠️ Gotchas / Failures
- **AlloyDB is private-only** — you MUST go through a GCE VM (or AlloyDB Studio) with `psql`; you can't connect from your laptop directly
- **Enable `google_ml_integration` (CASCADE)** — powers both embeddings (`ai.initialize_embeddings`) AND LLM calls (`google_ml.predict_row`)
- **Grant `roles/aiplatform.user`** to the AlloyDB service agent BEFORE embedding, or you get permissions errors
- **`enable_faster_embedding_generation` flag must be `on`** — enable via `gcloud beta alloydb instances update ... --update-mode=FORCE_APPLY`, wait, re-verify
- The trial cluster uses `--cpu-count=8`, a standard cluster `--cpu-count=2` (and no `--subscription-type`)
- `openssl rand -hex 16` password — **save it** (you need it to connect multiple times)
- Free trial cluster is only available if you've **never used AlloyDB** in the project
- *(add your own here)*

## 🚀 Beyond the Lab
- Wire this vector store into an ADK agent → a **production RAG agent** (retrieval + generation together)
- Try **incremental_refresh_mode => 'transactional'** so new/changed products auto-embed
- Experiment with ScaNN tuning params (`num_leaves`, `max_num_levels`) for larger datasets
- Enrich with **hybrid search** (keyword + vector) for even better retrieval
- Map to your BPM brain: this is the "knowledge + case data retrieval layer" agentic workflows query at decision points
- *(add your own here)*

## 🎬 Video
[▶️ Watch Day 9](youtube-link)

---
*Built by [Abdul Qaadir](https://linktr.ee/bpmforbusiness) — 30 Labs, 30 Days on Google Cloud.*