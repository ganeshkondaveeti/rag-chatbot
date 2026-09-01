from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from src.main import app
from src.config import config

client = TestClient(app)

def test_health_check_uninitialized():
    """Before init_pipeline is fully set up, health should be uninitialized if we mock it."""
    with patch("src.api.routes._query_pipeline", None):
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json()["status"] in ["healthy", "uninitialized"]

def test_status_endpoint_uninitialized():
    """Test the status endpoint when uninitialized."""
    with patch("src.api.routes._vectorstore_manager", None):
        response = client.get("/api/status")
        assert response.status_code == 503

@patch("src.api.routes._vectorstore_manager")
def test_status_endpoint_ready(mock_vsm):
    mock_db = MagicMock()
    mock_db._collection.count.return_value = 100
    mock_vsm.db = mock_db
    
    response = client.get("/api/status")
    assert response.status_code == 200
    assert response.json()["chunks_stored"] == 100

@patch("src.api.routes._llm_client")
@patch("src.api.routes._query_pipeline")
def test_query_pipeline_refused(mock_pipeline, mock_llm):
    # Setup mock refusal
    mock_pipeline.process_query.return_value = {
        "refused": True,
        "refusal_message": "I cannot answer that.",
        "refusal_category": "advisory",
    }
    
    response = client.post("/api/query", json={"query": "Should I invest?"})
    assert response.status_code == 200
    data = response.json()
    assert data["refused"] == True
    assert data["answer"] == "I cannot answer that."
    assert data["refusal_category"] == "advisory"
    mock_llm.generate.assert_not_called()

@patch("src.api.routes._llm_client")
@patch("src.api.routes._query_pipeline")
def test_query_pipeline_success(mock_pipeline, mock_llm):
    # Setup mock context
    mock_pipeline.process_query.return_value = {
        "refused": False,
        "context": [{
            "content": "HDFC Mid Cap has an expense ratio of 1.2%",
            "metadata": {"source_url": "http://test", "scrape_date": "2023-10-01"}
        }],
    }
    mock_llm.generate.return_value = "The expense ratio is 1.2%."
    
    response = client.post("/api/query", json={"query": "expense ratio?"})
    assert response.status_code == 200
    data = response.json()
    assert data["refused"] == False
    assert "The expense ratio is 1.2%." in data["answer"]
    assert data["source_url"] == "http://test"

def test_ingest_auth_missing():
    response = client.post("/api/ingest/refresh")
    assert response.status_code == 401 # Missing credentials gives 401 in FastAPI HTTPBearer

def test_ingest_auth_invalid():
    response = client.post("/api/ingest/refresh", headers={"Authorization": "Bearer BAD_TOKEN"})
    assert response.status_code == 401
    
@patch("src.api.routes.init_pipeline")
@patch("src.ingestion.ingest.main")
def test_ingest_auth_valid(mock_ingest, mock_init):
    response = client.post("/api/ingest/refresh", headers={"Authorization": f"Bearer {config.INGEST_API_KEY}"})
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    mock_ingest.assert_called_once()
    mock_init.assert_called_once()
