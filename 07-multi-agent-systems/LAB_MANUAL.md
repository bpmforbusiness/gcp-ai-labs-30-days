# Build Multi-Agent Systems with ADK

## Complete Implementation Lab Manual

**Prepared by:** Abdul Qaadir (@TechWorldWithAbdul)
**Series:** 30 Labs, 30 Days — Day 7 · **Last Updated:** August 2026
**Original codelab:** [Build Multi-Agent Systems with ADK](https://codelabs.developers.google.com/codelabs/production-ready-ai-with-gc/3-developing-agents/build-a-multi-agent-system-with-adk)

---

## 1. Introduction

### Overview
This lab teaches you how to orchestrate complex, multi-agent systems using the Google Agent Development Kit (Google ADK). You'll move from simple agent hierarchies to building automated, collaborative workflows.

### What you'll build
Two distinct multi-agent systems:
- A simple **travel planning agent** that learns to transfer conversations between a "brainstorming" agent and an "attraction planning" agent.
- A more advanced **movie pitch generator** that uses a "writer's room" of automated agents (like a researcher, screenwriter, and critic) to work together in a loop to create a full movie plot.

### What you'll learn
- How to create parent and sub-agent relationships.
- How to write data to the session `state` from a tool.
- How to read from the `state` using key templating (e.g., `{my_key?}`).
- How to use a `SequentialAgent` for step-by-step workflows.
- How to use a `LoopAgent` to create iterative refinement cycles.
- How to use a `ParallelAgent` to run independent tasks concurrently.

### Cost
Completing this lab should cost **less than $1 USD**. New users get the $300 Free Trial.

---

## 2. Multi-Agent Systems — The Concept

ADK lets you build a **flow of multiple, simpler agents** that collaborate on a problem by dividing the work — instead of one complex prompt. Advantages:

- **Simpler Design:** easier to design and organize small, specialized agents than one large prompt.
- **Reliability:** specialized agents are more reliable at their specific tasks.
- **Maintainability:** fix one small agent without breaking others.
- **Modularity:** agents built for one workflow are reusable in others.

### The Hierarchical Agent Tree
In ADK, agents are organized in a **tree structure**. The entire structure starts with the **`root_agent`** — a **parent** that can have one or more **sub-agents**, which can themselves be parents. This hierarchy controls the conversation flow: it limits which agent can "pass" the conversation to which other agent, making behavior predictable and easier to debug.

---

## 3. Project Setup

### Google Account
Use a **personal Google account** (work/school accounts may have restrictions).

### Enable Billing
- Redeem Google Cloud credits (banner at top of codelab) OR set up a personal billing account at console.cloud.google.com/billing.

### Create a Project (optional)
If you don't have a project: [create a new project](https://console.cloud.google.com/projectcreate).

---

## 4. Open Cloud Shell Editor

1. Click this link to navigate directly to [Cloud Shell Editor](https://ide.cloud.google.com/).
2. If prompted, click **Authorize**.
3. If the terminal doesn't appear: **View** → **Terminal**.
4. In the terminal, set your project:

```shell
gcloud config set project [PROJECT_ID]
```

Example: `gcloud config set project lab-project-id-example`

- If you can't remember your project ID: `gcloud projects list`
- Success message: `Updated property [core/project].`

---

## 5. Enable APIs

Enable the Vertex AI API to interact with Gemini:

```shell
gcloud services enable aiplatform.googleapis.com
```

**Note:** You'll use the **Vertex AI SDK for Python** to interact with models hosted on Vertex AI. Docs: [Introduction to the Vertex AI SDK for Python](https://cloud.google.com/vertex-ai/docs/python-sdk/use-vertex-ai-python-sdk).

---

## 6. Set up the Project Environment

### Clone the repo

```shell
git clone --depth 1 https://github.com/GoogleCloudPlatform/devrel-demos.git devrel-demos-multiagent-lab
```

The `--depth 1` flag clones only the latest version (faster).

### Move the lab folder and navigate

```bash
mv devrel-demos-multiagent-lab/ai-ml/build-multiagent-systems-with-adk/adk_multiagent_systems ~
cd ~/adk_multiagent_systems
```

### Review your file structure
Open the `adk_multiagent_systems` folder in the Explorer (File → Open Folder...). You should see two sub-directories: `parent_and_subagents` and `workflow_agents`.

### Activate a virtual environment

```bash
uv venv
source .venv/bin/activate
```

Install dependencies:

```shell
uv pip install -r requirements.txt
```

### Set up environment variables

Create a `.env` file:

```shell
cloudshell edit .env
```

Paste:

```python
GOOGLE_GENAI_USE_VERTEXAI=TRUE
GOOGLE_CLOUD_PROJECT="[YOUR-PROJECT-ID]"
GOOGLE_CLOUD_LOCATION=global
MODEL="gemini-2.5-flash"
```

Replace `[YOUR-PROJECT-ID]` with your actual project ID. Copy `.env` into the sub-agent directories:

```shell
cp .env parent_and_subagents/.env
cp .env workflow_agents/.env
```

---

## 7. Explore transfers between parent, sub-agent, and peer agents

The conversation always starts with the `root_agent`. By default, a parent uses its sub-agents' `description` to decide when to transfer. You can also guide transfers explicitly in the parent's `instruction` using the sub-agents' `name`.

### Step 1 — Open `parent_and_subagents/agent.py`
Notice the three agents:
- **`root_agent`** (named **`steering`**): asks the user a question to decide which sub-agent to transfer to.
- **`travel_brainstormer`**: helps brainstorm destinations.
- **`attractions_planner`**: helps list things to do in a country.

### Step 2 — Make them sub-agents

Add to the `root_agent` creation:

```python
    sub_agents=[travel_brainstormer, attractions_planner]
```

### Step 3 — Test the automatic transfer

```shell
cd ~/adk_multiagent_systems
adk run parent_and_subagents
```

At the `[user]:` prompt, type `hello`. Then reply: `I could use some help deciding.`

You should see `[travel_brainstormer]:` — the root transferred **automatically based on the description only**.

Type `exit` to end the conversation.

### Step 4 — Make transfers explicit

Add to the `root_agent`'s `instruction`:

```python
        If they need help deciding, send them to 'travel_brainstormer'.
        If they know what country they'd like to visit, send them to the 'attractions_planner'.
```

Run again:

```shell
adk run parent_and_subagents
```

- `hello` → reply `I would like to go to Japan.` → **`[attractions_planner]`** responds (explicit instruction guided the transfer).
- Reply `Actually I don't know what country to visit.` → **`[travel_brainstormer]`** responds — note that peer-to-peer transfers are allowed by default.
- Type `exit` to end.

### Recap
- Conversation always starts with `root_agent`.
- Parent can auto-transfer based on `description`.
- Explicit control via `instruction` using agent `name`.
- By default, agents can transfer to **peer** agents (siblings).

---

## 8. Use session state to store and retrieve information

Every ADK conversation has a `Session` with a **state dictionary**, accessible to ALL agents — perfect for passing info between them.

### Step 1 — Add a state-saving tool

In `parent_and_subagents/agent.py`, paste after the `# Tools` header:

```python
def save_attractions_to_state(
    tool_context: ToolContext,
    attractions: List[str]
) -> dict[str, str]:
    """Saves the list of attractions to state["attractions"].

    Args:
        attractions [str]: a list of strings to add to the list of attractions

    Returns:
        None
    """
    # Load existing attractions from state. If none exist, start an empty list
    existing_attractions = tool_context.state.get("attractions", [])

    # Update the 'attractions' key with a combo of old and new lists.
    # When the tool is run, ADK will create an event and make
    # corresponding updates in the session's state.
    tool_context.state["attractions"] = existing_attractions + attractions

    # A best practice for tools is to return a status message in a return dict
    return {"status": "success"}
```

Key points:
- `tool_context: ToolContext` is your gateway to the session.
- `tool_context.state["attractions"] = ...` reads from and writes to the session's state.

### Step 2 — Add the tool to `attractions_planner`

```python
    tools=[save_attractions_to_state]
```

### Step 3 — Update the instruction

Add to `attractions_planner`'s `instruction`:

```python
        - When they reply, use your tool to save their selected attraction and then provide more possible attractions.
        - If they ask to view the list, provide a bulleted list of { attractions? } and then suggest some more.
```

### Step 4 — Test in the ADK Web UI

```shell
adk web
```

Output shows `ADK Web Server started... http://localhost:8000`.

1. Click **Web Preview** → **Change Port** → enter `8000` → **Change and Preview**.
2. From **Select an agent** dropdown, choose `parent_and_subagents`.
3. Conversation:
   - `hello` → reply `I'd like to go to Egypt.` → transferred to `attractions_planner` with a list.
   - Choose: `I'll go to the Sphinx` → "Okay, I've saved The Sphinx to your list..."
   - Click the tool-response box to see the event's `stateDelta`.
   - Add another attraction.
   - Open the **State** tab in the sidebar — you'll see the `attractions` array.
   - Ask: `What is on my list?` → the agent reads state and returns the list.
4. Stop the server: close tab + **CTRL + C**.

### Recap
- **Write state:** `tool_context.state["my_list"] = [...]` from within a tool.
- **Read state:** key templating in instructions, e.g. `Here is your list: {my_list?}`.
- **Inspect state:** State tab in the ADK Dev UI.

---

## 9. Workflow Agents — Overview

**Workflow agents** *execute* their sub-agents one after another in an automated flow, without waiting for user input. Perfect for "Plan and Execute" or "Draft and Revise" pipelines. ADK provides three built-in workflow agents:

- `SequentialAgent` — linear sequence
- `LoopAgent` — iterative loop
- `ParallelAgent` — concurrent execution

You'll build a **movie pitch generator** for a historical character, with agents for research, iterative writing, and report generation. Final system structure (film_concept_team):

```
greeter (root)
  └─ film_concept_team (SequentialAgent)
       ├─ writers_room (LoopAgent: researcher → screenwriter → critic)
       ├─ preproduction_team (ParallelAgent: box_office_researcher + casting_agent)
       └─ file_writer
```

---

## 10. Build a multi-agent system with a SequentialAgent

A `SequentialAgent` executes its sub-agents in a linear sequence, in order — perfect for ordered pipelines.

Structure of this first version:
- **`root_agent`** (**`greeter`**): welcomes the user, gets the movie subject.
- **`film_concept_team`** (`SequentialAgent`), which runs:
  1. **`researcher`** — gets facts from Wikipedia.
  2. **`screenwriter`** — uses those facts to write a plot.
  3. **`file_writer`** — saves the final plot to a file.

### Steps

1. Open `adk_multiagent_systems/workflow_agents/agent.py`.
   - **Note:** sub-agents must be defined before being assigned to a parent, so read the file from **bottom to top** to follow the conversational flow.
2. Notice the `append_to_state` tool — lets agents append data to a list in session state (how `researcher` and `screenwriter` pass work).
3. Launch the web UI with live-reloading:

```shell
cd ~/adk_multiagent_systems
adk web --reload_agents
```

4. Web Preview → Change Port → `8000` → select `workflow_agents`.
5. `hello` → `greeter` responds → when prompted, enter a historical figure (e.g. Zhang Zhongjing, Ada Lovelace, Marcus Aurelius).
6. The `SequentialAgent` runs all three sub-agents silently — no intermediate messages; the agent responds only when the whole sequence completes.
   - If it fails: click **+ New Session** and retry.
7. Open the generated `.txt` file in the **`movie_pitches`** directory.
8. In the Dev UI, click the last agent icon → **event view** → shows a visual graph of the agent tree (greeter → film_concept_team → sub-agents in order).
9. Click **Request** / **Response** tabs for any agent to inspect exact data passed (including session state).

### Recap
- `SequentialAgent` runs sub-agents one by one, in order, without user input between steps.
- Sub-agents use the **session state** (e.g., `{ PLOT_OUTLINE? }`) to access prior agents' work.
- The **event graph** visualizes and debugs the whole workflow.

---

## 11. Add a LoopAgent for iterative work

A `LoopAgent` runs its sub-agents in a sequence and **repeats** until a condition is met — `max_iterations` count or a sub-agent calling the built-in `exit_loop` tool. Great for iterative refinement.

You'll create a **"writer's room"**: `researcher`, `screenwriter`, and a new **`critic`** agent loop together, improving the plot each pass until the `critic` decides it's ready.

### Step 1 — Add the import

In `workflow_agents/agent.py`, near the other `google.adk` imports:

```python
from google.adk.tools import exit_loop
```

### Step 2 — Add the `critic` agent

Paste under the `# Agents` section:

```python
critic = Agent(
    name="critic",
    model=model_name,
    description="Reviews the outline so that it can be improved.",
    instruction="""
    INSTRUCTIONS:
    Consider these questions about the PLOT_OUTLINE:
- Does it meet a satisfying three-act cinematic structure?
- Do the characters' struggles seem engaging?
- Does it feel grounded in a real time period in history?
- Does it sufficiently incorporate historical details from the RESEARCH?

If the PLOT_OUTLINE does a good job with these questions, exit the writing loop with your 'exit_loop' tool.
If significant improvements can be made, use the 'append_to_state' tool to add your feedback to the field 'CRITICAL_FEEDBACK'.
Explain your decision and briefly summarize the feedback you have provided.

PLOT_OUTLINE:
{ PLOT_OUTLINE? }

RESEARCH:
{ research? }
""",
    before_model_callback=log_query_to_model,
    after_model_callback=log_model_response,
    tools=[append_to_state, exit_loop]
)
```

### Step 3 — Create the `writers_room` LoopAgent

Paste *above* the `film_concept_team` definition:

```python
writers_room = LoopAgent(
    name="writers_room",
    description="Iterates through research and writing to improve a movie plot outline.",
    sub_agents=[
        researcher,
        screenwriter,
        critic
    ],
    max_iterations=5,
)
```

### Step 4 — Update `film_concept_team`

Replace the existing definition:

```python
film_concept_team = SequentialAgent(
    name="film_concept_team",
    description="Write a film plot outline and save it as a text file.",
    sub_agents=[
        writers_room,
        file_writer
    ],
)
```

### Step 5 — Test the loop

1. Return to the ADK Dev UI → **+ New Session**.
2. `hello` → give a broader topic: *an industrial designer who made products for the masses*, *a cartographer*, *that guy who made crops yield more food*.
3. Watch the logs cycle: `[researcher]` → `[screenwriter]` → `[critic]` → repeat...
4. When the loop completes, the file is written to `movie_pitches`.
5. Inspect the **event graph** to see the loop structure.

### Recap
- `LoopAgent` repeats its sequence ("inner loop") for iterative tasks.
- Agents pass work via session state (`PLOT_OUTLINE`, `CRITICAL_FEEDBACK`).
- Loop stops via `max_iterations` or `exit_loop` tool.

---

## 12. Use a ParallelAgent for "fan out and gather"

A `ParallelAgent` executes all its sub-agents **at the same time** — ideal for independent sub-tasks. Pattern: "fan out" the work, then a later agent "gathers" results.

You'll add a **"preproduction team"**: one agent researches box office potential while another brainstorms casting — simultaneously.

### Step 1 — Add the ParallelAgent and sub-agents

Paste under the `# Agents` header:

```python
box_office_researcher = Agent(
    name="box_office_researcher",
    model=model_name,
    description="Considers the box office potential of this film",
    instruction="""
    PLOT_OUTLINE:
    { PLOT_OUTLINE? }

    INSTRUCTIONS:
    Write a report on the box office potential of a movie like that described in PLOT_OUTLINE based on the reported box office performance of other recent films.
    """,
    output_key="box_office_report"
)

casting_agent = Agent(
    name="casting_agent",
    model=model_name,
    description="Generates casting ideas for this film",
    instruction="""
    PLOT_OUTLINE:
    { PLOT_OUTLINE? }

    INSTRUCTIONS:
    Generate ideas for casting for the characters described in PLOT_OUTLINE
    by suggesting actors who have received positive feedback from critics and/or
    fans when they have played similar roles.
    """,
    output_key="casting_report"
)

preproduction_team = ParallelAgent(
    name="preproduction_team",
    sub_agents=[
        box_office_researcher,
        casting_agent
    ]
)
```

### Step 2 — Update `film_concept_team`

```python
film_concept_team = SequentialAgent(
    name="film_concept_team",
    description="Write a film plot outline and save it as a text file.",
    sub_agents=[
        writers_room,
        preproduction_team,
        file_writer
    ],
)
```

### Step 3 — Update the `file_writer` instruction (gather the reports)

Replace the `instruction` string:

```python
    instruction="""
    INSTRUCTIONS:
- Create a marketable, contemporary movie title suggestion for the movie described in the PLOT_OUTLINE.
If a title has been suggested in PLOT_OUTLINE, you can use it, or replace it with a better one.
- Use your 'write_file' tool to create a new txt file with the following arguments:
- for a filename, use the movie title
- Write to the 'movie_pitches' directory.
- For the 'content' to write, include:
- The PLOT_OUTLINE
- The BOX_OFFICE_REPORT
- The CASTING_REPORT

PLOT_OUTLINE:
{ PLOT_OUTLINE? }

BOX_OFFICE_REPORT:
{ box_office_report? }

CASTING_REPORT:
{ casting_report? }
""",
```

### Step 4 — Test

1. ADK Dev UI → **+ New Session** → `hello`.
2. Enter a new character idea: *that actress who invented the technology for wifi*, *an exciting chef*, *key players in the worlds fair exhibitions*.
3. When complete, inspect the final file — it should contain the plot + box office report + casting report in one document.

### Recap
- `ParallelAgent` "fans out" work, running sub-agents concurrently.
- Efficient for independent tasks.
- Results "gathered" by a later agent via session state (`output_key`) read by a final agent (like `file_writer`).

---

## 13. Custom workflow agents (optional)

When `SequentialAgent`, `LoopAgent`, and `ParallelAgent` aren't enough, **`CustomAgent`** provides flexibility for custom flow control, conditional execution, or state management between sub-agents. Useful for complex workflows, stateful orchestrations, or custom business logic. (Out of scope for this lab, but good to know it exists.)

---

## 14. Congratulations!

You've built a sophisticated multi-agent system with ADK — progressing from a simple parent-child relationship to orchestrating complex, automated workflows that research, write, and refine a creative project.

### What you did in this lab
- Organized agents in a **hierarchical tree** with parent/sub-agent relationships.
- Controlled **agent-to-agent transfers** (automatic via `description`, explicit via `instruction`).
- Used a **tool** to write data to `tool_context.state`.
- Used **key templating** (`{ PLOT_OUTLINE? }`) to read state and guide prompts.
- Implemented a **`SequentialAgent`** (research → write → save).
- Used a **`LoopAgent`** with a `critic` + `exit_loop` for iterative refinement.
- Used a **`ParallelAgent`** to fan out independent tasks concurrently.

### Continued experimentation
- **Add more agents:** e.g., a `marketing_agent` in `preproduction_team` that writes a tagline from the `PLOT_OUTLINE`.
- **Add more tools:** give `researcher` a Google Search API tool.
- **Explore `CustomAgent`:** conditionally run an agent only if a specific key exists in session state.

---

## Clean up

Delete the Cloud Shell resources when done (or keep the project for the next labs in the series):
```bash
cd ~
rm -rf adk_multiagent_systems devrel-demos-multiagent-lab
```
*(Optional: disable the Vertex AI API or delete the project to stop billing.)*
