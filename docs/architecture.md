# Architecture: Mutual Fund FAQ Assistant

> **Reference**: [problemStatement.md](file:///Users/gkondave/Documents/Python/Agents/Antigravity/RAG-Chatbot/docs/problemStatement.md)

---

## 1. High-Level Architecture

```mermaid
flowchart TB
    subgraph SCHEDULER ["⏰ GitHub Actions Scheduler (Daily 10 AM IST)"]
        SA["Cron Trigger\n(4:30 AM UTC)"] -->|POST /api/ingest/refresh| SB["Railway Backend\nIngestion Endpoint"]
    end

    subgraph BACKEND ["🖥️ Backend API · Railway"]
        subgraph INGESTION ["📥 Data Ingestion Pipeline"]
            A["Groww Scheme URLs\n(5 HDFC Funds)"] -->|Playwright| B["Web Scraper"]
            B -->|Raw HTML| C["Content Extractor\n& Cleaner"]
            C -->|Structured Text| D["Chunking Engine\n(RecursiveCharacterTextSplitter)"]
            D -->|Chunks + Metadata| E["Embedding Model\n(bge-large-en-v1.5)"]
            E -->|Vectors + Metadata| F[("ChromaDB\nPersistent Volume")]
        end

        subgraph RUNTIME ["🤖 Query Pipeline (Real-Time)"]
            G["POST /api/query"] --> H["PII & Guardrail Filter"]
            H -->|Clean Query| I["Query Embedder\n(bge-large-en-v1.5)"]
            I -->|Query Vector| J["Similarity Search\n(ChromaDB)"]
            J -->|Top-K Chunks + Metadata| K["Prompt Builder\n(Facts-Only System Prompt)"]
            K -->|Augmented Prompt| L["Groq LLM\n(GPT-OSS 120B)"]
            L -->|Raw Response| M["Response Formatter\n(3 sentences + citation + footer)"]
            M --> N["JSON Response"]
        end

        F -.->|Retrieved Context| J
        SB --> A
    end

    subgraph FRONTEND ["🌐 Frontend · Vercel"]
        O["Chat UI\n(HTML / CSS / JS)"] -->|POST /api/query| G
        N -->|JSON| O
    end
```

---

## 2. Technology Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| **LLM** | Groq API (`openai/gpt-oss-120b`) | Ultra-low-latency inference via Groq LPU; GPT-OSS 120B for strong reasoning and instruction-following |
| **Embeddings** | `BAAI/bge-large-en-v1.5` | High-quality 1024-dim embeddings; top-tier retrieval accuracy; runs locally via sentence-transformers |
| **Vector Store** | ChromaDB (persistent, Railway volume) | Zero-config, file-based; persistent across Railway deployments via mounted volume |
| **Web Scraping** | Playwright + BeautifulSoup4 | Playwright handles Groww's JS-rendered pages; BS4 for HTML parsing |
| **Orchestration** | LangChain | Composable chains for retrieval, prompt building, and LLM calls |
| **Backend API** | FastAPI + Uvicorn | Async Python API server; auto-generated OpenAPI docs; Railway-compatible |
| **Frontend** | HTML / CSS / JavaScript | Minimal static chat UI; deployed on Vercel CDN |
| **Scheduler** | GitHub Actions (cron) | Daily 10 AM IST ingestion trigger; free for public repos |
| **Backend Hosting** | Railway | Persistent volumes for ChromaDB; Docker/Nixpacks deploys; environment variables |
| **Frontend Hosting** | Vercel | Static site hosting; global CDN; zero-config deploys from Git |
| **Language** | Python 3.11+ (backend), JavaScript (frontend) | Ecosystem maturity for ML/NLP + lightweight browser UI |

---

## 3. Data Ingestion Pipeline

### 3.1 Corpus & Source Model

All data is sourced exclusively from the **5 Groww scheme URLs**. Each URL serves as a single, self-contained source document.

| # | Scheme | Source URL | Category |
|---|--------|-----------|----------|
| 1 | HDFC Mid Cap Fund | `https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth` | Mid Cap |
| 2 | HDFC Small Cap Fund | `https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth` | Small Cap |
| 3 | HDFC Gold ETF FoF | `https://groww.in/mutual-funds/hdfc-gold-etf-fund-of-fund-direct-plan-growth` | Gold / Commodity |
| 4 | HDFC Large Cap Fund | `https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth` | Large Cap |
| 5 | HDFC ELSS Tax Saver Fund | `https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth` | ELSS / Tax Saving |

### 3.2 Scraping Strategy

```mermaid
flowchart LR
    A["Groww URL"] --> B["Playwright\n(headless Chrome)"]
    B -->|Wait for JS render| C["Full DOM Snapshot"]
    C --> D["BeautifulSoup4\nExtract Sections"]
    D --> E["Structured Sections"]

    E --> E1["Fund Overview"]
    E --> E2["Returns & NAV"]
    E --> E3["Fund Details\n(Expense, Exit Load, etc.)"]
    E --> E4["Holdings"]
    E --> E5["Peer Comparison*"]

    style E5 stroke-dasharray: 5 5
```

**Key extraction targets per scheme page:**

| Section | Data Points Extracted |
|---------|----------------------|
| Fund Overview | Fund name, category, sub-category, AMC name, fund manager |
| Fund Details | Expense ratio, exit load, minimum SIP/lumpsum, lock-in period, benchmark index, riskometer |
| NAV & AUM | Latest NAV, AUM, NAV date |
| Tax Information | STCG/LTCG tax rates, ELSS lock-in |
| General Info | Fund house, inception date, plan type (Direct/Regular) |

> **Note**: Returns, performance comparisons, and peer data are **scraped but tagged as non-answerable** to comply with the "no performance advice" constraint. They are stored only for future extensibility and are excluded from retrieval.

### 3.3 Content Cleaning

```python
# Pseudocode for content cleaning
def clean_content(raw_html: str, source_url: str) -> list[Document]:
    """
    1. Strip navigation, footers, ads, modals
    2. Normalize whitespace and encoding
    3. Extract section headings as metadata
    4. Attach source_url and scrape_date to each section
    """
```

**PII Scrubbing**: The scraper validates that no PII (PAN, Aadhaar, account numbers, emails, phone numbers) exists in scraped content. Any detected PII patterns are stripped before storage.

### 3.4 Chunking Strategy

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| **Splitter** | `RecursiveCharacterTextSplitter` | Preserves paragraph and sentence boundaries |
| **Chunk Size** | 500 characters | Small enough for precise retrieval of individual facts |
| **Chunk Overlap** | 50 characters | Prevents context loss at boundaries |
| **Metadata per Chunk** | `scheme_name`, `section`, `source_url`, `scrape_date` | Enables filtered retrieval and citation generation |

**Expected corpus size**: ~5 URLs × ~8 sections × ~2-3 chunks/section ≈ **80–120 chunks total**

### 3.5 Embedding & Storage

```mermaid
flowchart LR
    A["Text Chunks\n+ Metadata"] --> B["BAAI/bge-large-en-v1.5\n(1024-dim)"]
    B --> C["Embedding Vectors"]
    C --> D[("ChromaDB\nPersistent Collection\n'mf_facts'")]
    A -->|Metadata| D
```

| Config | Value |
|--------|-------|
| **Model** | `BAAI/bge-large-en-v1.5` |
| **Embedding Dimension** | 1024 |
| **Distance Metric** | Cosine similarity |
| **Collection Name** | `mf_facts` |
| **Persistence** | `$CHROMA_PERSIST_DIR` (Railway volume mount) |

---

## 4. Query Pipeline (Runtime)

### 4.1 End-to-End Query Flow

```mermaid
sequenceDiagram
    actor User
    participant FE as Frontend (Vercel)
    participant API as FastAPI (Railway)
    participant Guard as Guardrail Layer
    participant Embed as Embedding Model
    participant VDB as ChromaDB
    participant Prompt as Prompt Builder
    participant LLM as Groq API (GPT-OSS 120B)
    participant Fmt as Response Formatter

    User->>FE: "What is the expense ratio of HDFC Mid Cap Fund?"
    FE->>API: POST /api/query
    API->>Guard: Validate query
    Guard->>Guard: PII check ✓
    Guard->>Guard: Advisory check ✓
    Guard->>Embed: Clean query
    Embed->>VDB: Query vector (top-k=3)
    VDB-->>Prompt: Retrieved chunks + metadata
    Prompt->>LLM: System prompt + Context + Query
    LLM-->>Fmt: Raw LLM response
    Fmt-->>API: Formatted response
    API-->>FE: JSON (3 sentences + citation + footer)
    FE-->>User: Display answer
```

### 4.2 Guardrail Layer

The guardrail layer runs **before** retrieval and acts as a gate for every incoming query.

```mermaid
flowchart TD
    Q["User Query"] --> PII{"Contains PII?\n(PAN/Aadhaar/Phone/Email)"}
    PII -->|Yes| R1["🚫 Refusal:\n'I cannot process personal information.\nPlease do not share PII.'"]
    PII -->|No| ADV{"Advisory Intent?\n(keyword + semantic check)"}
    ADV -->|Yes| R2["🚫 Refusal:\n'I provide facts only, not investment advice.\nVisit amfiindia.com for guidance.'"]
    ADV -->|No| SCOPE{"In-Scope?\n(relates to HDFC schemes)"}
    SCOPE -->|No| R3["🚫 Refusal:\n'I can only answer questions about\nthe 5 HDFC mutual fund schemes.'"]
    SCOPE -->|Yes| PASS["✅ Proceed to Retrieval"]
```

**Advisory Detection Keywords**:
```
should, recommend, suggest, better, best, compare returns,
which fund, invest in, buy, sell, hold, prediction, forecast
```

**PII Detection Patterns** (regex):
```
PAN:     [A-Z]{5}[0-9]{4}[A-Z]
Aadhaar: \b\d{4}\s?\d{4}\s?\d{4}\b
Phone:   \b[6-9]\d{9}\b
Email:   \b[\w.-]+@[\w.-]+\.\w+\b
```

### 4.3 Retrieval Configuration

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| **Search Type** | Similarity search (cosine) | Standard semantic retrieval |
| **Top-K** | 3 | Small corpus; 3 chunks provide sufficient context without noise |
| **Metadata Filter** | Optional `scheme_name` filter | Applied when query explicitly mentions a fund name |
| **Score Threshold** | 0.35 (minimum similarity) | Prevents hallucination from irrelevant chunks |

### 4.4 Groq LLM Configuration

| Parameter | Value |
|-----------|-------|
| **Provider** | Groq Cloud API |
| **Model** | `openai/gpt-oss-120b` |
| **Temperature** | 0.0 (deterministic, factual) |
| **Max Tokens** | 256 |
| **API Key** | Stored in Railway env vars (`GROQ_API_KEY`) |

**Why Groq?**
- **Speed**: ~10x faster inference than traditional cloud LLM APIs (LPU architecture)
- **Cost**: Generous free tier suitable for FAQ-scale traffic
- **Quality**: GPT-OSS 120B offers strong reasoning and instruction-following for constrained factual tasks

### 4.5 Prompt Engineering

```text
SYSTEM PROMPT:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
You are a facts-only mutual fund FAQ assistant for HDFC mutual fund schemes
available on Groww. You must follow these rules strictly:

RULES:
1. Answer ONLY using the provided context. Do NOT use prior knowledge.
2. Respond in a MAXIMUM of 3 sentences.
3. Include EXACTLY ONE source citation URL from the context metadata.
4. Append this footer to every response:
   "Last updated from sources: {scrape_date}"
5. If the context does not contain the answer, respond:
   "I don't have this information in my current data. Please visit
   {source_url} for the latest details."
6. NEVER provide investment advice, opinions, recommendations, or
   performance comparisons.
7. If the user asks for advice or comparisons, politely refuse and direct
   them to https://www.amfiindia.com/investor-corner/knowledge-center

CONTEXT:
{retrieved_chunks}

USER QUERY:
{user_query}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 4.6 Response Formatter

Every LLM response passes through a post-processor that enforces the output contract:

```mermaid
flowchart LR
    A["Raw LLM Output"] --> B["Sentence Counter\n(max 3)"]
    B --> C["Citation Validator\n(exactly 1 URL)"]
    C --> D["Footer Appender\n('Last updated from sources: date')"]
    D --> E["Final Response"]
```

| Rule | Enforcement |
|------|-------------|
| ≤ 3 sentences | Truncate at 3rd sentence boundary if exceeded |
| 1 citation link | Extract from chunk metadata; inject if missing |
| Footer | Always appended from `scrape_date` metadata |

---

## 5. Refusal Handling

### 5.1 Refusal Categories & Responses

| Category | Trigger | Response Template |
|----------|---------|-------------------|
| **Advisory** | Keywords: *should, recommend, better, best, compare* | "I'm a facts-only assistant and cannot provide investment advice or recommendations. For investment guidance, please visit [AMFI Investor Corner](https://www.amfiindia.com/investor-corner/knowledge-center)." |
| **PII Detected** | Regex match for PAN/Aadhaar/Phone/Email | "I cannot process personal or sensitive information. Please do not share PII such as PAN, Aadhaar, or account numbers." |
| **Out of Scope** | No relevant chunks above similarity threshold | "I can only answer factual questions about the 5 HDFC mutual fund schemes in my database. Please rephrase or visit [Groww](https://groww.in/mutual-funds) for other funds." |
| **Performance Query** | Keywords: *returns, performance, NAV history, CAGR* | "I don't provide performance data or return calculations. For the latest returns, please refer to the official factsheet at {source_url}." |

---

## 6. Backend API (FastAPI)

### 6.1 API Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `POST` | `/api/query` | Accept user query, return factual answer | Public (CORS-restricted) |
| `POST` | `/api/ingest/refresh` | Trigger full re-ingestion pipeline | Bearer token (`INGEST_API_KEY`) |
| `GET` | `/api/health` | Health check (DB status, model loaded) | Public |
| `GET` | `/api/status` | Last ingestion date, chunk count | Public |

### 6.2 Request / Response Schemas

**Query Endpoint** — `POST /api/query`

```json
// Request
{
  "query": "What is the expense ratio of HDFC Mid Cap Fund?"
}

// Response (200 OK)
{
  "answer": "The expense ratio of HDFC Mid Cap Fund (Direct Growth) is 0.75%.",
  "source_url": "https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth",
  "last_updated": "2026-08-30",
  "refused": false
}

// Response (200 OK — Refusal)
{
  "answer": "I'm a facts-only assistant and cannot provide investment advice...",
  "source_url": null,
  "last_updated": null,
  "refused": true,
  "refusal_category": "advisory"
}
```

**Ingest Endpoint** — `POST /api/ingest/refresh`

```json
// Response (200 OK)
{
  "status": "success",
  "schemes_scraped": 5,
  "chunks_stored": 97,
  "scrape_date": "2026-08-30"
}
```

### 6.3 CORS Configuration

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://mf-faq-assistant.vercel.app",  # Production (Vercel)
        "http://localhost:5500",                   # Local dev (Live Server)
        "http://localhost:3000",                   # Local dev (alternative)
        "http://127.0.0.1:5500",                   # Local dev (IP)
    ],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

### 6.4 Ingest Endpoint Security

The `/api/ingest/refresh` endpoint is protected with a Bearer token to prevent unauthorized re-ingestion:

```python
from fastapi import Header, HTTPException

async def verify_ingest_key(authorization: str = Header(...)):
    expected = f"Bearer {os.getenv('INGEST_API_KEY')}"
    if authorization != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")
```

---

## 7. Scheduled Ingestion (GitHub Actions)

### 7.1 Scheduler Overview

A GitHub Actions workflow runs daily at **10:00 AM IST (4:30 AM UTC)** to trigger a full data refresh on the Railway backend.

```mermaid
sequenceDiagram
    participant GH as GitHub Actions
    participant RW as Railway Backend
    participant GW as Groww URLs
    participant DB as ChromaDB (Volume)

    GH->>RW: POST /api/ingest/refresh (Bearer token)
    RW->>GW: Scrape 5 scheme URLs (Playwright)
    GW-->>RW: HTML pages
    RW->>RW: Clean → Chunk → Embed
    RW->>DB: Upsert vectors + metadata
    DB-->>RW: Confirmation
    RW-->>GH: 200 OK (5 schemes, 97 chunks)
```

### 7.2 Workflow Definition

```yaml
# .github/workflows/scheduled-ingestion.yml
name: Daily Data Ingestion

on:
  schedule:
    - cron: '30 4 * * *'   # 4:30 AM UTC = 10:00 AM IST
  workflow_dispatch:         # Allow manual trigger from GitHub UI

jobs:
  trigger-ingestion:
    runs-on: ubuntu-latest
    steps:
      - name: Trigger Ingestion on Railway Backend
        run: |
          response=$(curl -s -o /dev/null -w "%{http_code}" \
            -X POST "${{ secrets.RAILWAY_BACKEND_URL }}/api/ingest/refresh" \
            -H "Authorization: Bearer ${{ secrets.INGEST_API_KEY }}" \
            -H "Content-Type: application/json" \
            --max-time 300)

          if [ "$response" -ne 200 ]; then
            echo "❌ Ingestion failed with HTTP $response"
            exit 1
          fi
          echo "✅ Ingestion completed successfully"

      - name: Notify on Failure
        if: failure()
        run: echo "::error::Daily ingestion failed. Check Railway logs."
```

### 7.3 GitHub Secrets Required

| Secret | Purpose | Example |
|--------|---------|---------|
| `RAILWAY_BACKEND_URL` | Railway backend base URL | `https://mf-faq-backend.up.railway.app` |
| `INGEST_API_KEY` | Bearer token for `/api/ingest/refresh` | `sk_ingest_xxxxxxxxxxxx` |

### 7.4 Ingestion Pipeline Steps (on Railway)

When `/api/ingest/refresh` is called, the backend executes:

```mermaid
flowchart LR
    A["API Trigger"] --> B["Scrape 5 Groww URLs\n(Playwright)"]
    B --> C["Clean & Parse\n(BS4)"]
    C --> D["Chunk\n(500 chars, 50 overlap)"]
    D --> E["Embed\n(BGE-large 1024-dim)"]
    E --> F["Clear & Upsert\nChromaDB Collection"]
    F --> G["Return Status\n(200 OK)"]
```

---

## 8. User Interface (Vercel Frontend)

### 8.1 Overview

The frontend is a **static single-page application** (HTML/CSS/JS) deployed on Vercel. It communicates with the Railway backend via `POST /api/query`.

### 8.2 Chat Layout

```
┌──────────────────────────────────────────────────┐
│  🏦 Mutual Fund FAQ Assistant                    │
│  ─────────────────────────────────────────────── │
│  ⚠️ Facts-only. No investment advice.            │
│                                                  │
│  💡 Try asking:                                  │
│  [What is the expense ratio of HDFC Mid Cap?]    │
│  [What is the exit load for HDFC ELSS fund?]     │
│  [What is the minimum SIP for HDFC Large Cap?]   │
│                                                  │
│  ┌──────────────────────────────────────────┐    │
│  │ 🤖 Welcome! I can answer factual         │    │
│  │    questions about HDFC mutual fund       │    │
│  │    schemes on Groww.                      │    │
│  └──────────────────────────────────────────┘    │
│                                                  │
│  ┌──────────────────────────────────────────┐    │
│  │ 👤 What is the expense ratio of HDFC     │    │
│  │    Mid Cap Fund?                          │    │
│  └──────────────────────────────────────────┘    │
│                                                  │
│  ┌──────────────────────────────────────────┐    │
│  │ 🤖 The expense ratio of HDFC Mid Cap     │    │
│  │    Fund (Direct Growth) is 0.75%.         │    │
│  │                                           │    │
│  │    🔗 Source: groww.in/mutual-funds/...   │    │
│  │    📅 Last updated from sources:          │    │
│  │       2026-08-29                          │    │
│  └──────────────────────────────────────────┘    │
│                                                  │
│  ┌──────────────────────────────────────────┐    │
│  │ Type your question...              [Send] │    │
│  └──────────────────────────────────────────┘    │
└──────────────────────────────────────────────────┘
```

### 8.3 Frontend Components

| Component | Implementation |
|-----------|---------------|
| Chat container | Scrollable `<div>` with message bubbles |
| Message input | `<input>` + Send button; Enter key to submit |
| Message bubbles | CSS-styled user (right-aligned) and bot (left-aligned) bubbles |
| Disclaimer banner | Fixed `<div>` at top — always visible |
| Example questions | Clickable `<button>` elements — auto-fill input |
| Source links | `<a>` tags rendered in bot responses |
| Loading state | Typing indicator animation during API call |
| Error handling | Toast/banner for network errors or backend unavailability |

### 8.4 API Client (JavaScript)

```javascript
const API_BASE = "https://mf-faq-backend.up.railway.app";

async function queryAssistant(userQuery) {
    const response = await fetch(`${API_BASE}/api/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: userQuery }),
    });

    if (!response.ok) throw new Error("Backend unavailable");
    return await response.json();
}
```

---

## 9. Project Directory Structure

```
RAG-Chatbot/
├── .github/
│   └── workflows/
│       └── scheduled-ingestion.yml    # Daily 10 AM IST cron trigger
│
├── docs/
│   ├── problemStatement.md
│   ├── problemStatement.txt
│   ├── architecture.md                # This document
│   └── implementation-plan.md
│
├── backend/
│   ├── src/
│   │   ├── __init__.py
│   │   ├── main.py                    # FastAPI app entry point
│   │   ├── config.py                  # Environment config loader
│   │   ├── scraper/
│   │   │   ├── __init__.py
│   │   │   ├── groww_scraper.py       # Playwright-based Groww page scraper
│   │   │   └── content_cleaner.py     # HTML → structured text cleaning
│   │   ├── ingestion/
│   │   │   ├── __init__.py
│   │   │   ├── chunker.py            # Text splitting with metadata
│   │   │   ├── embedder.py           # BGE-large embedding
│   │   │   └── vectorstore.py        # ChromaDB collection management
│   │   ├── pipeline/
│   │   │   ├── __init__.py
│   │   │   ├── guardrails.py         # PII detection, advisory filter, scope check
│   │   │   ├── retriever.py          # Similarity search with metadata filtering
│   │   │   ├── prompt_builder.py     # System prompt + context assembly
│   │   │   ├── llm_client.py         # Groq API wrapper
│   │   │   └── response_formatter.py # 3-sentence + citation + footer enforcer
│   │   └── api/
│   │       ├── __init__.py
│   │       └── routes.py             # API route definitions
│   ├── data/
│   │   ├── raw/                      # Raw scraped HTML (cached)
│   │   ├── processed/                # Cleaned text + metadata JSON
│   │   └── chroma_db/                # ChromaDB persistent storage (Railway volume)
│   ├── tests/
│   │   ├── test_guardrails.py
│   │   ├── test_retriever.py
│   │   ├── test_formatter.py
│   │   └── test_api.py              # API endpoint tests
│   ├── requirements.txt
│   ├── Procfile                      # Railway process definition
│   └── railway.toml                  # Railway config
│
├── frontend/
│   ├── index.html                    # Main chat page
│   ├── css/
│   │   └── style.css                 # Chat UI styles
│   ├── js/
│   │   └── app.js                    # Chat logic + API client
│   └── vercel.json                   # Vercel deployment config
│
├── .env.example
├── .gitignore
└── README.md
```

---

## 10. Data Flow Summary

```mermaid
flowchart LR
    subgraph Scheduled ["⏰ Daily (GitHub Actions → Railway)"]
        S1["10 AM IST\nCron Trigger"] --> S2["POST /api/ingest/refresh"]
        S2 --> S3["Scrape 5 Groww URLs\n(Playwright)"]
        S3 --> S4["Clean & Parse\n(BS4)"]
        S4 --> S5["Chunk\n(500 chars)"]
        S5 --> S6["Embed\n(BGE-large)"]
        S6 --> S7[("ChromaDB\nRailway Volume")]
    end

    subgraph Online ["🤖 Real-Time (Vercel → Railway)"]
        Q1["User Query\n(Vercel UI)"] --> Q2["POST /api/query\n(Railway)"]
        Q2 --> Q3{"Guardrails\nPass?"}
        Q3 -->|No| Q4["Refusal\nResponse"]
        Q3 -->|Yes| Q5["Embed Query"]
        Q5 --> Q6["Retrieve\nTop-3"]
        Q6 --> Q7["Build Prompt"]
        Q7 --> Q8["Groq LLM"]
        Q8 --> Q9["Format\nResponse"]
        Q9 --> Q10["JSON → Vercel UI"]
    end

    S7 -.-> Q6
