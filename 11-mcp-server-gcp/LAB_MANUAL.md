# Build, Secure, and Deploy an MCP Server on Google Cloud

## Complete Implementation Lab Manual

**Prepared by:** Abdul Qaadir (@TechWorldWithAbdul)
**Series:** 30 Labs, 30 Days — Day 11 · **Last Updated:** September 2026

---

## 1. Introduction

### Overview
Build a **production-grade, secure MCP server** using **FastMCP** + **uv** that exposes **four Google Cloud tools**, then containerize and deploy it to **two** runtime targets (Cloud Run + GKE Autopilot), and register it in **Gemini Enterprise Agent Platform (Agent Registry)**.

**The security theme:** MCP servers give AI agents the keys to your cloud. This lab shows how to deploy one with **no static credentials, enforced IAM, HTTPS/SSL, and secretless Workload Identity** — the difference between a hobby server and one an enterprise would trust.

### The 4 MCP tools you'll build
1. **`vertex_ai_generate_content`** — invoke Vertex AI Gemini (live `google-genai` SDK)
2. **`gcs_bucket_inspector`** — list/inspect a Cloud Storage bucket (live)
3. **`cloud_logging_audit_writer`** — write structured audit entries (live)
4. **`gcp_resource_health_checker`** — health/status (static mock, zero-dependency)

> **Design note:** tools 1–3 make real API calls; tool 4 is intentionally a static mock so test clients can verify the pipeline with no extra quotas. In production extend it with `google-cloud-resource-manager` or Cloud Monitoring Uptime Checks.

### What you'll do
- Build a FastMCP server conforming to **MCP Spec 2026-07-28** over Streamable HTTP
- Containerize with a **multi-stage Docker build** (via `uv`)
- Secure-deploy to **Cloud Run** (IAM-enforced auth + managed SSL)
- Secure-deploy to **GKE Autopilot** using **Workload Identity** + **Kubernetes Gateway API with TLS**
- Register the endpoint in **Agent Registry** with OIDC bearer-token auth, then test via Service Discovery

### Cost
**50 minutes** · MCP server itself is tiny (serverless/GKE). Largest cost is the transient GKE Autopilot cluster — delete it after (cleanup commands included).

---

## 2. Before You Begin

### Prerequisites
- Google Cloud project (**billing enabled**)
- `gcloud` CLI installed + configured
- **Python 3.10+** and **`uv`** installed
- `docker` installed
- `kubectl` installed

### Key mental model: MCP Spec 2026-07-28
The newest MCP spec (published 2026-07-28) defines a **stateless architecture, simplified transports, and strict result typing** (`resultType: "complete"`), while staying backward compatible. FastMCP implements this over **Streamable HTTP** (SSE + HTTP) with SSL/TLS.

---

## 3. Set Up Google Cloud Environment

### Login + set project
```bash
gcloud auth login
export PROJECT_ID=$(gcloud config get-value project)
gcloud config set project ${PROJECT_ID}
```

### Enable all required APIs
```bash
gcloud services enable \
    agentregistry.googleapis.com \
    run.googleapis.com \
    container.googleapis.com \
    artifactregistry.googleapis.com \
    aiplatform.googleapis.com \
    logging.googleapis.com \
    storage.googleapis.com \
    compute.googleapis.com \
    iam.googleapis.com \
    --project="${PROJECT_ID}"
```

### Local credentials for dev-time client libraries
```bash
gcloud auth application-default login
```

---

## 4. Build the MCP Server with FastMCP + uv

### Initialize the project
```bash
mkdir -p mcp-server/src/mcp_server
cd mcp-server
uv init --lib
```

### `pyproject.toml`
```toml
[project]
name = "secure-mcp-gcp-server"
version = "0.1.0"
description = "FastMCP server with Google Cloud tools supporting FastMCP Spec 2026-07 over SSE/HTTP with SSL"
readme = "README.md"
requires-python = ">=3.10"
dependencies = [
    "fastmcp>=0.4.0",
    "mcp>=1.2.0",
    "google-genai>=1.0.0",
    "google-cloud-storage>=2.14.0",
    "google-cloud-logging>=3.11.0",
    "google-cloud-resource-manager>=1.12.0",
    "uvicorn>=0.30.0",
    "httpx>=0.27.0",
    "pydantic>=2.7.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/mcp_server"]
```

