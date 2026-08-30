import re
from typing import Tuple, Optional

# Regex Patterns for PII
PII_PATTERNS = {
    "PAN": r"[A-Z]{5}[0-9]{4}[A-Z]",
    "Aadhaar": r"\b\d{4}\s?\d{4}\s?\d{4}\b",
    "Phone": r"\b[6-9]\d{9}\b",
    "Email": r"\b[\w.-]+@[\w.-]+\.\w+\b",
}

# Keywords for Advisory Intent
ADVISORY_KEYWORDS = [
    "should", "recommend", "suggest", "better", "best",
    "compare", "which fund", "buy", "sell", "hold", 
    "prediction", "forecast", "advice", "good for me", "predict"
]

# Keywords for Performance Queries
PERFORMANCE_KEYWORDS = [
    "returns", "cagr", "nav history", "performance", "yield", "profit"
]

# Keywords for In-Scope Queries (HDFC funds)
SCOPE_KEYWORDS = [
    "hdfc", "mid cap", "midcap", "small cap", "smallcap", 
    "gold etf", "gold fof", "large cap", "largecap", "elss", "tax saver"
]

REFUSAL_TEMPLATES = {
    "PII": "I cannot process personal or sensitive information. Please do not share PII such as PAN, Aadhaar, or account numbers.",
    "Advisory": "I'm a facts-only assistant and cannot provide investment advice or recommendations. For investment guidance, please visit [AMFI Investor Corner](https://www.amfiindia.com/investor-corner/knowledge-center).",
    "Performance": "I don't provide performance data or return calculations. For the latest returns, please refer to the official factsheet.",
    "Out of Scope": "I can only answer factual questions about the 5 HDFC mutual fund schemes in my database. Please rephrase or visit [Groww](https://groww.in/mutual-funds) for other funds."
}

class Guardrails:
    @staticmethod
    def check_pii(query: str) -> bool:
        """Returns True if PII is detected."""
        for pattern in PII_PATTERNS.values():
            if re.search(pattern, query, re.IGNORECASE):
                return True
        return False

    @staticmethod
    def check_advisory(query: str) -> bool:
        """Returns True if advisory intent is detected."""
        query_lower = query.lower()
        for keyword in ADVISORY_KEYWORDS:
            if keyword in query_lower:
                return True
        return False

    @staticmethod
    def check_performance(query: str) -> bool:
        """Returns True if performance query is detected."""
        query_lower = query.lower()
        for keyword in PERFORMANCE_KEYWORDS:
            if keyword in query_lower:
                return True
        return False

    @staticmethod
    def check_in_scope(query: str) -> bool:
        """Returns True if the query is in scope (mentions an HDFC fund related keyword or general query).
        We keep it a bit loose so we don't reject general questions like 'what is the expense ratio?'
        If they explicitly ask about a non-HDFC fund, we'd ideally want to reject, but keyword 
        inclusion is safer. Actually, a better scope check is to see if any out of scope fund is mentioned,
        but for simplicity we check if ANY HDFC keyword is present OR if it's just a general question.
        We will implement a simple scope check: if it contains 'sbi', 'icici', 'axis', 'nippon', etc., out of scope.
        """
        query_lower = query.lower()
        out_of_scope_brands = ["sbi", "icici", "axis", "nippon", "kotak", "tata", "uti", "dsp", "mirae"]
        for brand in out_of_scope_brands:
            if brand in query_lower:
                return False
        return True

    @classmethod
    def run_all(cls, query: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Runs all guardrails.
        Returns: (is_refused, refusal_message, category)
        """
        if cls.check_pii(query):
            return True, REFUSAL_TEMPLATES["PII"], "pii"
        
        if cls.check_advisory(query):
            return True, REFUSAL_TEMPLATES["Advisory"], "advisory"
            
        if cls.check_performance(query):
            return True, REFUSAL_TEMPLATES["Performance"], "performance"
            
        if not cls.check_in_scope(query):
            return True, REFUSAL_TEMPLATES["Out of Scope"], "out_of_scope"
            
        return False, None, None