```

---

## 11. Environment & Configuration

### 11.1 Backend Environment Variables

#### Local Development (`.env` file)

| Variable | Value | Description |
|----------|-------|-------------|
| `GROQ_API_KEY` | `gsk_xxxxxxxxxxxx` | Groq API authentication key |
| `GROQ_MODEL` | `openai/gpt-oss-120b` | LLM model identifier |
| `CHROMA_PERSIST_DIR` | `./backend/data/chroma_db` | ChromaDB path (local directory) |
| `EMBEDDING_MODEL` | `BAAI/bge-large-en-v1.5` | Embedding model name |
| `CHUNK_SIZE` | `500` | Characters per chunk |
| `CHUNK_OVERLAP` | `50` | Overlap between chunks |
| `TOP_K` | `3` | Number of chunks to retrieve |
| `SIMILARITY_THRESHOLD` | `0.35` | Minimum cosine similarity |
| `INGEST_API_KEY` | `sk_ingest_xxxxxxxxxxxx` | Bearer token for ingest endpoint |
| `ALLOWED_ORIGINS` | `http://localhost:5500,http://localhost:3000` | CORS allowed origins (local) |
| `PORT` | `8000` | Server port |

#### Production — Railway

| Variable | Value | Description |
|----------|-------|-------------|
| `GROQ_API_KEY` | `gsk_xxxxxxxxxxxx` | Groq API authentication key |
| `GROQ_MODEL` | `openai/gpt-oss-120b` | LLM model identifier |
| `CHROMA_PERSIST_DIR` | `/data/chroma_db` | ChromaDB path (Railway volume mount) |
| `EMBEDDING_MODEL` | `BAAI/bge-large-en-v1.5` | Embedding model name |
| `CHUNK_SIZE` | `500` | Characters per chunk |
| `CHUNK_OVERLAP` | `50` | Overlap between chunks |
| `TOP_K` | `3` | Number of chunks to retrieve |
| `SIMILARITY_THRESHOLD` | `0.35` | Minimum cosine similarity |
| `INGEST_API_KEY` | `sk_ingest_xxxxxxxxxxxx` | Bearer token for ingest endpoint |
| `ALLOWED_ORIGINS` | `https://mf-faq-assistant.vercel.app` | CORS allowed origins (production) |
| `PORT` | `8000` | Server port (auto-set by Railway) |