### Install deps
```bash
uv sync
```

### `src/mcp_server/server.py`
```python
import os
import logging
from typing import Dict, Any, List, Optional
from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import PlainTextResponse
from google import genai
from google.cloud import storage
from google.cloud import logging as cloud_logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp-gcp-server")

# Initialize FastMCP Server conforming to MCP Spec 2026-07-28
mcp = FastMCP(
    "Google Cloud Production Tools",
    instructions="MCP Server conforming to MCP Spec 2026-07-28 for Vertex AI, Cloud Storage, Audit Logging, and Health Inspection."
)

@mcp.custom_route("/healthz", methods=["GET"])
async def health_check(request: Request) -> PlainTextResponse:
    """Kubernetes readiness and liveness probe health check endpoint."""
    return PlainTextResponse("OK")

@mcp.tool(description="Generate content or answer questions using Vertex AI Gemini model.")
def vertex_ai_generate_content(
    prompt: str,
    model_name: str = "gemini-2.5-flash",
    project_id: Optional[str] = None,
    location: str = "us-central1"
) -> str:
    """Invokes Vertex AI Gemini API using official google-genai SDK."""
    target_project = project_id or os.getenv("GCP_PROJECT") or os.getenv("GOOGLE_CLOUD_PROJECT")
    if not target_project:
        return "Error: GCP project ID not configured."

    try:
        client = genai.Client(vertexai=True, project=target_project, location=location)
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
        )
        return response.text or "No text returned from Gemini."
    except Exception as e:
        logger.error(f"Vertex AI Tool Error: {e}")
        return f"Error executing Vertex AI tool: {str(e)}"

@mcp.tool(description="List objects and inspect metadata for a specified Google Cloud Storage bucket.")
def gcs_bucket_inspector(
    bucket_name: str,
    max_results: int = 10,
    prefix: Optional[str] = None
) -> Dict[str, Any]:
    """Inspects GCS bucket content and metadata conforming to MCP Spec 2026-07-28 resultType schema."""
    try:
        client = storage.Client()
        bucket = client.bucket(bucket_name)
        blobs = list(client.list_blobs(bucket, max_results=max_results, prefix=prefix))
        items = [{"name": b.name, "size_bytes": b.size, "updated": str(b.updated)} for b in blobs]
        return {
            "resultType": "complete",
            "bucket_name": bucket_name,
            "object_count_sample": len(items),
            "objects": items
        }
    except Exception as e:
        logger.error(f"GCS Inspector Error: {e}")
        return {"resultType": "complete", "error": f"Failed to inspect GCS bucket: {str(e)}"}

@mcp.tool(description="Write structured operational or security audit log records to Google Cloud Logging.")
def cloud_logging_audit_writer(
    log_name: str,
    message: str,
    severity: str = "INFO",
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Sends structured audit entry to Cloud Logging."""
    try:
        client = cloud_logging.Client()
        logger_instance = client.logger(log_name)
        payload = {"message": message, "metadata": metadata or {}, "source": "mcp-server-gcp"}
        logger_instance.log_struct(payload, severity=severity.upper())
        return {
            "resultType": "complete",
            "status": "success",
            "log_name": log_name,
            "recorded_message": message
        }
    except Exception as e:
        logger.error(f"Cloud Logging Error: {e}")
        return {"resultType": "complete", "error": f"Failed to record audit log: {str(e)}"}

@mcp.tool(description="Check health and operational state of Google Cloud project resources.")
def gcp_resource_health_checker(project_id: Optional[str] = None) -> Dict[str, Any]:
    """Returns project resource summary and status."""
    target_project = project_id or os.getenv("GOOGLE_CLOUD_PROJECT") or "unknown-project"
    return {
        "resultType": "complete",
        "status": "HEALTHY",
        "project_id": target_project,
        "mcp_spec_version": "2026-07-28",
        "_meta": {
            "io.modelcontextprotocol/protocolVersion": "2026-07-28",
            "io.modelcontextprotocol/serverInfo": {"name": "mcp-gcp-server", "version": "0.1.0"}
        },
        "transports_enabled": ["Streamable HTTP"],
        "ssl_tls_enabled": True
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    logger.info(f"Starting FastMCP Server on port {port} (Streamable HTTP Transport, Spec 2026-07-28)...")
    mcp.run(transport="http", host="0.0.0.0", port=port)
```

