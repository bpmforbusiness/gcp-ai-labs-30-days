# 🎬 DAY 1 VIDEO SCRIPT — "I Built an AI Coffee Barista with RAG on Google Cloud"
**Channel:** @TechWorldWithAbdul · **Series:** 30 Labs, 30 Days · **Target length:** 12-18 min

---

## 🎥 VIDEO STRUCTURE (with timestamps)

| Time | Section |
|---|---|
| 0:00 | Hook (30 sec) |
| 0:30 | What we're building today (60 sec) |
| 1:30 | THE CONCEPT: RAG explained simply (3 min) |
| 4:30 | The architecture (60 sec) |
| 5:30 | THE LAB: GCP setup |
| 7:00 | THE LAB: menu.json + agent.py |
| 10:00 | THE LAB: Streamlit app.py |
| 12:00 | THE LAB: Deploy to Cloud Run |
| 13:30 | THE TEST: RAG in action (the fun part) |
| 15:30 | Key lessons + gotchas |
| 16:30 | CTA + Day 2 tease |

---

## 🎬 SCRIPT

### [0:00] HOOK
*(Screen: title card "DAY 1/30 — RAG AGENT" over footage of the deployed chatbot answering)*

"Your AI chatbot just recommended a drink that doesn't exist. ☕ That's hallucination — and today, I'm going to show you how to stop it. I'm building 30 AI labs on Google Cloud in 30 days, and this is Day 1: a coffee barista AI that can ONLY recommend what's actually on the menu."

*(Cut to you, speaking to camera)*

"Welcome to 30 Labs, 30 Days — I'm Abdul. Every day for the next month I'm performing a Google Codelab, building something real, and showing you the failures too. No gatekeeping. Day 1 is the hottest concept in enterprise AI right now: RAG."

### [0:30] WHAT WE'RE BUILDING
*(Screen: app screenshot / architecture image)*

"Here's the goal: an AI barista for a coffee shop. You type 'recommend something strong and warm' — it says espresso. You ask 'do you have a matcha frappuccino?' — it says no, politely, because it doesn't exist on the menu. That's RAG: Retrieval-Augmented Generation. The agent retrieves real data, then generates an answer grounded in that data."

"We're building it with three Google Cloud pieces:
- ADK — Google's open-source Agent Development Kit
- Gemini 3.5 Flash — the brain
- Cloud Run — serverless deployment

And the whole thing costs less than a dollar."

### [1:30] THE CONCEPT: RAG EXPLAINED SIMPLY
*(Screen: whiteboard / sketchnote — this is where the sketchnote image shines)*

"Before we touch code, let's make sure RAG actually clicks. Because if you understand this one concept, you understand half of enterprise AI in 2026."

"Here's the problem with a plain chatbot: the model only knows what it was trained on. Ask it about a menu it's never seen, and it will confidently invent a 'Unicorn Latte.' That's hallucination — and in banking, healthcare, or customer service, a confident wrong answer is a lawsuit."

"RAG fixes it with three steps — retrieve, augment, generate:

1. RETRIEVE — the agent has a tool. In our case, a function that reads menu.json — the real menu, with prices and allergens.
2. AUGMENT — the retrieved data gets injected into the prompt as context, alongside the user's question.
3. GENERATE — the LLM answers using ONLY that context. It can't invent a drink, because the only drinks it can see are in the menu."

*(Key visual: three boxes R→A→G with arrows)*

"Think of it like this: the LLM is a brilliant chef who talks a lot — RAG hands him the actual fridge contents before he starts cooking. He can only cook what's in the fridge."

### [2:30] WHY A TOOL, NOT JUST THE PROMPT?
*(This is the "token efficiency" discussion from the lab — real insight)*

"Quick question you should ask: why not just paste the menu into the system prompt? For 8 items, that's cheap. But what if the shop has 500 items? Every single query pays for all 500 items in tokens — even the 'what are your hours?' question. By using a tool, the agent calls the menu ONLY when it needs it. That's token economy — the difference between a demo and a product."

### [3:30] THE ARCHITECTURE
*(Screen: architecture image)*

"Here's the full picture: Streamlit chat UI on top → ADK agent with Gemini inside → a get_menu() tool → menu.json as the source of truth. When you ask a question, the agent decides 'I need menu data,' calls the tool, gets the items, and answers grounded. Clean, simple, production-shaped."

### [5:30] THE LAB — LET'S BUILD IT
*(Screen: Cloud Shell)*

"Alright, enough theory — let's build. I'm starting in Cloud Shell so there's zero local setup. If you're following along, the full manual is linked in the description and on GitHub."

**STEP 1 — Project setup**
```bash
gcloud config set project <YOUR_PROJECT_ID>
gcloud services enable run.googleapis.com aiplatform.googleapis.com cloudbuild.googleapis.com
export PROJECT_ID=$(gcloud config get-value project)
export REGION=us-central1   # use your closest region
mkdir coffee-barista-agent && cd coffee-barista-agent
```
*(Show the API enable verification: `gcloud services list --enabled`)*

"APIs take 2-3 minutes to activate — I'll show you how to verify they're ready before moving on."

### [7:00] THE LAB — menu.json + agent.py
*(Screen: editor with menu.json)*

"First, the menu — this is the source of truth. 8 items, each with name, description, price, tags, and allergens."

*(Show menu.json, scroll through items quickly)*

"Notice the structure: tags like 'strong', 'hot', 'dairy-free' — and allergens like 'dairy' on the pumpkin latte. This structure is what lets the agent reason: 'lactose intolerant → exclude anything with dairy.'"

*(Cut to agent.py)*

"Now the agent. This is where ADK shines — look how little code it takes:"