### 11.2 Frontend Configuration

The frontend is a **plain HTML/CSS/JS** project (no build step, no Vite). The API base URL is set directly in `frontend/js/app.js`.

#### Local Development

```javascript
// frontend/js/app.js
const API_BASE = "http://localhost:8000";  // Local backend
```

#### Production — Vercel

Before deploying to Vercel, update the `API_BASE` in `frontend/js/app.js` to point to the Railway backend:

```javascript
// frontend/js/app.js
const API_BASE = "https://mf-faq-backend.up.railway.app";  // Railway backend
```

> **Note**: Since this is a static site with no build step, there are no Vercel environment variables. The API URL is hardcoded in `app.js` and must be updated before pushing to the `main` branch for Vercel deployment.

### 11.3 GitHub Secrets

| Secret | Value | Description |
|--------|-------|-------------|
| `RAILWAY_BACKEND_URL` | `https://mf-faq-backend.up.railway.app` | Railway backend URL |
| `INGEST_API_KEY` | `sk_ingest_xxxxxxxxxxxx` | Bearer token matching Railway env |

### 11.4 Backend Dependencies (`backend/requirements.txt`)

```
fastapi>=0.115.0
uvicorn[standard]>=0.30.0
langchain>=0.3.0
langchain-groq>=0.2.0
langchain-community>=0.3.0
chromadb>=0.5.0
sentence-transformers>=3.0.0
playwright>=1.45.0
beautifulsoup4>=4.12.0
python-dotenv>=1.0.0
httpx>=0.27.0
```