---

## 5. Test the MCP Server Locally

### Start the server (terminal 1)
```bash
uv run python -m src.mcp_server.server
```
You should see:
```
INFO:mcp-gcp-server:Starting FastMCP Server on port 8080 (Streamable HTTP Transport, Spec 2026-07-28)...
INFO: Starting MCP server 'Google Cloud Production Tools' with transport 'http' on http://0.0.0.0:8080/mcp
INFO:     Uvicorn running on http://0.0.0.0:8080 (Press CTRL+C to quit)
```

### Verify Streamable HTTP via curl (terminal 2)
> The Streamable HTTP spec **requires both** `Content-Type: application/json` AND `Accept: application/json, text/event-stream` headers.

```bash
curl -i -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc": "2.0", "method": "initialize", "params": {"protocolVersion": "2026-07-28", "capabilities": {}, "clientInfo": {"name": "curl-test", "version": "1.0.0"}}, "id": 1}'
```
Expected: `HTTP/1.1 200 OK`, `content-type: text/event-stream`, `mcp-session-id: ...`, with a JSON-RPC init result.

### Run the MCP test client
Create `src/mcp_server/test_client.py`:
```python
import asyncio
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

async def test_mcp_server():
    server_url = "http://localhost:8080/mcp"
    print(f"[*] Connecting to local FastMCP Server at {server_url} (Streamable HTTP)...")

    async with streamable_http_client(server_url) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("[+] Connected and initialized session successfully.")

            tools_response = await session.list_tools()
            print("\n[*] Discovered MCP Tools:")
            for tool in tools_response.tools:
                print(f"  - {tool.name}: {tool.description}")

            print("\n[*] Invoking tool: gcp_resource_health_checker...")
            health_result = await session.call_tool("gcp_resource_health_checker", {})
            print("[+] Result:")
            for content in health_result.content:
                print(content.text)

if __name__ == "__main__":
    asyncio.run(test_mcp_server())
```
Run it:
```bash
uv run python src/mcp_server/test_client.py
```
Expected output: connection success, 4 discovered tools, and the health-check result JSON. Then `CTRL+C` in terminal 1.

---

## 6. Containerize the MCP Server

### Multi-stage `Dockerfile` (built with `uv`)
```dockerfile
FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim AS builder

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

COPY pyproject.toml uv.lock* /app/
RUN uv sync --no-install-project --no-dev

COPY README.md /app/
COPY src /app/src
RUN uv sync --no-dev

FROM python:3.11-slim-bookworm

WORKDIR /app
COPY --from=builder /app /app

ENV PATH="/app/.venv/bin:$PATH"
ENV PORT=8080
ENV PYTHONUNBUFFERED=1

EXPOSE 8080
CMD ["python", "-m", "src.mcp_server.server"]
```

### Create Artifact Registry repo + build with Cloud Build
```bash
gcloud artifacts repositories create mcp-servers \
    --repository-format=docker \
    --location=us-central1 \
    --description="Docker repository for MCP Servers" \
    --project="${PROJECT_ID}"

export IMAGE_URI="us-central1-docker.pkg.dev/${PROJECT_ID}/mcp-servers/secure-mcp-server:latest"

gcloud builds submit . --tag="${IMAGE_URI}" --project="${PROJECT_ID}"
```
Output: `SUCCESS: Image published to us-central1-docker.pkg.dev/.../secure-mcp-server:latest`

---

## 7. Deploy to Cloud Run with IAM & HTTPS

### Create least-privilege service account
```bash
gcloud iam service-accounts create mcp-server-cr-sa \
    --display-name="MCP Server Cloud Run SA" \
    --project="${PROJECT_ID}"

export SA_EMAIL="mcp-server-cr-sa@${PROJECT_ID}.iam.gserviceaccount.com"

gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
    --member="serviceAccount:${SA_EMAIL}" --role="roles/aiplatform.user"
gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
    --member="serviceAccount:${SA_EMAIL}" --role="roles/logging.logWriter"
gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
    --member="serviceAccount:${SA_EMAIL}" --role="roles/storage.objectViewer"
```

