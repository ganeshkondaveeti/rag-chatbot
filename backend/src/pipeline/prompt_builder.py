from typing import List, Dict, Any

SYSTEM_PROMPT_TEMPLATE = """
You are a facts-only mutual fund FAQ assistant for HDFC mutual fund schemes available on Groww. You must follow these rules strictly:

RULES:
1. Answer ONLY using the provided context. Do NOT use prior knowledge.
2. Respond in a MAXIMUM of 3 sentences.
3. Include EXACTLY ONE source citation URL from the context metadata at the end.
4. If the context does not contain the answer, respond EXACTLY with:
   "I don't have this information in my current data. Please visit {source_url} for the latest details."
5. NEVER provide investment advice, opinions, recommendations, or performance comparisons.

CONTEXT:
{context_str}

USER QUERY:
{query}
"""

class PromptBuilder:
    @staticmethod
    def build_prompt(query: str, context_chunks: List[Dict[str, Any]]) -> str:
        """
        Builds the final prompt string using the system template, the user query, and the retrieved context.
        """
        if not context_chunks:
            context_str = "No context available."
        else:
            context_pieces = []
            for i, chunk in enumerate(context_chunks):
                content = chunk.get("content", "")
                metadata = chunk.get("metadata", {})
                source_url = metadata.get("source_url", "Unknown")
                scrape_date = metadata.get("scrape_date", "Unknown")
                
                piece = f"--- Chunk {i+1} ---\nContent: {content}\nSource: {source_url}\nScraped: {scrape_date}"
                context_pieces.append(piece)
                
            context_str = "\n\n".join(context_pieces)
            
        # We also want to pass a generic fallback URL if context is empty, but we can just use Groww's main mutual funds page.
        fallback_url = "https://groww.in/mutual-funds"
        if context_chunks:
            fallback_url = context_chunks[0].get("metadata", {}).get("source_url", fallback_url)
            
        prompt = SYSTEM_PROMPT_TEMPLATE.format(
            context_str=context_str,
            query=query,
            source_url=fallback_url
        )
        return prompt