### 11.5 Railway Configuration

**`backend/Procfile`**:
```
web: uvicorn src.main:app --host 0.0.0.0 --port $PORT
```

**`backend/railway.toml`**:
```toml
[build]
builder = "nixpacks"

[deploy]
startCommand = "playwright install-deps chromium && playwright install chromium && uvicorn src.main:app --host 0.0.0.0 --port $PORT"
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 3

[[volumes]]
mount = "/data"
```

### 11.6 Vercel Configuration

**`frontend/vercel.json`**:
```json
{
  "buildCommand": null,
  "outputDirectory": ".",
  "rewrites": [
    { "source": "/(.*)", "destination": "/index.html" }
  ],
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        { "key": "X-Content-Type-Options", "value": "nosniff" },
        { "key": "X-Frame-Options", "value": "DENY" }
      ]
    }
  ]
}
```

---

## 12. Local Development (Mac)

Before deploying to Railway and Vercel, verify everything works locally on your Mac.

### 12.1 Prerequisites

```bash
# Ensure Python 3.11+ is installed
python3 --version

# Ensure Node.js is available (optional, for npx serve)
node --version
```

### 12.2 Starting the Backend Locally

```bash
# 1. Navigate to the project root
cd RAG-Chatbot

# 2. Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install dependencies
pip install -r backend/requirements.txt

# 4. Install Playwright browser
playwright install chromium

# 5. Create .env from template (fill in your GROQ_API_KEY)
cp .env.example .env
# Edit .env and set your GROQ_API_KEY and INGEST_API_KEY

# 6. Run the FastAPI backend
cd backend
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

> **`--reload`** enables auto-restart on code changes during development. Do not use in production.

The backend will be available at `http://localhost:8000`.