### Deploy with enforced IAM auth
```bash
gcloud run deploy secure-mcp-server \
    --image="${IMAGE_URI}" \
    --platform=managed \
    --region=us-central1 \
    --service-account="${SA_EMAIL}" \
    --set-env-vars="GOOGLE_CLOUD_PROJECT=${PROJECT_ID}" \
    --no-allow-unauthenticated \
    --ingress=all \
    --project="${PROJECT_ID}"

export CLOUD_RUN_URL=$(gcloud run services describe secure-mcp-server --platform=managed --region=us-central1 --format='value(status.url)' --project="${PROJECT_ID}")
echo "Cloud Run HTTPS Endpoint: ${CLOUD_RUN_URL}"
```

### Verify security: unauthenticated → 401
```bash
curl -i -X POST "${CLOUD_RUN_URL}/mcp" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc": "2.0", "method": "initialize", "params": {"protocolVersion": "2026-07-28", "capabilities": {}, "clientInfo": {"name": "curl-test", "version": "1.0.0"}}, "id": 1}'
```
Expected: `HTTP/2 401`.

### Authorized request with OIDC token → 200
```bash
export ID_TOKEN=$(gcloud auth print-identity-token --audiences="${CLOUD_RUN_URL}")

curl -i -X POST "${CLOUD_RUN_URL}/mcp" \
  -H "Authorization: Bearer ${ID_TOKEN}" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc": "2.0", "method": "initialize", "params": {"protocolVersion": "2026-07-28", "capabilities": {}, "clientInfo": {"name": "curl-test", "version": "1.0.0"}}, "id": 1}'
```
Expected: `HTTP/2 200 OK` + MCP init event.

### Test live tool: Cloud Storage Inspector
Create a bucket + file:
```bash
export BUCKET_NAME="${PROJECT_ID}-mcp-demo"
gcloud storage buckets create "gs://${BUCKET_NAME}" --location=us-central1 --project="${PROJECT_ID}"
echo "Hello from Secure MCP on Google Cloud!" > sample.txt
gcloud storage cp sample.txt "gs://${BUCKET_NAME}/sample.txt"
```
Create `src/mcp_server/test_gcs_tool.py` (authenticates via OIDC token, passes an httpx client into `streamable_http_client`):
```python
import asyncio, os, subprocess, httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

async def test_gcs_tool():
    cloud_run_url = os.getenv("CLOUD_RUN_URL")
    bucket_name = os.getenv("BUCKET_NAME")
    if not cloud_run_url or not bucket_name:
        print("[!] Please set both CLOUD_RUN_URL and BUCKET_NAME environment variables.")
        return
    id_token = subprocess.check_output(
        ["gcloud", "auth", "print-identity-token", f"--audiences={cloud_run_url}"], text=True).strip()
    headers = {"Authorization": f"Bearer {id_token}"}
    server_url = f"{cloud_run_url}/mcp"
    print(f"[*] Connecting to remote Cloud Run MCP server at {server_url} (Streamable HTTP)...")
    async with httpx.AsyncClient(headers=headers) as http_client:
        async with streamable_http_client(server_url, http_client=http_client) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                print("[+] Authenticated and initialized remote MCP session.")
                tools_response = await session.list_tools()
                print(f"[*] Verified {len(tools_response.tools)} available tools on Cloud Run.")
                print(f"\n[*] Invoking tool: gcs_bucket_inspector on '{bucket_name}'...")
                result = await session.call_tool("gcs_bucket_inspector", {"bucket_name": bucket_name})
                print("[+] Response from Cloud Run MCP Server:")
                for content in result.content:
                    print(content.text)

if __name__ == "__main__":
    asyncio.run(test_gcs_tool())
```
Run it:
```bash
uv run python src/mcp_server/test_gcs_tool.py
```
Expected: live object metadata returned from Cloud Run (your `sample.txt`, 39 bytes).

---

## 8. Deploy to GKE Autopilot with Workload Identity & TLS

### Provision cluster
```bash
gcloud container clusters create-auto mcp-gke-cluster \
    --location=us-central1 \
    --project="${PROJECT_ID}"

gcloud container clusters get-credentials mcp-gke-cluster \
    --location=us-central1 \
    --project="${PROJECT_ID}"
```

