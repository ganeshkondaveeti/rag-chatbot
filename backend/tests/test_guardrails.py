import pytest
from src.pipeline.guardrails import Guardrails, REFUSAL_TEMPLATES

def test_pii_detection():
    # Aadhaar (12 digits with spaces or no spaces)
    assert Guardrails.check_pii("My aadhaar is 1234 5678 9012") == True
    assert Guardrails.check_pii("123456789012") == True
    
    # PAN (5 letters, 4 digits, 1 letter)
    assert Guardrails.check_pii("My PAN is ABCDE1234F") == True
    
    # Phone number (10 digits starting with 6-9)
    assert Guardrails.check_pii("Call me at 9876543210") == True
    
    # Email
    assert Guardrails.check_pii("Email me at test@example.com") == True
    
    # Safe queries
    assert Guardrails.check_pii("What is the expense ratio?") == False
    assert Guardrails.check_pii("HDFC Mid Cap Fund details") == False

def test_advisory_intent():
    # Advisory queries
    assert Guardrails.check_advisory("Should I invest in HDFC Mid Cap Fund?") == True
    assert Guardrails.check_advisory("Which fund is better — HDFC Mid Cap or Small Cap?") == True
    assert Guardrails.check_advisory("Predict the NAV of HDFC Mid Cap next month") == True
    assert Guardrails.check_advisory("Is this a good for me to buy?") == True
    
    # Safe queries
    assert Guardrails.check_advisory("What is the expense ratio of HDFC Mid Cap?") == False
    assert Guardrails.check_advisory("Tell me the exit load") == False

def test_performance_query():
    # Performance queries
    assert Guardrails.check_performance("What are the 3-year returns of HDFC Large Cap?") == True
    assert Guardrails.check_performance("Show me the CAGR") == True
    assert Guardrails.check_performance("What is the nav history?") == True
    
    # Safe queries
    assert Guardrails.check_performance("What is the expense ratio?") == False
    assert Guardrails.check_performance("What is the minimum SIP amount?") == False

def test_out_of_scope():
    # Out of scope funds
    assert Guardrails.check_in_scope("Tell me about SBI Blue Chip Fund") == False
    assert Guardrails.check_in_scope("ICICI prudential mutual fund") == False
    
    # In scope queries
    assert Guardrails.check_in_scope("What is the expense ratio of HDFC Mid Cap Fund?") == True
    assert Guardrails.check_in_scope("What is the exit load?") == True

def test_run_all():
    # PII
    is_refused, msg, cat = Guardrails.run_all("Here is my PAN ABCDE1234F")
    assert is_refused == True
    assert msg == REFUSAL_TEMPLATES["PII"]
    assert cat == "pii"
    
    # Advisory
    is_refused, msg, cat = Guardrails.run_all("Which fund should I buy?")
    assert is_refused == True
    assert msg == REFUSAL_TEMPLATES["Advisory"]
    assert cat == "advisory"
    
    # Performance
    is_refused, msg, cat = Guardrails.run_all("What are the 3-year returns?")
    assert is_refused == True
    assert msg == REFUSAL_TEMPLATES["Performance"]
    assert cat == "performance"
    
    # Out of Scope
    is_refused, msg, cat = Guardrails.run_all("Tell me about SBI fund")
    assert is_refused == True
    assert msg == REFUSAL_TEMPLATES["Out of Scope"]
    assert cat == "out_of_scope"
    
    # Safe
    is_refused, msg, cat = Guardrails.run_all("What is the minimum SIP amount for HDFC Large Cap Fund?")
    assert is_refused == False
    assert msg is None
    assert cat is None
