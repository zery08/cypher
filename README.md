# Graph Chat Workspace

Chat-first Neo4j exploration app built with a React frontend and a FastAPI backend.

## Structure

- `frontend/`: React + JavaScript + Vite client
- `backend/`: FastAPI + `uv` backend with Neo4j and LLM orchestration

## Backend

```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload
```

Create `backend/.env` first. The backend reads z.ai credentials directly:

```env
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=wafergraph123
ZAI_API_KEY=your-zai-api-key
ZAI_MODEL=glm-4.7
CORS_ORIGINS=http://localhost:5173
```

By default the backend uses z.ai's OpenAI-compatible endpoint:
`https://api.z.ai/api/paas/v4`

`ZAI_BASE_URL` is optional. The generic `LLM_*` aliases still work if you want a different compatible provider.

## Neo4j Demo Data

Spin up Neo4j and seed the wafer graph:

```bash
bash scripts/setup_neo4j.sh
```

This creates demo nodes and relationships with this shape:

- `(:Wafer {wafer_id, lot_id, product, process_step, status})`
- `(:Recipe {recipe_id, name, process_family, tool_id, chamber})`
- `(:Metrology {metrology_id, metric, value, unit, site, tool, measured_at})`
- `(Wafer)-[:USES_RECIPE]->(Recipe)`
- `(Wafer)-[:HAS_METROLOGY]->(Metrology)`

Useful sample Cypher:

```cypher
MATCH (w:Wafer)-[:USES_RECIPE]->(r:Recipe)
RETURN w, r
LIMIT 10;
```

```cypher
MATCH (w:Wafer {wafer_id: "WAF-B2102"})-[:HAS_METROLOGY]->(m:Metrology)
RETURN w, m
LIMIT 10;
```

## Frontend

```bash
cd frontend
npm install
npm run dev
```

## What It Does

- Uses the chat panel as the primary input surface
- Lets the backend decide when Neo4j data is required
- Generates read-only Cypher via z.ai glm-4.7 when database lookup is needed
- Shows the latest Cypher and graph result on the left side
- Lets users attach selected nodes and edges into follow-up chat turns
