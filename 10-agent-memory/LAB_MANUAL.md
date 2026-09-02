# Visualize Your AI Assistant Memory with Gemini and Cloud SQL pgvector

## Complete Implementation Lab Manual

**Prepared by:** Abdul Qaadir (@TechWorldWithAbdul)
**Series:** 30 Labs, 30 Days — Day 10 · **Last Updated:** September 2026
**Original codelab:** [Visualize your AI assistant memory with Gemini and Cloud SQL pgvector](https://codelabs.developers.google.com/next26/postgres-visual-memory-agent)
**Author:** Billy Jacobson

---

## 1. Introduction

### Overview
Build the **Living Memory Demo** — an AI-powered assistant that tracks "memories" of your conversation to provide a personalized experience.

The app uses:
- **Gemini** (`gemini-2.5-flash` for extraction, `gemini-embedding-001` for vectors) for natural-language understanding
- **Cloud SQL for PostgreSQL** with the **pgvector** extension to store and retrieve memories by **semantic similarity**

A visualizer renders memories as color-coded nodes in a vector space, so you can *see* how the AI builds a personalized memory profile in real time.

### What you'll do
- Set up a Cloud SQL for PostgreSQL instance with `pgvector` support
- Use Gemini to interactively extract "memories" from user messages
- Perform vector searches in PostgreSQL to retrieve relevant context for AI responses
- Run a chat app with a live "AI memory" visualizer

### Cost
About 60 minutes · **less than $5 USD** · resources deletable after.

---

## 2. Before You Begin

### Setup
1. Create/select a Google Cloud project (billing enabled).
2. Start **Cloud Shell**, verify auth + project:
```bash
gcloud auth list
gcloud config get project
export PROJECT_ID=<YOUR_PROJECT_ID>
gcloud config set project $PROJECT_ID
```

### Enable APIs
```bash
gcloud services enable sqladmin.googleapis.com \
                       aiplatform.googleapis.com
```

---

## 3. Clone the Demo Repository

```bash
git clone https://github.com/GoogleCloudPlatform/devrel-demos.git
cd devrel-demos/codelabs/visual-memory-postgres-demo
npm install
```

---

## 4. Create and Configure the Cloud SQL Database

### Set environment variables
```bash
export REGION="us-central1"
export INSTANCE_NAME="living-memory-db"
export DB_HOST=127.0.0.1
export DB_PORT=5432
export DB_USER=memory_app
export DB_PASS=memory_app_password
export DB_NAME=living_memory
export PGPASSWORD=$DB_PASS
```

### Create the instance (takes 5-10 min)
```bash
gcloud sql instances create $INSTANCE_NAME \
    --database-version=POSTGRES_16 \
    --cpu=1 \
    --memory=3840MB \
    --region=$REGION \
    --root-password=$DB_PASS \
    --edition=ENTERPRISE
```

### Database schema (understand it)
The `schema.sql` enables the `vector` extension and creates tables:
- **`users` / `conversations` / `messages`** — user profiles + conversation history.
- **`memories`** — the core RAG table. Each row = a piece of info extracted from conversation (e.g. "User likes hiking"). Stores:
  - `content`: the memory text
  - `memory_type`: `FACT`, `PREF`, or `IMPLICIT`
  - `embedding`: a 768-dim `vector` (semantic representation via Gemini)
- **pgvector HNSW index** on the `embedding` column — optimizes k-NN searches via the cosine-distance operator (`<=>`).

### Create DB + app user
```bash
gcloud sql databases create $DB_NAME --instance=$INSTANCE_NAME
gcloud sql users create $DB_USER --instance=$INSTANCE_NAME --password=$DB_PASS
```

### Start the Cloud SQL Auth Proxy
Provides secure access without IP allowlisting:
```bash
(cloud-sql-proxy ${GOOGLE_CLOUD_PROJECT}:us-central1:living-memory-db &) && sleep 2 && echo ""
```
You should see: `The proxy has started successfully and is ready for new connections!`

### Apply the schema
```bash
psql -h 127.0.0.1 -U $DB_USER -d $DB_NAME < schema.sql
psql -h 127.0.0.1 -U $DB_USER -d $DB_NAME -c "\dt"
```
You should see: `conversations`, `memories`, `messages`, `queries_log`, `users`.

---

## 5. Semantic Retrieval with pgvector

In `server.js`, the `/api/chat` endpoint retrieves relevant memories before generating a response:
```javascript
// Retrieve Similar Memories for Context (Using pgvector)
const promptEmbeddingRes = await ai.models.embedContent({
  model: 'gemini-embedding-001',
  contents: message,
  config: { outputDimensionality: 768 },
});
const promptEmbedding = promptEmbeddingRes.embeddings[0].values;
const embeddingStr = `[${promptEmbedding.join(',')}]`;

// Query DB for top 5 closest memories
const relevantMemories = await pool.query(
  `SELECT id, content, memory_type, category
   FROM memories
   WHERE user_id = $1
   ORDER BY embedding <=> $2::vector
   LIMIT 5`,
  [userId, embeddingStr]
);
```

**How it works (RAG):**
1. **Embedding:** the user's message → `gemini-embedding-001` → 768-dim vector (semantic meaning).
2. **pgvector:** pass that vector to Cloud SQL; the `<=>` cosine-distance operator finds the **5 most semantically similar memories**.
3. **Result:** The AI gets only the *relevant* memories to personalize its response — without loading the entire history.

---

## 6. Memory Extraction

In `extractMemoriesAsync` (`server.js`):
```javascript
async function extractMemoriesAsync(userMessage, userId, messageId) {
  const extractionPrompt = `
    Analyze the following user message. A memory profile is being built for this user.
    Extract ANY explicit facts (Facts), preferences (Pref), or implicit behavioral traits/styles (Implicit).
    Return the result as a raw JSON array of objects (NO Markdown blocks, just the JSON array).
    Format: [{"content": "string fact/sentence", "type": "FACT|PREF|IMPLICIT", "category": "General|Travel|Hobby|Persona"}]
    If nothing is found, return [].
    Message: "${userMessage}"
    `;
  const result = await ai.models.generateContent({
    model: 'gemini-2.5-flash',
    contents: extractionPrompt
  });
  let rawJson = result.text.replace(/^```json/g, '').replace(/```$/g, '').trim();
  let extracted;
  try { extracted = JSON.parse(rawJson); } catch (e) { return; }
  if (Array.isArray(extracted) && extracted.length > 0) {
    for (const memory of extracted) {
      const embedRes = await ai.models.embedContent({
        model: 'gemini-embedding-001',
        contents: memory.content,
        config: { outputDimensionality: 768 },
      });
      const vectorData = `[${embedRes.embeddings[0].values.join(',')}]`;
      await pool.query(
        `INSERT INTO memories (user_id, content, memory_type, category, embedding, source_message_id)
                 VALUES ($1, $2, $3, $4, $5, $6)`,
        [userId, memory.content, memory.type.toUpperCase(), memory.category, vectorData, messageId]
      );
    }
  }
}
```

**How it works:**
1. **Gemini (structured output):** `gemini-2.5-flash` analyzes the message → JSON array of facts/preferences (FACT / PREF / IMPLICIT, with category).
2. **Cloud SQL (hybrid storage):** each extracted fact is embedded, then stored — relational data (user id, text, category) sits right alongside the vector data in one row.
3. **Result:** a self-updating, real-time memory profile — Gemini's analysis + Cloud SQL's storage.

---

## 7. Run the Chat Application

1. **Seed example users:**
```bash
npm run seed
```
2. **Run the server:**
```bash
node server.js
```
3. Click **Web Preview** → **Change Port** → enter **3000** → **Change and Preview**.

### Interact with the assistant
- On the right, the **AI Cortex Data Visualizer** shows memories as nodes in a vector space, color-coded by type (Fact / Preference / Implicit Trait). Zoom/pan to inspect.
- **Query existing memories:** select a seeded user, ask *"Give me restaurant recommendations in New York City"*. Click the assistant's reply to see which memories it used (highlighted green), and zoom to them to see how they shaped the response.
- **Create a new user:** click **+** → name/description → **Create**. In ~30 seconds, new memory nodes appear (Gemini extracted facts from your message, stored in Cloud SQL). Ask *"What food do I like?"* to see it use the new memories.

---

## 8. Clean Up

```bash
gcloud sql instances delete $INSTANCE_NAME --quiet
rm -rf ~/devrel-demos
```

---

## Key Takeaways
- **Cloud SQL pgvector** = PostgreSQL + vector search in a fully managed GCP database.
- **RAG retrieval** = embed the query (`gemini-embedding-001`, 768-dim) → `ORDER BY embedding <=> $2::vector LIMIT 5` (cosine distance, HNSW-indexed).
- **Dynamic memory extraction** = `gemini-2.5-flash` pulls structured FACTS / PREFs / IMPLICIT traits as JSON, each embedded and stored.
- **Hybrid storage** = relational columns (user/text/category) + high-dim vector live in the same row.
- **Visual feedback** = color-coded memory nodes show exactly how the AI builds a persona — great for explaining RAG + memory to non-experts.

## Next Steps
- Explore [Cloud SQL pgvector docs](https://cloud.google.com/sql/docs/postgres/work-with-vectors)
- Learn more about [Gemini API capabilities](https://ai.google.dev/docs)
- Deep dive into [Cloud SQL Auth Proxy](https://cloud.google.com/sql/docs/postgres/sql-proxy)
- Customize the `extractionPrompt` in `server.js` to extract different data types

*(Built from the original Google Cloud codelab by Billy Jacobson.)*