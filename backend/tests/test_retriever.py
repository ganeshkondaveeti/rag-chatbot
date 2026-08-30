import pytest
from unittest.mock import MagicMock
from src.pipeline.retriever import Retriever, QueryPipeline

def test_extract_scheme_name():
    retriever = Retriever(vectorstore_manager=None)
    
    assert retriever.extract_scheme_name("What is the expense ratio for HDFC Mid Cap?") == "HDFC Mid Cap Fund"
    assert retriever.extract_scheme_name("Tell me about hdfc elss") == "HDFC ELSS Tax Saver Fund"
    assert retriever.extract_scheme_name("gold fof nav") == "HDFC Gold ETF FoF"
    assert retriever.extract_scheme_name("expense ratio") == None

def test_retrieve_with_scheme():
    mock_db = MagicMock()
    mock_doc = MagicMock()
    mock_doc.page_content = "This is a test document."
    mock_doc.metadata = {"source_url": "http://test.com", "scheme_name": "HDFC Mid Cap Fund"}
    mock_db.similarity_search.return_value = [mock_doc]
    
    mock_vsm = MagicMock()
    mock_vsm.db = mock_db
    
    retriever = Retriever(vectorstore_manager=mock_vsm)
    
    results = retriever.retrieve("What is the expense ratio for HDFC Mid Cap?")
    
    # Check if metadata filter was applied
    mock_db.similarity_search.assert_called_once_with(
        "What is the expense ratio for HDFC Mid Cap?",
        k=3,
        filter={"scheme_name": "HDFC Mid Cap Fund"}
    )
    
    assert len(results) == 1
    assert results[0]["content"] == "This is a test document."
    assert results[0]["metadata"]["source_url"] == "http://test.com"

def test_retrieve_without_scheme():
    mock_db = MagicMock()
    mock_db.similarity_search.return_value = []
    
    mock_vsm = MagicMock()
    mock_vsm.db = mock_db
    
    retriever = Retriever(vectorstore_manager=mock_vsm)
    
    results = retriever.retrieve("expense ratio")
    
    # Check if fallback top_k was applied and no filter
    mock_db.similarity_search.assert_called_once_with(
        "expense ratio",
        k=5
    )
    assert len(results) == 0

def test_query_pipeline_refusal():
    mock_retriever = MagicMock()
    pipeline = QueryPipeline(retriever=mock_retriever)
    
    res = pipeline.process_query("What are the 3-year returns of HDFC Mid Cap?")
    assert res["refused"] == True
    assert res["refusal_category"] == "performance"
    assert len(res["context"]) == 0
    mock_retriever.retrieve.assert_not_called()

def test_query_pipeline_success():
    mock_retriever = MagicMock()
    mock_retriever.retrieve.return_value = [{"content": "Data"}]
    
    pipeline = QueryPipeline(retriever=mock_retriever)
    
    res = pipeline.process_query("What is the expense ratio for HDFC Mid Cap?")
    assert res["refused"] == False
    assert res["refusal_category"] == None
    assert len(res["context"]) == 1
    mock_retriever.retrieve.assert_called_once_with("What is the expense ratio for HDFC Mid Cap?")