### Workload Identity (GSA ↔ KSA, no static keys)
```bash
gcloud iam service-accounts create mcp-gke-sa \
    --display-name="GKE MCP Service Account" --project="${PROJECT_ID}"
export GSA_EMAIL="mcp-gke-sa@${PROJECT_ID}.iam.gserviceaccount.com"

gcloud projects add-iam-policy-binding "${PROJECT_ID}" --member="serviceAccount:${GSA_EMAIL}" --role="roles/aiplatform.user"
gcloud projects add-iam-policy-binding "${PROJECT_ID}" --member="serviceAccount:${GSA_EMAIL}" --role="roles/logging.logWriter"
gcloud projects add-iam-policy-binding "${PROJECT_ID}" --member="serviceAccount:${GSA_EMAIL}" --role="roles/storage.objectViewer"

kubectl create serviceaccount mcp-server-ksa --namespace default
kubectl annotate serviceaccount mcp-server-ksa --namespace default \
    iam.gke.io/gcp-service-account="${GSA_EMAIL}"
gcloud iam service-accounts add-iam-policy-binding "${GSA_EMAIL}" \
    --role="roles/iam.workloadIdentityUser" \
    --member="serviceAccount:${PROJECT_ID}.svc.id.goog[default/mcp-server-ksa]" \
    --project="${PROJECT_ID}"
```

### Deployment + internal Service manifest (`deployment.yaml`)
Note the **MCP-registry labels/annotations** and the `iam.gke.io/spiffe-identity-type: agent-identity` annotation.
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mcp-server-deployment
  namespace: default
  labels:
    app: mcp-server
    registry.gke.io/functional-type: "MCP_SERVER"
  annotations:
    modelcontextprotocol.info/urls: |
      - https://mcp.34.36.245.158.nip.io/mcp
    modelcontextprotocol.info/capabilities: |
      card:
        endpoint: "/mcp"
        protocol: "HTTP"
spec:
  replicas: 2
  selector:
    matchLabels:
      app: mcp-server
  template:
    metadata:
      labels:
        app: mcp-server
      annotations:
        iam.gke.io/spiffe-identity-type: agent-identity
    spec:
      serviceAccountName: mcp-server-ksa
      containers:
      - name: mcp-server
        image: us-central1-docker.pkg.dev/PROJECT_ID/mcp-servers/secure-mcp-server:latest
        ports:
        - containerPort: 8080
          name: http
        env:
        - name: PORT
          value: "8080"
        - name: GOOGLE_CLOUD_PROJECT
          value: "PROJECT_ID"
        resources:
          requests:
            cpu: "250m"
            memory: "512Mi"
          limits:
            cpu: "1000m"
            memory: "1Gi"
        readinessProbe:
          httpGet:
            path: /healthz
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 10
        livenessProbe:
          httpGet:
            path: /healthz
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 15
---
apiVersion: v1
kind: Service
metadata:
  name: mcp-server-service
  namespace: default
  labels:
    app: mcp-server
spec:
  type: ClusterIP
  sessionAffinity: ClientIP
  ports:
  - port: 80
    targetPort: 8080
    name: http
  selector:
    app: mcp-server
```
Apply:
```bash
sed "s/PROJECT_ID/${PROJECT_ID}/g" deployment.yaml | kubectl apply -f -
```

### Static IP + Google-managed SSL via `nip.io`
```bash
gcloud compute addresses create mcp-server-ip --global --project="${PROJECT_ID}"
export MCP_IP=$(gcloud compute addresses describe mcp-server-ip --global --format="value(address)" --project="${PROJECT_ID}")
export MCP_DOMAIN="mcp.${MCP_IP}.nip.io"

gcloud compute ssl-certificates create mcp-server-cert \
    --domains="${MCP_DOMAIN}" --global --project="${PROJECT_ID}"
```

### Gateway, HTTPRoute, HealthCheckPolicy, GCPBackendPolicy (`gateway.yaml`)
```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: Gateway
metadata:
  name: mcp-gateway
  namespace: default
