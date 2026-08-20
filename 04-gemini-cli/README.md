# Day 4: Hands-on Lab — Gemini CLI

**Series:** 30 Labs, 30 Days · **Topic:** GCP AI · **Product:** Gemini CLI
**Codelab:** [Hands-on Lab: Gemini CLI](https://codelabs.developers.google.com/codelabs/cloud-run/gemini-cli)
**Date:** 2026-08-20 · **Status:** ✅ Complete

> 🎬 **Watch the video:** [Day 4 — Gemini CLI: Your AI Partner in the Terminal](https://youtu.be/aeAcWM2yOhE)

> 📘 **FOLLOW ALONG: [`LAB_MANUAL.md`](LAB_MANUAL.md)** — the complete step-by-step implementation manual (install, 3 auth methods, prompts, tools, Tic-Tac-Toe build, extensions). Use it while doing this lab — every command is copy-paste ready.

## 🧠 The AI Concept: The AI Coding Copilot, Right in Your Terminal

**Gemini CLI is Google's AI pair-programmer built into the terminal.** It's the direct competitor to Claude Code — same idea: you chat with an AI that can read your files, run commands, use tools (web search, web fetch), and write/refactor code across your whole project. Powered by Gemini models, it turns natural language into working software.

**Why it matters:** This is the workflow of 2026 — developers don't just *write* code; they *direct* AI to build, iterate, and debug it. After Day 3 (vibe-coding in AI Studio's UI), today shows the **terminal-native** version — the same capability, scriptable and automatable, which is where serious engineering happens.

## 🛠️ The Build (Step-by-step)

### What you'll do
- Install + authenticate **Gemini CLI** (3 methods: Google login, API key, Vertex AI)
- Run basic prompts (weather, web fetch, multi-step news summarization)
- Use **system commands** via `!` mode
- **Generate a Tic-Tac-Toe game** (human vs computer, separated HTML/CSS/JS)
- Test it with a local Python server
- Install the **Nanobanana extension** for AI image generation

### Key steps
1. **Setup:** Cloud Shell → set project → enable `aiplatform` + `cloudresourcemanager` APIs
2. **Install:** `npm install -g @google/gemini-cli` (or use preinstalled Cloud Shell)
3. **Authenticate:** `/auth` → Login with Google, or `GEMINI_API_KEY`, or Vertex AI env vars
4. **Try prompts:**
   - `> What is the weather today in Tokyo` (auto-uses GoogleSearch tool)
   - `/tools` — confirm installed tools
   - WebFetch + multi-step: *"Get news from mainichi.jp, filter sports, summarize"*
   - `!` mode for system commands (`ls`, `pwd`)
5. **Build Tic-Tac-Toe:** one prompt → generates `index.html`, `style.css`, `script.js` (AI handles game state, computer AI, win detection, reset)
6. **Test:** `python3 -m http.server 8080` → open localhost:8080
7. **Extensions:** `gemini extensions install https://github.com/gemini-cli-extensions/nanobanana` → `/generate`, `/edit`, `/icon`, `/diagram`, etc. (needs `NANOBANANA_GEMINI_API_KEY`)

### Challenge
What prompts could build: your favorite game · a photo gallery · a Manga generator app?

## 💰 Cost & Free Tier

Gemini CLI in Cloud Shell is free (preinstalled + authenticated). API-key auth uses your AI Studio free tier. Prebuilt in Cloud Shell = zero install cost.

## 📚 What I Learned
- *(to be filled after performing the lab)*

## ⚠️ Gotchas / Failures
- **Node.js 20+ required** for local install
- Auth menu is via `/auth` inside Gemini (exit with `/quit` first if needed)
- `GOOGLE_CLOUD_PROJECT` must be set for Google-login auth (or in `.env`)
- Nanobanana extension needs `NANOBANANA_GEMINI_API_KEY` exported before use
- *(add your own here)*

## 🚀 Beyond the Lab
- Compare Gemini CLI vs Claude Code (you run both)
- Automate a build: use Gemini CLI in a CI/CD pipeline
- Generate the **30 Labs series thumbnail art** with `/generate`
- *(add your own here)*

## 🎬 Video
[▶️ Watch Day 4](youtube-link)

---
*Built by [Abdul Qaadir](https://linktr.ee/bpmforbusiness) — 30 Labs, 30 Days on Google Cloud.*
