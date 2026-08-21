# Build a Google Trends Analyst Agent with BigQuery MCP

## 1. Overview
In this codelab, you will build a Google Trends Analyst Agent using the Google ADK. This agent leverages the BigQuery MCP server to dynamically discover and execute tools that query the Google Trends public dataset (`bigquery-public-data.google_trends`).

### What you'll learn
* How to set up a project for ADK development.
* How to enable and use Managed MCP servers for BigQuery.
* How to build an agent that uses MCP tools.
* How to run the agent locally for testing.
* How to deploy the agent to Google Cloud Run.

### What you'll need
* A Google Cloud project with billing enabled
* A web browser such as Chrome
* Python 3.11+

This codelab is for intermediate developers who have some familiarity with Python and Google Cloud.
This codelab takes approximately 15-20 minutes to complete.
The resources created in this codelab should cost less than $5.

## 2. Set up your environment

### Create a Google Cloud Project
In the Google Cloud Console, on the project selector page, select or create a Google Cloud project.
Make sure that billing is enabled for your Cloud project. Learn how to check if billing is enabled on a project.
We encourage you to use Google Cloud Shell for this codelab. It provides a terminal environment with Python and the Google Cloud CLI already installed.
To activate Cloud Shell, click the Activate Cloud Shell button at the top of the Google Cloud console.

### Set Environment Variables
Set the following environment variables.

```bash
export GOOGLE_CLOUD_PROJECT=<INSERT_YOUR_GCP_PROJECT_HERE>
export GOOGLE_GENAI_USE_VERTEXAI=1
```
*Note: Setting `GOOGLE_GENAI_USE_VERTEXAI=1` directs the ADK to use Vertex AI, leveraging Cloud IAM for authentication instead of a GEMINI_API_KEY.*

### Authenticate and Configure gcloud
Sign in to your Google Account, set your active project, and configure Application Default Credentials.
You may skip this step if you are using the Cloud Shell.

```bash
gcloud auth login
gcloud auth application-default login
```
*Note: `gcloud auth login` authenticates the gcloud CLI commands, while `gcloud auth application-default login` authenticates local application code.*

Set the Google Cloud project:

```bash
gcloud config set project ${GOOGLE_CLOUD_PROJECT}
```

### Enable Necessary APIs
Enable the required Google Cloud APIs for Cloud Run, Artifact Registry, BigQuery, and Vertex AI.

```bash
gcloud services enable run.googleapis.com                        cloudbuild.googleapis.com                        artifactregistry.googleapis.com                        bigquery.googleapis.com                        aiplatform.googleapis.com
```

### Enable MCP for BigQuery
Managed MCP servers must be explicitly enabled for your project.

```bash
gcloud beta services mcp enable bigquery.googleapis.com
```

### Create a Project Folder
Start by creating a root folder for your agent and an internal folder for the agent implementation.

```bash
mkdir google-trends-agent
cd google-trends-agent
mkdir google_trends
```

## 3. Create the Agent Code

Create an empty file named `google_trends/__init__.py`:

```bash
touch google_trends/__init__.py
```

Then, create a file named `google_trends/agent.py` and paste the following code:

```python
import os
import textwrap
import warnings
from datetime import date

import google.auth
from google.adk.agents import LlmAgent
from google.adk.apps import App
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams
from google.auth.transport.requests import Request

# Suppress experimental ADK credential warnings
warnings.filterwarnings("ignore")

def get_agent_instruction(project_id: str) -> str:
    """Generates a clear and formatted prompt for the data analyst."""
    instruction = f"""
    # ROLE
    You are a Google Search Trends Analyst. Your mission is to provide clear answers using SQL data.

    # DATA CONSTRAINTS
    - BigQuery tool `execute_sql` requires explicit billing project mapping. Use: '{project_id}'.
    - Target dataset strictly: `bigquery-public-data.google_trends`

    # SCHEMA DISCOVERY (CRITICAL)
    1. DO NOT call `get_table_info` or `list_table_ids` (Triggers Permission Errors).
    2. Run `SELECT * FROM table LIMIT 0` via `execute_sql` for field definition mapping.

    # OUTPUT PRESENTATION
    - Render purely as a cleanly aligned Markdown table.
    - Use clear and descriptive headers for each column.
    - Remove conversational preambles. Output only the results.
    """
    return textwrap.dedent(instruction).strip()

def get_auth_headers() -> dict[str, str]:
    """Fetch auth headers for the project using Google Cloud Platform scopes."""
    credentials, _ = google.auth.default(
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    request = Request()
    credentials.refresh(request)

    return {"Authorization": f"Bearer {credentials.token}"}

def get_todays_date() -> str:
    """Returns today's date in YYYY-MM-DD format."""
    return date.today().isoformat()

# --- Application Initialization ---
project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
if not project_id:
    raise ValueError("GOOGLE_CLOUD_PROJECT environment variable is not set")

mcp_headers = {
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream",
} | get_auth_headers()

# Configure BigQuery Tools via MCP
bq_tools = McpToolset(
    connection_params=StreamableHTTPConnectionParams(
        url="https://bigquery.googleapis.com/mcp",
        headers=mcp_headers,
    )
)

# Initialize the LLM Agent
root_agent = LlmAgent(
    name="google_trends",
    model="gemini-3-flash-preview",
    tools=[get_todays_date, bq_tools],
    instruction=get_agent_instruction(project_id),
)

# Create the ADK App
app = App(name=root_agent.name, root_agent=root_agent)
```