spec:
  gatewayClassName: gke-l7-global-external-managed
  listeners:
  - name: https
    protocol: HTTPS
    port: 443
    tls:
      mode: Terminate
      options:
        networking.gke.io/pre-shared-certs: mcp-server-cert
  addresses:
  - type: NamedAddress
    value: mcp-server-ip
---
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: mcp-http-route
  namespace: default
spec:
  parentRefs:
  - name: mcp-gateway
  hostnames:
  - "MCP_DOMAIN"
  rules:
  - matches:
    - path:
        type: PathPrefix
        value: /
    backendRefs:
    - name: mcp-server-service
      port: 80
---
apiVersion: networking.gke.io/v1
kind: HealthCheckPolicy
metadata:
  name: mcp-health-check-policy
  namespace: default
spec:
  default:
    checkIntervalSec: 15
    timeoutSec: 5
    healthyThreshold: 1
    unhealthyThreshold: 2
    config:
      type: HTTP
      httpHealthCheck:
        port: 8080
        requestPath: /healthz
  targetRef:
    group: ""
    kind: Service
    name: mcp-server-service
---
apiVersion: networking.gke.io/v1
kind: GCPBackendPolicy
metadata:
  name: mcp-backend-policy
  namespace: default
spec:
  default:
    sessionAffinity:
      type: CLIENT_IP
  targetRef:
    group: ""
    kind: Service
    name: mcp-server-service
```
Apply:
```bash
sed "s/MCP_DOMAIN/${MCP_DOMAIN}/g" gateway.yaml | kubectl apply -f -
```

> **Why `GCPBackendPolicy` session affinity?** MCP Streamable HTTP stores session state in memory after initialization. `sessionAffinity: CLIENT_IP` routes a client's subsequent tool calls to the **same pod** holding its active session.
> **Why `HealthCheckPolicy`?** Tells the GLB to probe `/healthz` on 8080.

### Test pods immediately via port-forward
```bash
kubectl get pods -l app=mcp-server
kubectl get gateway mcp-gateway
kubectl port-forward svc/mcp-server-service 8080:80
```
Create `src/mcp_server/test_vertex_tool.py` (flexible host via `--host` flag, defaults to `http://localhost:8080/mcp` or `$MCP_URL`):
```python
import argparse, asyncio, os
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

async def test_vertex_tool(server_url: str):
    print(f"[*] Connecting to MCP server at {server_url} (Streamable HTTP)...")
    async with streamable_http_client(server_url) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("[+] Connected and initialized session successfully.")
            tools_response = await session.list_tools()
            print(f"[*] Discovered {len(tools_response.tools)} MCP Tools:")
            for tool in tools_response.tools:
                print(f"  - {tool.name}")
            prompt = "Explain in 2 sentences why Model Context Protocol (MCP) Streamable HTTP is great for cloud deployments."
            print(f"\n[*] Invoking tool: vertex_ai_generate_content with prompt: '{prompt}'...")
            result = await session.call_tool("vertex_ai_generate_content", {"prompt": prompt, "model_name": "gemini-2.5-flash"})
            print("\n[+] Response from Vertex AI Gemini:")
            for content in result.content:
                print(content.text)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test Vertex AI MCP Tool on FastMCP Server.")
    parser.add_argument("--host", default=os.getenv("MCP_URL", "http://localhost:8080/mcp"),
                        help="MCP Server host or URL (default: http://localhost:8080/mcp or $MCP_URL)")
    args = parser.parse_args()
    url = args.host
    if not url.startswith("http://") and not url.startswith("https://"):
        url = f"https://{url}"
    if not url.endswith("/mcp"):
        url = f"{url.rstrip('/')}/mcp"
    asyncio.run(test_vertex_tool(url))
```
Run via the port-forward:
```bash
uv run python src/mcp_server/test_vertex_tool.py --host="http://localhost:8080/mcp"
```
Expected: **Gemini answers via Vertex AI** — this confirms pods are healthy **AND Workload Identity is authenticating secretless** against Vertex AI.

### Verify the public HTTPS endpoint
> The GLB + Google-managed SSL cert take **~5–15 min** to provision (status `PROVISIONING` → `ACTIVE`). Check with:
> ```bash
> gcloud compute ssl-certificates describe mcp-server-cert --global --format="value(managed.status)"
> ```
Once `ACTIVE`:
```bash
uv run python src/mcp_server/test_vertex_tool.py --host="https://${MCP_DOMAIN}/mcp"
```
You should see the same 4 tools + a Gemini answer over public HTTPS.