**Quick health check:**
```bash
curl http://localhost:8000/api/health
```

**API docs (auto-generated):**
```
http://localhost:8000/docs     # Swagger UI
http://localhost:8000/redoc    # ReDoc
```

### 12.3 Starting the Frontend Locally

Open a **new terminal** (keep backend running):

```bash
# Option 1: Python HTTP server
cd RAG-Chatbot/frontend
python3 -m http.server 5500

# Option 2: VS Code Live Server (port 5500)
# Right-click index.html → "Open with Live Server"

# Option 3: npx serve
cd RAG-Chatbot/frontend
npx -y serve -l 5500
```

The frontend will be available at `http://localhost:5500`.

> **Important**: Ensure `API_BASE` in `frontend/js/app.js` is set to `http://localhost:8000` for local development.

### 12.4 Running a Local Ingestion

```bash
# Trigger ingestion via the API (use your INGEST_API_KEY from .env)
curl -X POST http://localhost:8000/api/ingest/refresh \
  -H "Authorization: Bearer sk_ingest_xxxxxxxxxxxx" \
  -H "Content-Type: application/json"
```

### 12.5 Stopping Locally

```bash
# Stop backend: Press Ctrl+C in the backend terminal
# Stop frontend: Press Ctrl+C in the frontend terminal
#   (applies to python3 -m http.server, npx serve, and VS Code Live Server)

# Deactivate the Python virtual environment when done
deactivate
```