```python
def get_menu() -> str:
    """Retrieves the coffee shop menu from menu.json."""
    with open("menu.json", "r") as f:
        return json.dumps(json.load(f))

barista_agent = LlmAgent(
    name="barista_agent",
    model="gemini-3.5-flash",
    instruction="""You are a friendly barista... Recommend ONLY items from get_menu().
Never suggest anything not on the menu...""",
    tools=[get_menu]
)
```

"That's it. A function + an agent with instructions + the tool registered. The instruction matters — 'recommend ONLY from the menu' is the guardrail that kills hallucination. ADK handles the rest."

### [10:00] THE LAB — Streamlit app.py
*(Screen: app.py + sidebar)*

"Now the face of the app — Streamlit. Two cool parts:

One: the sidebar renders the real menu with prices, tags, and allergen warnings — pulled from the same menu.json. Users see the truth before they even ask.

Two: the chat. We create an InMemoryRunner around the agent, keep a session ID, and run each message through run_debug() — collecting the response text back into the chat."

*(Show a chat exchange working locally)*

"Look at that — 'recommend something strong and warm' → espresso. The grounding is working locally."

### [12:00] THE LAB — Deploy to Cloud Run
*(Screen: the deploy command + output)*

"Now the magic: serverless deployment from source. One command:"

```bash
gcloud run deploy coffee-barista \
  --source . \
  --region $REGION \
  --allow-unauthenticated \
  --command "/cnb/lifecycle/launcher" \
  --args "sh,-c,python3 -m streamlit run app.py --server.port=\$PORT --server.address=0.0.0.0" \
  --service-account "barista-agent-sa@$PROJECT_ID.iam.gserviceaccount.com" \
  --set-env-vars GOOGLE_GENAI_USE_ENTERPRISE=TRUE,GOOGLE_CLOUD_PROJECT=$PROJECT_ID,GOOGLE_CLOUD_LOCATION=global
```

*(Wait for the build — 3-5 min, show the progress)*

"Notice what I did NOT do: use the default service account. I created a dedicated `barista-agent-sa` with only the AI Platform user role. Principle of least privilege — the app can call Gemini and nothing else. If it gets compromised, there's no blast radius."

### [13:30] THE TEST — RAG in action
*(Screen: the deployed URL, live testing — THE money shot)*

"Here's the moment of truth — live, on the deployed URL."

**Test 1 — In-menu:** "Recommend something strong and warm." → Espresso ✓

**Test 2 — The trap:** "Do you have a matcha frappuccino?" → *agent politely declines* — "I'm sorry, that's not on our menu..." ✓

**Test 3 — Allergen-aware:** "I'm lactose intolerant, what can I get?" → only dairy-free items: Oat Milk Latte, Espresso, Cold Brew. NO croissant, NO pumpkin latte ✓

"That third test is the money shot. The model didn't just avoid hallucinating — it reasoned about allergens from the data. That's the difference between a demo and something you'd actually ship."

### [15:30] KEY LESSONS + GOTCHAS
*(Screen: bullet list)*

"Three things I want you to take away:

1. **Grounding is a prompt + a tool + data.** The instruction 'only from the menu' plus the tool boundary is what makes it safe.
2. **Token economy matters.** Tools over prompt-dumping — that's how you scale from 8 items to 500.
3. **Least privilege on Cloud Run.** A dedicated service account with one role. It takes 2 extra commands and saves you from a bad day.

Gotchas I hit: the APIs take a couple minutes to activate — check `gcloud services list --enabled` before proceeding. And the first deploy takes 3-5 minutes to build the container — that's normal, don't panic."

### [16:30] CTA + DAY 2 TEASE
*(Screen: series outro card)*

"Day 1 done. ✅ Day 2: I'm taking this same agent and securing it with a real MCP server on Cloud Run — Model Context Protocol, the protocol everyone's talking about.

If you want to follow along, everything is on GitHub — link in description. The full lab manual, the code, the screenshots. And if this helped, like and share — it genuinely helps the series reach more builders.

I'm Abdul — 29 more labs to go. See you tomorrow. ☕"

---

## 🎨 VISUALS NEEDED
1. **Sketchnote:** RAG concept (retrieve → augment → generate) — use `pega` style or the thumbnail generator
2. **Architecture image** (already in repo)
3. **B-roll:** Cloud Shell commands running, menu.json scrolling, agent.py, live chat tests
4. **Thumbnail:** RAG AGENT / AI COFFEE BARISTA (already generated)

## 📝 DESCRIPTION TEMPLATE
```
☕ I built an AI coffee barista with RAG on Google Cloud — and it CANNOT hallucinate.

Day 1 of 30 Labs, 30 Days: building AI on Google Cloud, one lab a day.

In this video:
0:00 The hook
0:30 What we're building
1:30 RAG explained simply
5:30 Lab: GCP setup
7:00 Lab: menu.json + ADK agent
10:00 Lab: Streamlit UI
12:00 Deploy to Cloud Run
13:30 Live testing (the fun part)
15:30 Lessons + gotchas

📖 Full lab manual + code: https://github.com/bpmforbusiness/gcp-ai-labs-30-days
🔗 Codelab: https://codelabs.developers.google.com/codelabs/cloud-run/build-streamlit-rag-agent-google-adk-cloud-run

30 Labs, 30 Days playlist: [link]

#RAG #GoogleCloud #CloudRun #AI #Gemini #ADK #Streamlit #GenAI #30DaysOfAI
```

## 📌 YOUTUBE TAGS
rag, retrieval augmented generation, google cloud, cloud run, gemini, adk, agent development kit, streamlit, ai agent, enterprise ai, rag explained, ai hallucination, google ai, serverless, 30 days of ai, gcp tutorial