---

## 9. Integrate with Gemini Enterprise Agent Platform (Agent Registry)

### Register the Cloud Run server

**Extract `toolspec.json`** from the live server:
```bash
export ID_TOKEN=$(gcloud auth print-identity-token --audiences="${CLOUD_RUN_URL}")

export SESSION_ID=$(curl -s -i -X POST "${CLOUD_RUN_URL}/mcp" \
  -H "Authorization: Bearer ${ID_TOKEN}" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2026-07-28", "capabilities": {}, "clientInfo": {"name": "cli", "version": "1.0"}}}' \
  | grep -i '^mcp-session-id:' | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST "${CLOUD_RUN_URL}/mcp" \
  -H "Authorization: Bearer ${ID_TOKEN}" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: ${SESSION_ID}" \
  -d '{"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}' \
  | grep '^data: ' | sed 's/^data: //' | jq '.result' > toolspec.json
```

**Register the service:**
```bash
export SERVER_NAME="secure-mcp-server"
export DISPLAY_NAME="Google Cloud FastMCP Server"
export REGION="global"

gcloud agent-registry services create "${SERVER_NAME}" \
  --project="${PROJECT_ID}" \
  --location="${REGION}" \
  --display-name="${DISPLAY_NAME}" \
  --mcp-server-spec-type="tool-spec" \
  --mcp-server-spec-content=toolspec.json \
  --interfaces="url=${CLOUD_RUN_URL}/mcp,protocolBinding=jsonrpc"

gcloud agent-registry services describe "${SERVER_NAME}" --location="${REGION}"
```

**Service Discovery test client** (`src/mcp_server/test_agent_platform.py`):
```python
import asyncio, os, subprocess, httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

async def main():
    server_name = os.getenv("SERVER_NAME", "secure-mcp-server")
    location = os.getenv("REGION", "global")

    print(f"[*] Discovering '{server_name}' from Agent Registry...")
    url = subprocess.check_output([
        "gcloud", "agent-registry", "services", "describe", server_name,
        f"--location={location}", "--format=value(interfaces[0].url)"
    ], text=True).strip()
    print(f"[+] Discovered Endpoint: {url}")

    headers = {}
    if "run.app" in url:
        audience = url.split("/mcp")[0]
        token = subprocess.check_output(
            ["gcloud", "auth", "print-identity-token", f"--audiences={audience}"], text=True).strip()
        headers["Authorization"] = f"Bearer {token}"

    async with httpx.AsyncClient(headers=headers, timeout=30.0) as http_client:
        async with streamable_http_client(url, http_client=http_client) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools = await session.list_tools()
                print(f"[+] Session active. Discovered {len(tools.tools)} tools:")
                for tool in tools.tools:
                    print(f"    - {tool.name}")
                print("\n[*] Invoking tool: gcp_resource_health_checker...")
                result = await session.call_tool("gcp_resource_health_checker", {})
                print(f"[+] Tool Output from Agent Platform:\n{result.content[0].text}")

if __name__ == "__main__":
    asyncio.run(main())
```
Run:
```bash
uv run python src/mcp_server/test_agent_platform.py
```

### GKE automatic discovery (no toolspec needed!)
Because your `deployment.yaml` already carried these, GKE auto-registered the server:
- `registry.gke.io/functional-type: "MCP_SERVER"` → registers the deployment into Agent Registry
- `modelcontextprotocol.info/urls` → internal ClusterIP endpoint for introspection
- `modelcontextprotocol.info/capabilities` → declares `/mcp` transport
- `iam.gke.io/spiffe-identity-type: agent-identity` → Workload Identity for agentic comms

Verify auto-registration:
```bash
gcloud agent-registry mcp-servers list --location=global
```
Expect both `mcp-server-deployment` (GKE, auto) and `secure-mcp-server` (Cloud Run, manual) as `ACTIVE`. Then describe to see the auto-ingested tools:
```bash
gcloud agent-registry mcp-servers describe mcp-server-deployment --location=us-central1
```
Test it via service discovery:
```bash
SERVER_NAME="mcp-server-deployment" REGION=us-central1 uv run python src/mcp_server/test_agent_platform.py
```

