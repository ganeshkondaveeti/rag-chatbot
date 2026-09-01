import pytest
from src.pipeline.response_formatter import ResponseFormatter

def test_truncation():
    # Less than 3 sentences
    raw = "This is one sentence. This is two."
    res = ResponseFormatter.format_response(raw, [])
    assert res["answer"] == "This is one sentence. This is two."
    
    # Exactly 3 sentences
    raw = "One. Two. Three."
    res = ResponseFormatter.format_response(raw, [])
    assert res["answer"] == "One. Two. Three."
    
    # More than 3 sentences
    raw = "One. Two. Three. Four. Five."
    res = ResponseFormatter.format_response(raw, [])
    assert res["answer"] == "One. Two. Three."
    
    # Complex sentences
    raw = "Hello! How are you? I am fine. Thanks."
    res = ResponseFormatter.format_response(raw, [])
    assert res["answer"] == "Hello! How are you? I am fine."

def test_source_and_footer():
    raw = "The expense ratio is 0.5%."
    context_chunks = [
        {
            "content": "some text",
            "metadata": {
                "source_url": "https://example.com/fund",
                "scrape_date": "2023-10-01"
            }
        }
    ]
    
    res = ResponseFormatter.format_response(raw, context_chunks)
    
    assert res["answer"] == raw
    assert res["source_url"] == "https://example.com/fund"
    assert res["last_updated"] == "2023-10-01"
    assert res["refused"] == False

def test_no_source():
    raw = "No data found."
    # Missing metadata
    context_chunks = [{"content": "text"}]
    
    res = ResponseFormatter.format_response(raw, context_chunks)
    assert res["answer"] == raw
    assert res["source_url"] is None
    assert res["last_updated"] is None
