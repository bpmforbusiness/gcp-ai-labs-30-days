# Getting Started with Vector Embeddings with AlloyDB AI

## Complete Implementation Lab Manual

**Prepared by:** Abdul Qaadir (@TechWorldWithAbdul)
**Series:** 30 Labs, 30 Days — Day 9 · **Last Updated:** August 2026
**Original codelab:** [Getting started with Vector Embeddings with AlloyDB AI](https://codelabs.developers.google.com/alloydb-ai-embedding)
**Author:** Gleb Otochkin

---

## 1. Introduction

### Overview
In this codelab you'll use **AlloyDB AI** by combining **vector search** with **Vertex AI / Gemini embeddings**. You'll deploy a real AlloyDB database, load product/inventory/store data, generate vector embeddings from product descriptions, run a **semantic similarity search**, enrich the result with a **generative LLM**, and speed it up with a **vector index**.

This is the RAG/embedding lab — the memory-and-retrieval side of agents (connects to Days 2, 5, and the RAG Day 1 coffee barista!).

### What you'll learn
- Deploy an **AlloyDB cluster** and **primary instance**
- Connect to AlloyDB from a **Compute Engine (GCE) VM**
- Create a database and enable **AlloyDB AI**
- Load data into the database
- Use **AlloyDB Studio** (web query interface)
- Use the **Gemini Enterprise Agent Platform embedding model** in AlloyDB
- Enrich results with a **generative LLM**
- Improve performance with a **vector index** (ScaNN)

### Cost
LESS THAN $3 USD in Cloud resources. New users get the $300 Free Trial.

---

## 2. Setup and Requirements

### Project Setup
1. Sign in to the [Google Cloud Console](http://console.cloud.google.com/) (use a personal Gmail/Workspace account, not work/school).
2. Create a new project (or reuse one). Header → **Select a project** → **New Project**. Note your **Project ID** (immutable, unique — referenced as `PROJECT_ID`).

### Enable Billing
- Use Google Cloud credits, or enable billing at console.cloud.google.com/billing.

### Start Cloud Shell
From the console, click the **Cloud Shell** icon (top-right toolbar), or press **G** then **S**, or go to [shell.cloud.google.com](https://shell.cloud.google.com/?show=terminal).
~5GB persistent home, all tools preinstalled — everything in this lab runs in the browser.

---

## 3. Before You Begin — Enable APIs

```bash
gcloud config set project [YOUR-PROJECT-ID]
PROJECT_ID=$(gcloud config get-value project)
gcloud services enable alloydb.googleapis.com \
                       compute.googleapis.com \
                       cloudresourcemanager.googleapis.com \
                       servicenetworking.googleapis.com \
                       aiplatform.googleapis.com
```
These enable: AlloyDB, Compute Engine, Networking (VPC peering), and Gemini Enterprise Agent Platform / Vertex AI.

---

## 4. Deploy AlloyDB

### Create a private IP range
AlloyDB is private-only. Allocate a private IP range in your VPC (the "default" network):
```bash
gcloud compute addresses create psa-range \
    --global \
    --purpose=VPC_PEERING \
    --prefix-length=24 \
    --description="VPC private service access" \
    --network=default
```
Create the private connection using that range:
```bash
gcloud services vpc-peerings connect \
    --service=servicenetworking.googleapis.com \
    --ranges=psa-range \
    --network=default
```

### Create AlloyDB cluster + instance
Generate a postgres password (note it — you'll need it later):
```bash
export PGPASSWORD=`openssl rand -hex 16`
echo $PGPASSWORD   # save this!
```
Set region + cluster name env vars:
```bash
export REGION=us-central1
export ADBCLUSTER=alloydb-aip-01
```

**If your first AlloyDB cluster (free trial):**
```bash
gcloud alloydb clusters create $ADBCLUSTER \
    --password=$PGPASSWORD \
    --network=default \
    --region=$REGION \
    --subscription-type=TRIAL
```

**If NOT your first cluster (standard):**
```bash
gcloud alloydb clusters create $ADBCLUSTER \
    --password=$PGPASSWORD \
    --network=default \
    --region=$REGION
```

**Create the primary instance** (trial: `--cpu-count=8`; standard: `--cpu-count=2`):
```bash
gcloud alloydb instances create $ADBCLUSTER-pr \
    --instance-type=PRIMARY \
    --cpu-count=8 \
    --region=$REGION \
    --cluster=$ADBCLUSTER
```
*(If your Cloud Shell disconnects, re-define `REGION` and `ADBCLUSTER`.)*

---

## 5. Connect to AlloyDB from a GCE VM

AlloyDB is private-only, so you need a Compute Engine VM in the same region/VPC to reach it via psql.

### Deploy a GCE VM
```bash
export ZONE=us-central1-a
gcloud compute instances create instance-1 \
    --zone=$ZONE \
    --create-disk=auto-delete=yes,boot=yes,image=projects/debian-cloud/global/images/$(gcloud compute images list --filter="family=debian-13 AND family!=debian-13-arm64" --format="value(name)") \
    --scopes=https://www.googleapis.com/auth/cloud-platform
```

### Install the PostgreSQL client (inside the VM)
```bash
gcloud compute ssh instance-1 --zone=us-central1-a
# now INSIDE the VM:
sudo apt-get update
sudo apt-get install --yes postgresql-client
```

### Connect to the primary instance
In the SSH session, set your noted password + the instance IP:
```bash
export PGPASSWORD=<Noted password>
export PROJECT_ID=$(gcloud config get-value project)
export REGION=us-central1
export ADBCLUSTER=alloydb-aip-01
export INSTANCE_IP=$(gcloud alloydb instances describe $ADBCLUSTER-pr --cluster=$ADBCLUSTER --region=$REGION --format="value(ipAddress)")
psql "host=$INSTANCE_IP user=postgres sslmode=require"
```
You'll land at the `postgres=>` prompt. Type `exit` to close.

---

## 6. Prepare the Database

### Grant Gemini permissions to AlloyDB
Open a **new Cloud Shell tab** (use the "+") and run:
```bash
PROJECT_ID=$(gcloud config get-value project)
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:service-$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")@gcp-sa-alloydb.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"
```
Then `exit` that tab.

### Create the database (in the VM SSH session)
```bash
psql "host=$INSTANCE_IP user=postgres" -c "CREATE DATABASE quickstart_db"
```

### Enable Vertex AI integration + pgvector
```bash
psql "host=$INSTANCE_IP user=postgres dbname=quickstart_db" -c "CREATE EXTENSION IF NOT EXISTS google_ml_integration CASCADE"
psql "host=$INSTANCE_IP user=postgres dbname=quickstart_db" -c "CREATE EXTENSION IF NOT EXISTS vector"
```

### Import data
```bash
gcloud storage cat gs://cloud-training/gcc/gcc-tech-004/cymbal_demo_schema.sql |psql "host=$INSTANCE_IP user=postgres dbname=quickstart_db"
gcloud storage cat gs://cloud-training/gcc/gcc-tech-004/cymbal_products.csv |psql "host=$INSTANCE_IP user=postgres dbname=quickstart_db" -c "\copy cymbal_products from stdin csv header"
gcloud storage cat gs://cloud-training/gcc/gcc-tech-004/cymbal_inventory.csv |psql "host=$INSTANCE_IP user=postgres dbname=quickstart_db" -c "\copy cymbal_inventory from stdin csv header"
gcloud storage cat gs://cloud-training/gcc/gcc-tech-004/cymbal_stores.csv |psql "host=$INSTANCE_IP user=postgres dbname=quickstart_db" -c "\copy cymbal_stores from stdin csv header"
```
You now have `cymbal_products` (~941), `cymbal_inventory` (~263k), `cymbal_stores` (~4.6k).

---

## 7. Calculate Embeddings

Connect to the DB:
```bash
psql "host=$INSTANCE_IP user=postgres dbname=quickstart_db"
```

### Verify the extension version + flag
```sql
SELECT extversion FROM pg_extension WHERE extname = 'google_ml_integration';
-- should be 1.5.2 / 1.6 + 
show google_ml_integration.enable_faster_embedding_generation;
-- should be 'on'
```
If the flag is `off`, enable it (gcloud):
```bash
export PROJECT_ID=$(gcloud config get-value project)
export REGION=us-central1
export ADBCLUSTER=alloydb-aip-01
gcloud beta alloydb instances update $ADBCLUSTER-pr \
   --database-flags google_ml_integration.enable_faster_embedding_generation=on \
   --region=$REGION --cluster=$ADBCLUSTER --project=$PROJECT_ID --update-mode=FORCE_APPLY
```
*(Note: `google_ml_integration` is the extension that powers both embeddings and the LLM integration — the lab text sometimes calls it "Google ML integration".)*

### Add an embedding column + generate embeddings
```sql
ALTER TABLE cymbal_products ADD COLUMN embedding vector(768);
\timing
CALL ai.initialize_embeddings(
    model_id => 'text-embedding-005',
    table_name => 'cymbal_products',
    content_column => 'product_description',
    embedding_column => 'embedding',
    batch_size => 50
);
```
(Typically <2 seconds for 941 products with fast embedding generation.)

### Auto-refresh embeddings (optional)
Create a second column that auto-updates on data changes:
```sql
ALTER TABLE cymbal_products ADD COLUMN product_embedding vector(768);
CALL ai.initialize_embeddings(
    model_id => 'text-embedding-005',
    table_name => 'cymbal_products',
    content_column => 'product_description',
    embedding_column => 'product_embedding',
    batch_size => 50,
    incremental_refresh_mode => 'transactional'
);
```

---

## 8. Run a Similarity Search

Run a semantic query: find products in store 1583 most closely related to *"What kind of fruit trees grow well here?"* using the **`<=>` cosine-distance operator**:
```sql
SELECT
        cp.product_name,
        left(cp.product_description,80) as description,
        cp.sale_price,
        cs.zip_code,
        (cp.embedding <=> embedding('text-embedding-005','What kind of fruit trees grow well here?')::vector) as distance
FROM
        cymbal_products cp
JOIN cymbal_inventory ci on
        ci.uniq_id=cp.uniq_id
JOIN cymbal_stores cs on
        cs.store_id=ci.store_id
        AND ci.inventory>0
        AND cs.store_id = 1583
ORDER BY
        distance ASC
LIMIT 10;
```
Result (ordered by semantic distance, most similar first): **Cherry Tree**, Meyer Lemon Tree, Toyon, California Lilac, Peppertree, Walnut, Sycamore, Live Oak, Cottonwood, Madrone.

### Alternative: AlloyDB Studio (web UI)
1. Console → **Clusters** page → select your primary instance.
2. Click **AlloyDB Studio** on the left.
3. Select `quickstart_db`, user `postgres`, enter the noted password → **Authenticate**.
4. Open an **Untitled Query** tab and run SQL there (better for multi-row output).

---

## 9. Improve the Response with a Generative LLM

Convert the top vector results into JSON, then feed that JSON to a Gemini model as part of a prompt.

### Step 1 — Query returns JSON
```sql
WITH trees as (
SELECT
        cp.product_name,
        left(cp.product_description,80) as description,
        cp.sale_price,
        cs.zip_code,
        cp.uniq_id as product_id
FROM
        cymbal_products cp
JOIN cymbal_inventory ci on
        ci.uniq_id=cp.uniq_id
JOIN cymbal_stores cs on
        cs.store_id=ci.store_id
        AND ci.inventory>0
        AND cs.store_id = 1583
ORDER BY
        (cp.embedding <=> embedding('text-embedding-005','What kind of fruit trees grow well here?')::vector) ASC
LIMIT 1)
SELECT json_agg(trees) FROM trees;
```
Outputs: `[{"product_name":"Cherry Tree","description":"...","sale_price":75.00,"zip_code":93230,"product_id":"..."}]`

### Step 2 — Test in Gemini Enterprise Agent Platform Studio
Open [Agent Platform Studio](https://console.cloud.google.com/agent-platform/studio) and prompt:
> "You are a friendly advisor helping to find a product based on the customer's needs. Based on the client request we have loaded a list of products closely related to search. The list in JSON format... Here is the list of products: [JSON]. The customer asked 'What tree is growing the best here?' You should give information about the product, price and some supplemental information."

The model returns a friendly, complete answer with price + supplemental info.

### Step 3 — Do it all in SQL (register the LLM model first)
Register `gemini-3.6-flash`:
```sql
CALL google_ml.create_model(
model_id => 'gemini-3.6-flash',
model_request_url => 'https://aiplatform.googleapis.com/v1/projects/PROJECT_ID/locations/global/publishers/google/models/gemini-3.6-flash:generateContent',
model_provider => 'google',
model_type => 'llm'
);
```
Then run the full RAG pipeline in one query — vector search → JSON → gemini prompt → answer:
```sql
WITH trees AS (
SELECT
        cp.product_name, cp.product_description AS description,
        cp.sale_price, cs.zip_code, cp.uniq_id AS product_id
FROM cymbal_products cp
JOIN cymbal_inventory ci ON ci.uniq_id = cp.uniq_id
JOIN cymbal_stores cs ON cs.store_id = ci.store_id
        AND ci.inventory>0 AND cs.store_id = 1583
ORDER BY (cp.embedding <=> embedding('text-embedding-005',
        'What kind of fruit trees grow well here?')::vector) ASC
LIMIT 1),
prompt AS (
SELECT 'You are a friendly advisor helping to find a product based on the customer''s needs.
Based on the client request we have loaded a list of products closely related to search.
The list in JSON format... Here is the list of products:' || json_agg(trees) || 'The customer asked "What kind of fruit trees grow well here?"
You should give information about the product, price and some supplemental information' AS prompt_text
FROM trees),
response AS (
SELECT google_ml.predict_row( model_id =>'gemini-3.6-flash',
        request_body => json_build_object('contents',
        json_build_object('role','user','parts', json_build_object('text', prompt_text))))->'candidates'->0->'content'->'parts'->0->'text' AS resp
FROM prompt)
SELECT REPLACE(resp::text, '\n', CHR(10)) FROM response;
```
→ The model returns a friendly recommendation (e.g., the Cherry Tree with price, benefits, and growing requirements).

---

## 10. Create a Vector Index (ScaNN) for Performance

With millions of vectors, vector search adds latency. Build an **Approximate Nearest Neighbor (ANN)** index using Google's **ScaNN** algorithm.

Enable the extension:
```sql
CREATE EXTENSION IF NOT EXISTS alloydb_scann;
```
Create a MANUAL ScaNN index:
```sql
CREATE INDEX cymbal_products_embeddings_scann ON cymbal_products
  USING scann (embedding cosine)
  WITH (num_leaves=10, max_num_levels = 1);
```
Re-run the similarity query — same result ("Cherry Tree"), and verify the index is used:
```sql
EXPLAIN (analyze)
WITH trees AS ( <same selection query> )
SELECT json_agg(trees) FROM trees;
```

---

## 11. Clean Up

1. **Delete the AlloyDB cluster** (Cloud console → AlloyDB → select cluster → delete) — deletes cluster + instances.
2. **Delete AlloyDB backups** (AlloyDB → Backups → delete).
3. **Delete the GCE VM** (`gcloud compute instances delete instance-1 --zone=us-central1-a`, or console → Compute Engine → delete).
4. *(Optional) Delete the whole project to stop all billing.*

---

## Key Takeaways
- **AlloyDB AI** = PostgreSQL + vectors + Vertex AI embeddings + generation, all inside SQL.
- Enable `google_ml_integration` (embeddings, ML, LLM) and `vector` (pgvector) extensions.
- Embeddings generated with `ai.initialize_embeddings(model_id => 'text-embedding-005', ...)` on a `vector(768)` column.
- **Similarity search** = `embedding <=> embedding('text-embedding-005', 'query')` (cosine distance), ordered ascending.
- **RAG in one query** — combine vector top-k (as JSON) + a registered LLM (`google_ml.predict_row`) to produce a natural-language answer directly from the DB.
- **ScaNN vector index** (`alloydb_scann`) speeds up ANN search at scale.
- The `enable_faster_embedding_generation` database flag must be `on` for fast batch embeddings.