> **Tip**: Keep both terminals visible side-by-side to monitor backend logs while testing from the frontend.

### 12.6 Local Development Summary

| Component | Command | URL | Port |
|-----------|---------|-----|------|
| Backend (FastAPI) | `uvicorn src.main:app --reload --port 8000` | `http://localhost:8000` | 8000 |
| Frontend (static) | `python3 -m http.server 5500` | `http://localhost:5500` | 5500 |
| Health Check | `curl http://localhost:8000/api/health` | — | — |
| Trigger Ingestion | `curl -X POST .../api/ingest/refresh` | — | — |

```mermaid
flowchart LR
    subgraph Local ["🖥️ Local Mac"]
        FE["Frontend\nlocalhost:5500"] -->|POST /api/query| BE["Backend\nlocalhost:8000"]
        BE -->|Groq API| GQ["Groq Cloud"]
        BE -->|Playwright| GW["Groww URLs"]
        BE --- DB[("ChromaDB\n./backend/data/chroma_db")]
    end
```

---

## 13. Deployment Model

### 13.1 Deployment Strategy

Deployment follows a phased approach:
1. **Local verification** — Ensure backend + frontend work on your Mac (Section 12)
2. **Push to GitHub** — Commit and push all code to the repository
3. **Backend deployment** — Deploy backend to Railway
4. **Frontend deployment** — Deploy frontend to Vercel
5. **Scheduler setup** — Configure GitHub Actions for daily ingestion

