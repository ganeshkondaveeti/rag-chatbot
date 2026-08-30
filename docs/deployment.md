# Phase-Wise Deployment Plan

This document outlines the deployment strategy for the Mutual Fund FAQ Assistant across Railway (Backend), Vercel (Frontend), and GitHub Actions (Scheduler).

---

## Phase 1: Preparation & GitHub Push

1. **Local Verification**: Ensure that the application runs locally and all tests pass (`pytest backend/tests/`).
2. **Environment Variables**: Document all required environment variables (`GROQ_API_KEY`, `INGEST_API_KEY`, `CHROMA_DB_DIR`).
3. **Commit & Push**:
   ```bash
   git add .
   git commit -m "Prepare for deployment"
   git push origin main
   ```

---

## Phase 2: Backend Deployment (Railway)

We use Railway to host the FastAPI backend, utilizing a persistent volume to store the ChromaDB vector database.

1. **Create Project**: Log into Railway and create a new project from your GitHub repository.
2. **Root Directory**: Configure the service to use the `backend/` directory as its root.
3. **Environment Variables**: Navigate to the Variables tab and add:
   - `GROQ_API_KEY`: Your Groq API token.
   - `INGEST_API_KEY`: A secure, randomly generated string.
   - `CHROMA_DB_DIR`: `/data`
4. **Persistent Volume**:
   - Go to the Settings tab -> Volumes.
   - Add a new volume and mount it at `/data`.
5. **Build Command**: Railway should automatically detect the `requirements.txt` and install dependencies. Ensure Playwright is installed via a post-install hook or custom start command if necessary (e.g., `playwright install chromium && uvicorn src.main:app --host 0.0.0.0 --port $PORT`).
6. **Verify Health**: Wait for the deployment to succeed, then test the health endpoint:
   ```bash
   curl https://<railway-app-url>/api/health
   ```

---

## Phase 3: Frontend Deployment (Vercel)

We use Vercel to host the static HTML/JS/CSS frontend.

1. **Update API URL**: In `frontend/js/app.js`, change the `API_BASE` variable to point to your Railway backend URL.
   ```javascript
   const API_BASE = "https://<railway-app-url>";
   ```
2. **Commit & Push**: Push this change to GitHub.
3. **Create Project**: Log into Vercel and import your GitHub repository.
4. **Configuration**:
   - Set the **Root Directory** to `frontend`.
   - Leave the build command empty (as it's a static site).
5. **Deploy**: Click Deploy and wait for the process to finish.
6. **Verify UI**: Open the Vercel URL and ensure the chat interface loads correctly.

---

## Phase 4: Scheduler Configuration (GitHub Actions)

We use GitHub Actions to run a daily cron job that triggers the backend's ingestion pipeline to refresh data.

1. **Navigate to GitHub Secrets**: Go to your repository Settings -> Secrets and variables -> Actions.
2. **Add Secrets**:
   - `RAILWAY_BACKEND_URL`: `https://<railway-app-url>` (no trailing slash).
   - `INGEST_API_KEY`: The exact same secure token you set in Railway.
3. **Verify Workflow**: Check the `.github/workflows/scheduled-ingestion.yml` file. It should be configured to run daily or on `workflow_dispatch`.
4. **Manual Trigger**:
   - Go to the Actions tab in your GitHub repository.
   - Select the "Daily Data Ingestion" workflow.
   - Click "Run workflow" to manually trigger the first ingestion.
5. **Verify Ingestion**: Monitor the GitHub Action logs and the Railway backend logs to ensure the scraping and ChromaDB insertion completed successfully.

---

## Phase 5: End-to-End Validation

1. **Send a Query**: Open the Vercel URL and ask a factual question (e.g., "What is the exit load for HDFC Mid Cap?").
2. **Verify Response**: Ensure the bot replies correctly, includes a source link, and appends the disclaimer footer.
3. **Verify Guardrails**: Ask an advisory question (e.g., "Should I invest in this fund?") and ensure it is gracefully refused.
4. **Verify CORS**: Check the browser's developer console to ensure there are no Cross-Origin Resource Sharing (CORS) errors when the frontend communicates with the Railway backend.
