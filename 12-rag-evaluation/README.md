# Day 12: Evaluate RAG Systems with Vertex AI

**Series:** 30 Labs, 30 Days · **Topic:** GCP AI · **Product:** Vertex AI Gen AI Evaluation Service, EvalTask, SQuAD 2.0
**Codelab:** [Evaluate RAG Systems with Vertex AI](https://codelabs.developers.google.com/codelabs/production-ready-ai-with-gc/6-ai-evaluation/evaluate-rag-systems-with-vertex-ai)
**Date:** 2026-09-18 · **Status:** 🚧 Draft (awaiting recording)

> 📘 **FOLLOW ALONG: [`LAB_MANUAL.md`](LAB_MANUAL.md)** — the complete step-by-step implementation manual (dataset prep, reference-free + referenced evaluation, custom metrics, visualization, production playbook). Every command is copy-paste ready.

## 📏 The AI Concept: PROVING YOUR RAG SYSTEM IS ACTUALLY GOOD

**Days 1–11 built RAG systems and agents. Today: how do you KNOW they're good?**

A demo that "looks smart" is not a deployable system. Production AI needs **evaluation** — and RAG has a unique problem: it's **three systems stacked** (retriever, context-utilizer, generator), any of which can fail silently. The model might retrieve the right context and ignore it, or write a polished answer built on garbage context.

This lab gives you the **measurement layer**: the Vertex AI Gen AI Evaluation Service, with **EvalTask**, predefined + custom metrics, and visualizations that tell you *not just WHO won, but WHY*.

## 🛠️ What you build
- **Evaluation datasets** from SQuAD 2.0 (neuroscience / history / geography questions + retrieved contexts)
- **Reference-free eval** — LLM-judged metrics: groundedness, relevance, helpfulness, safety, instruction-following
- **Custom metrics** — your own scoring rubrics (5→1 pointwise) wrapped in PointwiseMetric
- **Referenced eval** — compare against golden answers: custom 1/0 correctness + `exact_match`, `bleu` (precision), `rouge` (recall)
- **Radar + bar plots** comparing "good" Model A vs "bad" Model B — evaluation that PROVES the difference

## 🧩 Series arc
- **Day 1:** built a RAG barista agent
- **Days 9–10:** vector embeddings + agent memory (RAG infrastructure)
- **Day 11:** secured MCP server (safe deployment)
- **Day 12 (today):** *the quality gate* — prove RAG output is grounded, relevant, and correct before anyone trusts it in production

## 🔑 Key takeaways
- **Prompt = question + retrieved context** — the evaluator must see exactly what the model saw, or groundedness is meaningless.
- **Groundedness is THE RAG metric** — it consistently separates high-quality from low-quality systems.
- **Model-based vs computation-based metrics are complementary** — LLM-judged metrics catch "semantically right, differently worded" (exact_match can't); math metrics (BLEU/ROUGE) are objective and fast.
- **Custom rubrics catch domain nuances** generic metrics miss.
- **Production playbook:** CI/CD eval gates · versioned golden datasets · retriever eval (Hit Rate/MRR) · Cloud Monitoring dashboards + alerts.

## 🎬 Video
Publication link to be added when the tutorial is recorded and uploaded.

## 🧹 Cleanup
Workbench instance: stop/delete `evaluation-workbench` after the lab (cheapest is to STOP it when idle). Less than $1 total usage for the lab itself.