> **Note**: A detailed phase-wise `deployment.md` will be created separately as part of deployment planning.

### 13.2 Deployment Architecture

```mermaid
flowchart LR
    subgraph GitHub ["GitHub Repository"]
        GR["Source Code"] --> GA["GitHub Actions\n(Cron: 4:30 AM UTC)"]
    end

    subgraph Railway ["Railway (Backend)"]
        RA["FastAPI Server\n(Uvicorn)"]
        RV[("Persistent Volume\n/data/chroma_db")]
        RA --- RV
    end

    subgraph Vercel ["Vercel (Frontend)"]
        VA["Static Site\n(HTML/CSS/JS)"]
    end

    subgraph External ["External Services"]
        GQ["Groq API"]
        GW["Groww URLs"]
    end

    GR -->|Git Push| RA
    GR -->|Git Push| VA
    GA -->|POST /api/ingest/refresh| RA
    VA -->|POST /api/query| RA
    RA -->|LLM Inference| GQ
    RA -->|Scrape| GW
```

### 13.3 Deployment Summary

| Aspect | Details |
|--------|---------|
| **Backend** | Railway — FastAPI + Uvicorn; auto-deploys on `git push` to `main` |
| **Frontend** | Vercel — static HTML/CSS/JS; auto-deploys on `git push` to `main` |
| **Database** | ChromaDB on Railway persistent volume (`/data/`) |
| **Scheduler** | GitHub Actions — `cron: '30 4 * * *'` (10 AM IST daily) |
| **Ingestion Flow** | GitHub Action → `POST /api/ingest/refresh` → Railway runs full pipeline |
| **Manual Refresh** | `workflow_dispatch` on GitHub Actions UI or direct API call |
| **Scaling** | Single instance (sufficient for demo/FAQ traffic) |

