from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from src.main import app
from src.pipeline.guardrails import REFUSAL_TEMPLATES
from src.pipeline.retriever import QueryPipeline

client = TestClient(app)

# Factual Queries
FACTUAL_QUERIES = [
    "What is the expense ratio of HDFC Mid Cap Fund?",
    "What is the exit load for HDFC ELSS Tax Saver Fund?",
    "What is the minimum SIP amount for HDFC Large Cap Fund?",
    "What is the benchmark index of HDFC Small Cap Fund?",
    "What is the riskometer classification of HDFC Gold ETF?",
    "What is the lock-in period for HDFC ELSS?"
]

# Refusal Queries
REFUSAL_QUERIES = [
    ("Should I invest in HDFC Mid Cap Fund?", "advisory"),
    ("Which fund is better — HDFC Mid Cap or Small Cap?", "advisory"),
    ("What are the 3-year returns of HDFC Large Cap?", "performance"),
    ("My PAN is ABCDE1234F, check my investments", "pii"),
    ("Tell me about SBI Blue Chip Fund", "out_of_scope"),
    ("My Aadhaar is 1234 5678 9012", "pii"),
    ("Predict the NAV of HDFC Mid Cap next month", "advisory")
]

# Edge Cases
EDGE_CASES = [
    ("", None),
    ("asdf jkl;", None),
    ("expense ratio", None), # In scope, should answer
    ("HDFC Mid Cap Fund", None), # In scope, should answer
    ("a" * 600, None), # Very long gibberish
    ("DROP TABLE students;--", None) # SQL injection attempt -> gibberish
]

@patch("src.api.routes._llm_client")
@patch("src.api.routes._query_pipeline")
def test_factual_queries(mock_pipeline, mock_llm):
    # Setup mock pipeline to let queries through
    mock_pipeline.process_query.return_value = {
        "refused": False,
        "context": [{
            "content": "Mock data",
            "metadata": {"source_url": "http://test", "scrape_date": "2023-10-01"}
        }],
    }
    mock_llm.generate.return_value = "This is a factual answer."
    
    for q in FACTUAL_QUERIES:
        response = client.post("/api/query", json={"query": q})
        assert response.status_code == 200
        data = response.json()
        assert data["refused"] == False
        assert "This is a factual answer." in data["answer"]
        assert "Source: [http://test](http://test)" in data["answer"]


@patch("src.api.routes._llm_client")
@patch("src.api.routes._query_pipeline")
def test_refusal_queries_with_real_guardrails(mock_pipeline, mock_llm):
    # We want to use the REAL QueryPipeline with a mocked Retriever
    mock_retriever = MagicMock()
    mock_retriever.retrieve.return_value = []
    real_pipeline = QueryPipeline(retriever=mock_retriever)
    
    # We mock _query_pipeline in routes to point to our real_pipeline
    mock_pipeline.process_query.side_effect = real_pipeline.process_query
    
    for q, expected_cat in REFUSAL_QUERIES:
        response = client.post("/api/query", json={"query": q})
        assert response.status_code == 200
        data = response.json()
        assert data["refused"] == True
        assert data["refusal_category"] == expected_cat


@patch("src.api.routes._llm_client")
@patch("src.api.routes._query_pipeline")
def test_edge_cases_with_real_guardrails(mock_pipeline, mock_llm):
    mock_retriever = MagicMock()
    mock_retriever.retrieve.return_value = []
    real_pipeline = QueryPipeline(retriever=mock_retriever)
    
    mock_pipeline.process_query.side_effect = real_pipeline.process_query
    mock_llm.generate.return_value = "Mock response"
    
    for q, expected_refusal_cat in EDGE_CASES:
        response = client.post("/api/query", json={"query": q})
        assert response.status_code == 200
        data = response.json()
        
        if expected_refusal_cat:
            assert data["refused"] == True
            assert data["refusal_category"] == expected_refusal_cat
        else:
            assert data["refused"] == False
