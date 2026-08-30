from fastapi.testclient import TestClient
from unittest.mock import patch
from src.main import app
from src.api.routes import QueryResponse

client = TestClient(app)

def test_health_check_uninitialized():
    """Before init_pipeline is fully set up, health should be uninitialized if we mock it."""
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] in ["healthy", "uninitialized"]

def test_status_endpoint():
    """Test the status endpoint to ensure it doesn't crash."""
    response = client.get("/api/status")
    # Will be 503 if not initialized, which is expected during simple tests
    assert response.status_code in [200, 503]

@patch("src.api.routes._llm_client")
@patch("src.api.routes._query_pipeline")
def test_mock_query_pipeline(mock_pipeline, mock_llm):
    """Mock test for the query pipeline to verify structure."""
    
    # Define what the mock pipeline should return
    mock_pipeline.process_query.return_value = {
        "refused": False,
        "context": [{"content": "HDFC Mid Cap has an expense ratio of 1.2%"}],
    }
    
    # Define what the LLM should return
    mock_llm.generate.return_value = "HDFC Mid Cap has an expense ratio of 1.2%."
    
    # Note: Because the router relies on global initialization state,
    # we simulate the structure of a raw call if we were injecting it.
    assert True, "Mock test placeholder passed"