### 13.4 Deploy Workflow

```
1. Verify locally (Section 12) — backend + frontend both work
     ↓
2. Push code to GitHub main branch
     ↓
3. Railway auto-builds & deploys backend
   Vercel auto-builds & deploys frontend
     ↓
4. Set environment variables on Railway + Vercel
     ↓
5. Manually trigger first ingestion via GitHub Actions (workflow_dispatch)
     ↓
6. Daily cron (10 AM IST) keeps data fresh automatically
```

> See `docs/deployment.md` (to be created) for step-by-step deployment instructions.

---

## 14. Known Limitations & Mitigations

| Limitation | Mitigation |
|-----------|------------|
| Groww pages are JS-rendered; simple HTTP requests fail | Use Playwright (headless Chrome) for full page rendering locally and on Railway |
| Groww may change page structure, breaking scrapers | Modular scraper with section-specific selectors; easy to update |
| Small corpus (~100 chunks) limits answer diversity | Sufficient for FAQ-style factual queries; expand corpus later if needed |
| Groq free tier has rate limits (~30 RPM) | Acceptable for demo/dev; upgrade to paid tier for production |
| BGE-large model (~1.3 GB) on Railway | Railway supports up to 8 GB RAM; model loads once at startup |
| Playwright on Railway requires system deps | Install via `playwright install-deps chromium` in deploy command |
| No real-time NAV data | Daily ingestion at 10 AM IST; footer states `Last updated from sources: <date>` |
| Cold starts on Railway free tier | First request after idle period may be slow (~10-15s); acceptable for FAQ use |
| CORS restrictions | Explicit allowlist for Vercel domain + localhost for dev |

---

## 15. Security & Compliance Checklist

| Requirement | Implementation |
|-------------|---------------|
| ✅ No PII collection | Regex-based PII detection in guardrail layer; immediate refusal |
| ✅ No investment advice | Keyword + semantic advisory detection; polite refusal with AMFI link |
| ✅ Source attribution | Every response includes exactly 1 Groww source URL |
| ✅ Data provenance | `scrape_date` metadata attached to every chunk |
| ✅ Official sources only | Corpus restricted to 5 Groww URLs; no third-party data |
| ✅ Transparency | Footer with last-updated date on every response |
| ✅ Ingest endpoint auth | Bearer token required; secret stored in GitHub + Railway |
| ✅ CORS policy | Allowlisted Vercel domain only; blocks unauthorized origins |
| ✅ No secrets in code | All keys via environment variables; `.env` gitignored |
