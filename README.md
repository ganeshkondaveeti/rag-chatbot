# 🏦 Mutual Fund FAQ Assistant

> Facts-only. No investment advice.

## Overview
A Retrieval-Augmented Generation (RAG) chatbot that answers factual questions about Groww Mutual Funds. It scrapes real-time data from Groww's mutual fund pages, stores it in a ChromaDB vector database, and uses the Groq API (Llama 3 8B) to answer user queries with precise citations.

## Features
- **Accurate & Factual**: Only answers questions based on scraped Groww mutual fund data.
- **Strict Guardrails**: Refuses to provide investment advice, predict performance, or handle Personally Identifiable Information (PII).
- **Source Citations**: Every answer includes a direct link to the source material.
- **Automated Data Pipeline**: Scrapes and updates fund data automatically.
- **Responsive UI**: Clean, mobile-friendly chat interface.

## Architecture
- **Frontend**: Vanilla JavaScript, HTML, CSS (Hosted on Vercel)
- **Backend**: FastAPI, Python (Hosted on Railway)
- **Database**: ChromaDB (Persistent Volume on Railway)
- **LLM**: Groq API (Llama 3 8B)
- **Scraping**: Playwright + BeautifulSoup4
- **Orchestration**: GitHub Actions (Daily Cron Job for Ingestion)

## Tech Stack
- Python 3.12+
- FastAPI
- ChromaDB
- Groq
- Playwright
- Pytest
- Vanilla JS/HTML/CSS

## Setup

### Prerequisites
- Python 3.12+
- Node.js (for frontend local server, optional)
- Groq API Key

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd <repository-name>
```

2. Set up the backend Python virtual environment:
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
```

### Backend Configuration (.env)
Create a `.env` file in the `backend/` directory with the following variables:
```env
GROQ_API_KEY=your_groq_api_key
INGEST_API_KEY=your_secure_ingest_token
CHROMA_DB_DIR=./data/chroma
```

### Frontend Configuration
If running the backend locally, ensure the `API_BASE` in `frontend/js/app.js` is set to `http://localhost:8000`. If connecting to a deployed backend, update it to the deployed URL.

## Local Development (Mac)

### Start Backend
In the `backend` directory, with the virtual environment activated:
```bash
uvicorn src.main:app --reload --port 8000
```
The backend will be available at `http://localhost:8000`.

### Start Frontend
In a new terminal window, navigate to the `frontend` directory:
```bash
cd frontend
python3 -m http.server 5500
```
Open `http://localhost:5500` in your browser.

### Run Local Ingestion
To populate the local ChromaDB with fund data, run:
```bash
curl -X POST http://localhost:8000/api/ingest/refresh -H "Authorization: Bearer <YOUR_INGEST_API_KEY>"
```
Wait for the response to confirm successful scraping and vector storage.

### Stop Backend & Frontend
- Press `Ctrl+C` in the backend terminal.
- Press `Ctrl+C` in the frontend terminal.
- Run `deactivate` to exit the Python virtual environment.

## Deployment

### Railway (Backend)
1. Connect your GitHub repository to Railway.
2. Select the `backend/` folder as the root directory.
3. Add a Persistent Volume mounted to `/data`.
4. Set the Environment Variables (`GROQ_API_KEY`, `INGEST_API_KEY`, `CHROMA_DB_DIR=/data`).
5. Ensure the start command is `uvicorn src.main:app --host 0.0.0.0 --port $PORT`.

### Vercel (Frontend)
1. Connect your GitHub repository to Vercel.
2. Set the Root Directory to `frontend`.
3. Leave the build command empty.
4. Ensure `API_BASE` in `app.js` points to your Railway URL before deploying.

### GitHub Actions (Scheduler)
A GitHub Action is configured in `.github/workflows/scheduled-ingestion.yml` to trigger the ingestion pipeline daily at 10 AM IST.
Required Repository Secrets:
- `RAILWAY_BACKEND_URL`: URL of your deployed Railway app.
- `INGEST_API_KEY`: The token used to authenticate the ingest endpoint.

## API Reference

### POST /api/query
Submit a question to the chatbot.
```bash
curl -X POST http://localhost:8000/api/query \
     -H "Content-Type: application/json" \
     -d '{"text": "What is the exit load for HDFC Mid Cap?"}'
```

### POST /api/ingest/refresh
Trigger the web scraping and vector database update pipeline.
```bash
curl -X POST http://localhost:8000/api/ingest/refresh \
     -H "Authorization: Bearer <INGEST_API_KEY>"
```

### GET /api/health
Check backend health status.
```bash
curl http://localhost:8000/api/health
```

### GET /api/status
Get ingestion status and chunk count.
```bash
curl http://localhost:8000/api/status
```

## Selected Schemes
This bot is currently configured to retrieve data for the following Groww mutual funds:
1. Parag Parikh Flexi Cap Fund Direct Growth
2. Quant Small Cap Fund Direct Plan Growth
3. HDFC Mid-Cap Opportunities Fund Direct Plan Growth
4. SBI Equity Hybrid Fund Direct Growth
5. Nippon India Small Cap Fund Direct Growth

## Known Limitations
- The bot is limited to the specific mutual funds listed above.
- It cannot answer dynamic questions about personal portfolios or real-time market fluctuations.
- The retrieval pipeline relies on Groww's current DOM structure; changes to their website may break the scraper.

## Disclaimer
> **Important:** This chatbot provides **Facts-only** information based on public data. It does **not** provide investment advice. Responses are generated by AI and may be inaccurate. Always consult a certified financial advisor before making investment decisions.

## License
MIT License