---

## 10. Clean Up Resources

```bash
# Cloud Run
gcloud run services delete secure-mcp-server --platform=managed --region=us-central1 --quiet --project="${PROJECT_ID}"
# GKE cluster (biggest cost — delete promptly)
gcloud container clusters delete mcp-gke-cluster --location=us-central1 --quiet --project="${PROJECT_ID}"
# Service accounts
gcloud iam service-accounts delete "mcp-server-cr-sa@${PROJECT_ID}.iam.gserviceaccount.com" --quiet --project="${PROJECT_ID}"
gcloud iam service-accounts delete "mcp-gke-sa@${PROJECT_ID}.iam.gserviceaccount.com" --quiet --project="${PROJECT_ID}"
# Artifact Registry
gcloud artifacts repositories delete mcp-servers --location=us-central1 --quiet --project="${PROJECT_ID}"
# Agent Registry service
gcloud agent-registry services delete secure-mcp-server --location=global --quiet --project="${PROJECT_ID}"
# Bucket
gcloud storage rm --recursive "gs://${BUCKET_NAME}" --quiet
# Static IP + cert
gcloud compute ssl-certificates delete mcp-server-cert --global --quiet --project="${PROJECT_ID}"
gcloud compute addresses delete mcp-server-ip --global --quiet --project="${PROJECT_ID}"
```
Verify:
```
Deleted service [secure-mcp-server].
Deleted cluster [mcp-gke-cluster].
Deleted repository [mcp-servers].
```

---

## 11. Gotchas & Pro Tips

- **Streamable HTTP needs TWO headers** — `Content-Type: application/json` AND `Accept: application/json, text/event-stream`. Drop either and the handshake fails.
- **The `uv` Dockerfile uses `uv sync --no-dev` twice** — first without the project (layer cache friendly), then with `src` copied. Don't skip `uv.lock*` copy or builds become non-reproducible.
- **`--no-allow-unauthenticated` is the security boundary on Cloud Run** — without it your MCP server is public on the internet with real cloud permissions. Always verify the **401** before the **200**.
- **Session affinity matters on GKE** — MCP Streamable HTTP holds session state in memory. Without `GCPBackendPolicy` `sessionAffinity: CLIENT_IP`, a tool call can land on a different pod than the one holding your session → errors. (On Cloud Run this is handled for you.)
- **`nip.io` gives you a real domain cheaply** (`mcp.<IP>.nip.io`) so Google can issue a managed SSL cert without you owning DNS. Perfect for labs; use a real domain in production.
- **GKE Workload Identity = zero static keys** — the GSA↔KSA binding + `iam.gke.io/spiffe-identity-type` lets pods inherit cloud roles with no `GOOGLE_APPLICATION_CREDENTIALS` json. Verify with the Vertex tool call, not just pod READY.
- **GKE's auto-discovery replaces `toolspec.json`** — labeling `registry.gke.io/functional-type: MCP_SERVER` makes GKE introspect and register your tools automatically. Only the Cloud Run path needs the manual curl→jq extraction.
- **Probe reads matter** — use `/healthz` (the custom FastMCP route) for both readiness and liveness, and configure `HealthCheckPolicy` to the same path so the GLB and K8s agree.
- **Cleanup order** — delete the GKE cluster FIRST (it's the biggest hourly cost) but leave the SSL cert / static IP until after you're done testing the public endpoint.

---

## 12. What You Learned

- Built a FastMCP server conforming to **MCP Spec 2026-07-28** over Streamable HTTP.
- Built 4 production Google Cloud tools (Vertex AI Gemini, Cloud Storage, Cloud Logging, Resource Health).
- Secured deployments on **Cloud Run** with enforced IAM + SSL/TLS (401-unauth → OIDC-200).
- Configured **secretless authentication on GKE Autopilot** with Workload Identity + Gateway API TLS.
- Registered the endpoint in **Gemini Enterprise Agent Platform** (manual toolspec for Cloud Run, auto-discovery for GKE) and tested via Service Discovery.

**Follow along with the video:** [Link to be added when published]