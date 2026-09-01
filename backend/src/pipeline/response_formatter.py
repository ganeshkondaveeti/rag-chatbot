import re
from typing import List, Dict, Any, Optional

class ResponseFormatter:
    @staticmethod
    def format_response(raw_response: str, context_chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Formats the raw LLM response.
        1. Ensures it is max 3 sentences.
        2. Extracts source URL and scrape date from context.
        3. Appends footer.
        """
        # Split into sentences and keep max 3.
        # This is a naive sentence splitter, but works well enough for simple text.
        sentences = re.split(r'(?<=[.!?]) +', raw_response.strip())
        
        # Sometime sentences are empty due to split
        sentences = [s.strip() for s in sentences if s.strip()]
        
        # Keep only up to 3 sentences
        truncated = " ".join(sentences[:3])
        
        # Get source metadata from the top context chunk
        source_url = None
        scrape_date = None
        if context_chunks:
            top_chunk = context_chunks[0]
            metadata = top_chunk.get("metadata", {})
            source_url = metadata.get("source_url")
            scrape_date = metadata.get("scrape_date")
            
        final_response = truncated
        
        if source_url and scrape_date:
            footer = f"\n\n🔗 Source: [{source_url}]({source_url})\n📅 Last updated from sources: {scrape_date}"
            final_response += footer
            
        return {
            "answer": final_response,
            "source_url": source_url,
            "last_updated": scrape_date,
            "refused": False,
            "refusal_category": None
        }
