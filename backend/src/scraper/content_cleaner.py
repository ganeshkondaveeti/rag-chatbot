import re
from typing import Dict, Any, List

class ContentCleaner:
    def __init__(self):
        # PII Regex patterns
        self.pii_patterns = {
            "pan": r'[A-Z]{5}[0-9]{4}[A-Z]{1}',
            "aadhaar": r'\b\d{4}\s?\d{4}\s?\d{4}\b',
            "phone": r'\b(?:\+91|91)?\s?[6-9]\d{9}\b',
            "email": r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        }
        
    def scrub_pii(self, text: str) -> str:
        """Removes PII from the text based on regex patterns."""
        if not text:
            return text
            
        clean_text = text
        for pii_type, pattern in self.pii_patterns.items():
            clean_text = re.sub(pattern, f'[REDACTED_{pii_type.upper()}]', clean_text)
            
        return clean_text

    def clean_html_text(self, text: str) -> str:
        """Normalizes whitespace and removes excessive blank lines."""
        if not text:
            return ""
        # Remove excessive whitespace and newlines
        clean_text = re.sub(r'\n+', '\n', text)
        clean_text = re.sub(r' +', ' ', clean_text)
        return clean_text.strip()
        
    def extract_data_points(self, text: str) -> Dict[str, Any]:
        """
        Attempts to heuristically extract key data points from raw text if possible.
        In a real scenario, this might rely on precise CSS selectors in the scraper,
        but having a fallback extractor is useful.
        """
        data_points = {}
        
        # Example heuristic extractions
        expense_ratio_match = re.search(r'Expense Ratio.*?([\d.]+%)', text, re.IGNORECASE)
        if expense_ratio_match:
            data_points["expense_ratio"] = expense_ratio_match.group(1)
            
        exit_load_match = re.search(r'Exit Load\s*([^%\n]*%?)', text, re.IGNORECASE)
        if exit_load_match:
            data_points["exit_load"] = exit_load_match.group(1).strip()
            
        aum_match = re.search(r'Fund Size.*?₹\s*([\d.,]+)\s*Cr', text, re.IGNORECASE)
        if aum_match:
            data_points["aum_cr"] = aum_match.group(1)
            
        return data_points

    def process_section(self, section_name: str, raw_text: str) -> Dict[str, Any]:
        """Processes a single section's text."""
        cleaned_text = self.clean_html_text(raw_text)
        safe_text = self.scrub_pii(cleaned_text)
        
        return {
            "section_name": section_name,
            "content": safe_text,
            "data_points": self.extract_data_points(safe_text)
        }