## 4. Run the agent
In this step, you will set up a local Python virtual environment, install dependencies, and run the agent to verify its behavior on your machine (or Google Cloud Shell).
Navigate to the application root directory (`google-trends-agent`).
Create a virtual environment:

```bash
python -m venv mcp_demo_env
source mcp_demo_env/bin/activate
```

Install the required Python packages:

```bash
pip install google-auth google-adk[mcp]
```

We will use ADK Web to test our new agent.
For local development and testing, run the following command:

```bash
adk web
```

For development and testing within Google Cloud Shell, run the following command:

```bash
adk web --allow_origins="*"
```

This will start the ADK web server. You can interact with the agent using the local web interface (usually at `http://localhost:8000`).
*Note: You may also use the simpler `adk run google_trends` command to test the agent.*

Try asking your agent these prompts:
* Show me the top trends in the USA
* What are the top rising trends in France this month?
* What were the top 3 trends in California last week?
* What are the BigQuery tables that you have access to?
* Tell me everything you know about the top_trends table

## 5. Deploy to Cloud Run
Follow these steps to deploy the agent securely to Google Cloud Run.

### Grant Permissions
Cloud Run needs permission to access Vertex AI and use BigQuery MCP tools.

```bash
# Get your project number automatically
PROJECT_NUMBER=$(gcloud projects describe $GOOGLE_CLOUD_PROJECT --format='value(projectNumber)')

# Vertex AI Access: To talk to the Gemini model
gcloud projects add-iam-policy-binding ${GOOGLE_CLOUD_PROJECT}   --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"   --role="roles/aiplatform.user"

# MCP & BigQuery: To execute tools and run SQL jobs
gcloud projects add-iam-policy-binding ${GOOGLE_CLOUD_PROJECT}   --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"   --role="roles/mcp.toolUser"

gcloud projects add-iam-policy-binding ${GOOGLE_CLOUD_PROJECT}   --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"   --role="roles/bigquery.jobUser"

gcloud projects add-iam-policy-binding ${GOOGLE_CLOUD_PROJECT}   --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"   --role="roles/bigquery.dataViewer"
```

### Create the Dockerfile
In the root of your project (`google-trends-agent`), create a file named `Dockerfile` and paste the following content:

```dockerfile
FROM python:3.11-slim
WORKDIR /app

# Create a non-root user
RUN adduser --disabled-password --gecos "" myuser
USER myuser
ENV PATH="/home/myuser/.local/bin:$PATH"

# Copy the agent folder into the container
COPY --chown=myuser:myuser google_trends/ /app/agents/google_trends/

# Install the python packages
RUN pip install google-auth google-adk

# Set environment variables
ENV GOOGLE_GENAI_USE_VERTEXAI=1

# Expose port
EXPOSE 8080

# Run ADK web server
CMD ["adk", "web", "--port=8080", "--host=0.0.0.0", "/app/agents"]
```

### Deploy the Agent
Run the following command from the root directory. This will containerize and deploy your agent to Cloud Run.
Keep an eye on the command output. Once the deployment finishes, it will provide a Service URL. You will use this URL to interact with your agent.

```bash
gcloud run deploy google-trends-agent   --source .   --region us-west1   --allow-unauthenticated   --set-env-vars="GOOGLE_CLOUD_PROJECT=${GOOGLE_CLOUD_PROJECT}"
```

### Quick Verification
Once the deployment finishes, the console will output a Service URL. Open this URL in your browser; it will provide the same interactive UI you saw locally, but now running in the cloud!
You can also monitor the logs to ensure everything is running smoothly:

```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=google-trends-agent" --limit 10
```

## 6. Clean Up
To avoid ongoing charges, delete the resources created during this codelab.

Delete the Cloud Run service:
```bash
gcloud run services delete google-trends-agent --region us-west1
```

If you created a project specifically for this codelab, you can delete the entire project:
```bash
gcloud projects delete ${GOOGLE_CLOUD_PROJECT}
```

You may also delete all the files related to this codelab:
```bash
deactivate
cd ..
rm -rf google-trends-agent
```
