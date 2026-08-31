# Getting Started with Agent2Agent (A2A) Protocol

## Complete Implementation Lab Manual

**Prepared by:** Abdul Qaadir (@TechWorldWithAbdul)
**Series:** 30 Labs, 30 Days — Day 8 · **Last Updated:** August 2026


---

## 1. Introduction

### Overview
The **Agent2Agent (A2A) protocol** standardizes communication between AI agents—especially those deployed in external systems. It **complements MCP** (Model Context Protocol):
- **MCP** = connects LLMs to *tools and data* (makes tools available to agents).
- **A2A** = lets *agents collaborate as agents* — back-and-forth, multi-turn communication (not just calling a tool).

Per the [official A2A docs](https://a2a-protocol.org/latest/): **use MCP for tools, A2A for agents** — with the agent's capabilities published via an **Agent Card**.

### What you'll build
A **personal purchasing concierge** (ADK) that talks to **two remote "seller" agents** over A2A:
- 🍔 **Burger agent** — built with **CrewAI**
- 🍕 **Pizza agent** — built with **LangGraph**

Both sellers are deployed as **A2A servers** on Cloud Run. The concierge is the **A2A client**, deployed on **Agent Engine**.

### What you'll learn
- Core structure of an A2A Server (Agent Card, task queue, agent executor)
- Core structure of an A2A Client
- Deploying an agent service to **Cloud Run**
- Deploying an agent service to **Vertex AI Agent Engine**
- How an A2A Client connects to A2A Servers (discovery)
- JSON-RPC request/response on a non-streaming connection

### Architecture Overview
```
User
  │
  ▼  (ADK — A2A Client)
Purchasing Concierge —── deployed on AGENT ENGINE
  │                              │
  │  A2A                        │  A2A
  ▼                              ▼
┌──────────────┐          ┌──────────────┐
│ Burger Agent│           │  Pizza Agent │
│  (CrewAI)   │           │  (LangGraph) │
│  Cloud Run  │           │  Cloud Run   │
└──────────────┘          └──────────────┘
  (A2A Servers)
```
The user only interacts with the Purchasing Concierge. The three agents use **completely different frameworks** (ADK, CrewAI, LangGraph) — A2A makes that irrelevant.

### Prerequisites
- Comfortable with Python
- Basic understanding of HTTP-based full-stack architecture

### Cost
Run the deployment, test, then delete the resources (see Clean Up). Costs are Cloud Run + Agent Engine + Vertex AI usage — keep minimal by cleaning up after.

---

## 2. Preparing the Workshop Development Setup

### Step 1: Select the Active Cloud Project
In the [Google Cloud Console](https://console.cloud.google.com/), select or create a project. Note your **PROJECT ID** (the value in parentheses, red box on the project selector) — used throughout the tutorial.

Make sure **billing is enabled**: navigation menu (☰) → **Billing** → confirm "Google Cloud Platform Trial Billing Account" is linked. If not, redeem a trial billing account first.

### Step 2: Cloud Shell setup
Click **Activate Cloud Shell** at the top of the console (click **Authorize** if prompted).

Verify auth:
```bash
gcloud auth list
```
You should see your personal Gmail as the ACTIVE credentialed account. If not, refresh the browser and re-authorize.

Check the configured project (the value in `( )` before `$`):
```bash
gcloud config set project <YOUR_PROJECT_ID>
```
(run only if the shown project is wrong/missing)

Clone the starter working directory:
```bash
git clone https://github.com/alphinside/purchasing-concierge-intro-a2a-codelab-starter.git purchasing-concierge-a2a
```

### Step 3: Open the editor + set up the app
1. Click **Open Editor** (Cloud Shell Editor).
2. **File → Open Folder** → find your username → **purchasing-concierge-a2a** → **OK**.
3. Open a terminal (**Terminal → New Terminal**, or `Ctrl + Shift + C`).

Install dependencies into a venv (Cloud Shell has `uv` preinstalled; we use Python 3.12):
```bash
uv sync --frozen
```
Check `pyproject.toml` — dependencies are `a2a-sdk`, `google-adk`, and `gradio`.

Enable required APIs:
```bash
gcloud services enable aiplatform.googleapis.com \
                       run.googleapis.com \
                       cloudbuild.googleapis.com \
                       cloudresourcemanager.googleapis.com
```
On success: `Operation "operations/..." finished successfully.`

---

## 3. Deploying A2A Server Remote Seller Agents to Cloud Run

Deploy the two remote seller agents (burger = CrewAI, pizza = LangGraph).

### Deploy the Burger Seller Agent (A2A Server)
Source code is under `remote_seller_agents/burger_agent`:
```bash
gcloud run deploy burger-agent \
    --source remote_seller_agents/burger_agent \
    --port=8080 \
    --allow-unauthenticated \
    --min 1 \
    --region us-central1 \
    --update-env-vars GOOGLE_CLOUD_LOCATION=us-central1 \
    --update-env-vars GOOGLE_CLOUD_PROJECT={your-project-id}
```
If prompted about creating a container repository to deploy from source, answer **Y**. On success:
```
Service [burger-agent] revision [burger-agent-xxxxx-xxx] has been deployed and is serving 100 percent of traffic.
Service URL: https://burger-agent-xxxxxxxxx.us-central1.run.app
```
Open the **Agent Card** (the A2A server "business card"): `https://burger-agent-xxxxxxxxx.us-central1.run.app/.well-known/agent.json`

### Update the Agent Card URL (HOST_OVERRIDE)
The card's `url` value is initially `http://0.0.0.0:8080/` — not reachable from outside. Fix it:
1. Search **Cloud Run** in the console → click the **burger-agent** service.
2. Copy the service URL → click **Edit and deploy new revision**.
3. Open **Variables & Secrets** → **Add variable**.
4. Set `HOST_OVERRIDE` = the Cloud Run URL (`https://burger-agent-xxxxxxxxx.us-central1.run.app`).
5. Click **Deploy**.
Re-open the agent card — the `url` is now correct.

### Deploy the Pizza Seller Agent (A2A Server)
Same process, source under `remote_seller_agents/pizza_agent`:
```bash
gcloud run deploy pizza-agent \
    --source remote_seller_agents/pizza_agent \
    --port=8080 \
    --allow-unauthenticated \
    --min 1 \
    --region us-central1 \
    --update-env-vars GOOGLE_CLOUD_LOCATION=us-central1 \
    --update-env-vars GOOGLE_CLOUD_PROJECT={your-project-id}
```
Copy the service URL, then **add `HOST_OVERRIDE`** = pizza Cloud Run URL (same steps as burger). Verify at `https://pizza-agent-xxxxxxxxx.us-central1.run.app/.well-known/agent.json`.

Both A2A server services are now live on Cloud Run.

---

## 4. Deploying the Purchasing Concierge (A2A Client) to Agent Engine

### Create the staging bucket
```bash
gcloud storage buckets create gs://purchasing-concierge-{your-project-id} --location=us-central1
```

### Prepare the `.env` file
```bash
cp .env.example .env
```
Edit `.env`:
```
GOOGLE_GENAI_USE_VERTEXAI=TRUE
GOOGLE_CLOUD_PROJECT={your-project-id}
GOOGLE_CLOUD_LOCATION=us-central1
STAGING_BUCKET=gs://purchasing-concierge-{your-project-id}
PIZZA_SELLER_AGENT_URL={your-pizza-agent-url}
BURGER_SELLER_AGENT_URL={your-burger-agent-url}
AGENT_ENGINE_RESOURCE_NAME={your-agent-engine-resource-name}
```
Fill `PIZZA_SELLER_AGENT_URL` and `BURGER_SELLER_AGENT_URL` with the Cloud Run URLs from the previous step (find them in the Cloud Run console, or `gcloud run services list`).

### Deploy to Agent Engine
```bash
uv run deploy_to_agent_engine.py
```
On success:
```
AgentEngine created. Resource name: projects/xxxx/locations/us-central1/reasoningEngines/yyyy
To use this AgentEngine in another session:
agent_engine = vertexai.agent_engines.get('projects/xxxx/locations/us-central1/reasoningEngines/yyyy)
```
Then **update `AGENT_ENGINE_RESOURCE_NAME`** in `.env` with that resource name.

### Test the deployed agent
```bash
bash test_agent_engine.sh
```
(It asks the agent: *"List available burger menu please"*.) You'll see streamed response events, including the burger menu (e.g., Classic/Double Cheeseburger, Spicy Chicken Burger) with token usage metadata.

---

## 5. Integration Testing and Payload Inspection

Launch the Gradio web UI:
```bash
uv run purchasing_concierge_ui.py
```
Output: `Running on local URL: http://0.0.0.0:8080` → **Ctrl + click** that URL (or use the Web Preview button).

Have a conversation:
- "Show me burger and pizza menu"
- "I want to order 1 bbq chicken pizza and 1 spicy cajun burger"

Continue until the order is complete. **Notice** the two sellers behave differently: the **pizza agent accepts** the request directly, while the **burger agent requests confirmation** before proceeding. A2A handles both interaction styles transparently.

---

## 6. Code Explanation — A2A Server Concept & Implementation

### The seller agents use different frameworks
**Burger (CrewAI):**
```python
from crewai import Agent, Crew, LLM, Task, Process
from crewai.tools import tool
...
model = LLM(model="vertex_ai/gemini-2.5-flash-lite")
burger_agent = Agent(
    role="Burger Seller Agent",
    goal=("Help user to understand what is available on burger menu and price also handle order creation."),
    backstory=("You are an expert and helpful burger seller agent."),
    allow_delegation=False,
    tools=[create_burger_order],
    llm=model,
)
agent_task = Task(description=self.TaskInstruction, agent=burger_agent, ...)
crew = Crew(tasks=[agent_task], agents=[burger_agent], process=Process.sequential)
```
**Pizza (LangGraph):**
```python
from langchain_google_vertexai import ChatVertexAI
from langgraph.prebuilt import create_react_agent
self.model = ChatVertexAI(model="gemini-2.5-flash-lite", location=..., project=...)
self.graph = create_react_agent(self.model, tools=self.tools, checkpointer=memory, prompt=self.SYSTEM_INSTRUCTION)
```

**The point:** these use entirely different frameworks from the ADK client — yet A2A lets them interoperate with zero shared internal code.

### Core components of an A2A Server

**1. Agent Card** — served at `/.well-known/agent.json`. Like a well-documented API (Swagger/Postman) for agents:
```json
{
  "capabilities": { "streaming": true },
  "defaultInputModes": ["text", "text/plain"],
  "defaultOutputModes": ["text", "text/plain"],
  "description": "Helps with creating burger orders",
  "name": "burger_seller_agent",
  "protocolVersion": "0.2.6",
  "skills": [
    { "id": "create_burger_order", "name": "Burger Order Creation Tool",
      "description": "Helps with creating burger orders", "examples": ["I want to order 2 classic cheeseburgers"], "tags": ["burger order creation"] }
  ],
  "url": "https://burger-agent-109790610330.us-central1.run.app",
  "version": "1.0.0"
}
```
Key fields: `AgentCapabilities` (streaming/push), `AgentSkill` (tools), `Input/OutputModes` (modalities), `Url` (address).
The card is built in `main.py` using the A2A Python SDK:
```python
agent_card = AgentCard(
    name="burger_seller_agent",
    url=agent_host_url, version="1.0.0",
    defaultInputModes=..., defaultOutputModes=...,
    capabilities=AgentCapabilities(streaming=True),
    skills=[AgentSkill(id="create_burger_order", ...)],
)
```
The dynamic `agent_host_url` (`HOST_OVERRIDE` env → `http://{host}:{port}/`) lets you switch between local and cloud deployment.

**2. Task Queue and Agent Executor** — each A2A server isolates tasks. Inherit the `AgentExecutor` abstract class to control task execution/cancellation (`agent_executor.py`):
```python
class BurgerSellerAgentExecutor(AgentExecutor):
    def __init__(self):
        self.agent = BurgerSellerAgent()
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        query = context.get_user_input()
        result = self.agent.invoke(query, context.context_id)
        parts = [Part(root=TextPart(text=str(result)))]
        await event_queue.enqueue_event(
            completed_task(context.task_id, context.context_id,
                           [new_artifact(parts, f"burger_{context.task_id}")], [context.message])
        )
    async def cancel(self, request, event_queue) -> Task | None:
        raise ServerError(error=UnsupportedOperationError())
```
Spin up the HTTP server with built-in helpers (`__main__.py`):
```python
request_handler = DefaultRequestHandler(
    agent_executor=BurgerSellerAgentExecutor(),
    task_store=InMemoryTaskStore(),
)
server = A2AStarletteApplication(agent_card=agent_card, http_handler=request_handler)
uvicorn.run(server.build(), host=host, port=port)
```
This provides the `/.well-known/agent.json` route + the POST endpoint for the A2A protocol.

### Agent Engine deployment (the concierge)
The concierge is built with ADK and deployed to **Vertex AI Agent Engine** — which handles production scaling of agents. **No Dockerfile needed** — deploy directly from a Python script:
```python
from google.adk import Agent
...
def create_agent(self) -> Agent:
    return Agent(
        model="gemini-2.5-flash-lite",
        name="purchasing_agent",
        instruction=self.root_instruction,
        before_model_callback=self.before_model_callback,
        before_agent_callback=self.before_agent_callback,
        tools=[self.send_task],
    )
```
Deploy via `deploy_to_agent_engine.py` using `vertexai.agent_engines`.

---

## 7. The A2A Client <-> Server Flow

**The typical A2A flow (client-server):**
1. **A2A Client** performs **discovery** on accessible A2A Server **agent cards**, using the card info to build a connection client.
2. When needed, the client sends a **Message** to the server. The server evaluates it as a **Task**. *(If a push-notification receiver URL is configured and supported, the server publishes task-progress state to the client endpoint.)*
3. After the task finishes, the server sends the **response artifact** back to the client.

**The Task/Messaging model:** the Task domain is *owned by the server*; the client sees it as a **Message**. This interchange uses **JSON-RPC 2.0**:
```json
{
  "id": "abc123",
  "jsonrpc": "2.0",
  "method": "message/send",
  "params": { "message": "hi, what can you help me with?" }
}
```
Various methods support sync, streaming, async, and task-status notifications. The client's `send_task` tool retrieves the right client for the agent and sends `SendMessageRequest` metadata to each seller.

---

## 8. Challenge (optional)

Deploy the Gradio app to Cloud Run yourself. (Prep the app so it runs as a deployable service — image, container, deploy.)

---

## 9. Clean Up

To avoid ongoing charges:
1. Console → **Manage Resources** → select the project → **Delete** → type the project ID → **Shut down**.
2. Or delete just the services: console → **Cloud Run** and **Agent Engine** → select each deployed service → **Delete**.

---

## Key Takeaways
- **A2A = agents talking to agents** (multi-turn, back-and-forth); **MCP = agents calling tools**. Use MCP for tools, A2A for agents.
- **Agent Cards** (`/.well-known/agent.json`) are the discovery mechanism — like agent "business cards."
- A2A servers expose an agent card + handle **JSON-RPC tasks** (via `AgentExecutor` + task store + Starlette app).
- **Frameworks don't matter** — ADK, CrewAI, LangGraph interoperate over A2A with zero shared code.
- Cloud Run hosts the servers; **Agent Engine** hosts the ADK client with no Dockerfile needed.
- The concierge can even handle agents that *ask for confirmation* mid-task (human/agent-in-the-loop), demonstrating A2A's bidirectional nature.
