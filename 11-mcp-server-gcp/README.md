# Day 11: Build, Secure, and Deploy an MCP Server on Google Cloud

**Series:** 30 Labs, 30 Days · **Topic:** GCP AI · **Product:** FastMCP, Cloud Run, GKE Autopilot, Workload Identity, Agent Registry
**Codelab:** [Build, Secure, and Deploy an MCP Server on Google Cloud](https://codelabs.developers.google.com/secure-mcp-server-gcp)
**Date:** 2026-09-07 · **Status:** ✅ Complete

> 🎬 **Watch the video:** [Day 11 — Secure MCP Server on GCP](https://youtu.be/myKbWJ5EefE)

> 🎬 **Thumbnail:** `screenshots/day11_thumbnail.png`

> 📘 **FOLLOW ALONG: [`LAB_MANUAL.md`](LAB_MANUAL.md)** — the complete step-by-step implementation manual (FastMCP server, 4 GCP tools, Cloud Run + GKE deploy, Agent Registry integration). Every command is copy-paste ready.

## 🔒 The AI Concept: MCP SERVERS THAT MEET ENTERPRISE SECURITY

**Day 2 deployed a secure MCP server on Cloud Run. Day 11 is the production-grade follow-up:** the same concept, hardened so an enterprise would actually trust it with real cloud permissions.

The Model Context Protocol (MCP) is *the* standard for letting AI agents access tools, databases, and enterprise context. But an MCP server that can touch Vertex AI and Cloud Storage is only as safe as its deployment. This lab answers: **how do you expose an MCP server so agents can use it, without handing out static credentials or leaving it open on the internet?**

Answer: **three layers of security**—
1. **Enforced IAM auth** (Cloud Run `--no-allow-unauthenticated`): no token → `401`.
2. **HTTPS/SSL everywhere** (managed certs on Cloud Run, Gateway API TLS + `nip.io` on GKE).
3. **Zero static keys** (Workload Identity: your pod *is* the service account).

## 🛠️ What you build
A **FastMCP server** (conforming to MCP Spec 2026-07-28, Streamable HTTP) with **four Google Cloud tools**:
- **Vertex AI Gemini** (`vertex_ai_generate_content`) — ask Gemini
- **Cloud Storage** (`gcs_bucket_inspector`) — inspect a bucket
- **Cloud Logging** (`cloud_logging_audit_writer`) — write audit entries
- **Health check** (`gcp_resource_health_checker`) — status (zero-dependency mock)

Then deploy it **twice** and register both in **Gemini Enterprise Agent Platform (Agent Registry)**:
- **Cloud Run** — serverless, IAM + managed SSL, manual `toolspec.json` registration
- **GKE Autopilot** — Workload Identity + Gateway API TLS, *automatic* Agent Registry discovery (no toolspec!)

## 🧩 Series arc
- **Day 2:** first MCP server, deployed to Cloud Run
- **Day 5:** consumed a managed BigQuery MCP server
- **Day 11 (today):** turn MCP into a *hardened, catalogued, enterprise-grade* tool your agents can discover and trust

## 📺 Video
**Watch:** [Day 11 — Secure MCP Server on GCP (Cloud Run + GKE)](https://youtu.be/myKbWJ5EefE) · 57:37

## 🗂️ Project files
- `LAB_MANUAL.md` — the full step-by-step manual
- `src/mcp_server/server.py` — FastMCP server + 4 tools (full source in manual §4)
- `src/mcp_server/test_client.py` — local test client (§5)
- `src/mcp_server/test_gcs_tool.py` — remote Cloud Run test client (§7)
- `src/mcp_server/test_vertex_tool.py` — GKE/HTTPS test client (§8)
- `src/mcp_server/test_agent_platform.py` — Agent Registry service-discovery client (§9)
- `Dockerfile` — multi-stage `uv` build (§6)
- `deployment.yaml` — GKE Deployment + Service (§8)
- `gateway.yaml` — Gateway API + HealthCheckPolicy + GCPBackendPolicy (§8)

## 🔑 Key takeaways
- FastMCP + MCP Spec **2026-07-28** = Streamable HTTP, strict `resultType`, stateless-friendly.
- **Test security, then function** on Cloud Run: verify `401` (unauth) before `200` (OIDC token).
- **Workload Identity** removes static SA keys — pods inherit cloud roles by identity.
- **GKE automatic MCP discovery** = no `toolspec.json`; label + annotate, GKE does the rest.
- **Session affinity** (CLIENT_IP) is mandatory for in-memory Streamable HTTP sessions on GKE.

## 🧹 Cleanup
All cleanup commands are in LAB_MANUAL §10 — delete the GKE cluster first (biggest cost), then Run service, SAs, Artifact Registry, Agent Registry service, bucket, IP + cert.