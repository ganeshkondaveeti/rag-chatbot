import re
from typing import List, Dict, Any, Optional
from src.ingestion.vectorstore import VectorStoreManager

SCHEME_ALIASES = {
    "HDFC Mid Cap Fund": ["hdfc mid cap", "mid cap fund", "midcap"],
    "HDFC Small Cap Fund": ["hdfc small cap", "small cap fund", "smallcap"],
    "HDFC Gold ETF FoF": ["hdfc gold", "gold etf", "gold fund", "gold fof"],
    "HDFC Large Cap Fund": ["hdfc large cap", "large cap fund", "largecap"],
    "HDFC ELSS Tax Saver Fund": ["hdfc elss", "tax saver", "elss fund"],
}

class Retriever:
    def __init__(self, vectorstore_manager: VectorStoreManager):
        self.vectorstore_manager = vectorstore_manager

    def extract_scheme_name(self, query: str) -> Optional[str]:
        """
        Extracts the scheme name from the user query based on known aliases.
        Returns the canonical scheme name or None.
        """
        query_lower = query.lower()
        
        # We need to sort by longest alias first to prevent partial matches
        # but the simple loop usually suffices since we return on first match.
        for canonical_name, aliases in SCHEME_ALIASES.items():
            for alias in aliases:
                if alias in query_lower:
                    return canonical_name
        return None

    def retrieve(self, query: str, top_k: int = 3, fallback_top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieves relevant chunks from ChromaDB.
        Uses metadata filtering if a scheme name is detected in the query.
        """
        # 1. Try to extract scheme name
        scheme_name = self.extract_scheme_name(query)
        
        # 2. Configure search kwargs
        search_kwargs = {}
        if scheme_name:
            search_kwargs["k"] = top_k
            search_kwargs["filter"] = {"scheme_name": scheme_name}
        else:
            search_kwargs["k"] = fallback_top_k
            
        # 3. Perform similarity search
        db = self.vectorstore_manager.db
        
        # Since we're using Google Generative AI Embeddings, we might need a specific query prefix
        # We'll just search the raw query as the embedding model is configured correctly.
        results = db.similarity_search(query, **search_kwargs)
        
        # 4. Format results
        formatted_results = []
        for doc in results:
            formatted_results.append({
                "content": doc.page_content,
                "metadata": doc.metadata
            })
            
        return formatted_results

class QueryPipeline:
    def __init__(self, retriever: Retriever):
        self.retriever = retriever
        
    def process_query(self, query: str) -> Dict[str, Any]:
        """
        Runs the full query pipeline: Guardrails -> Retriever
        """
        from src.pipeline.guardrails import Guardrails
        
        # 1. Run Guardrails
        is_refused, refusal_msg, refusal_category = Guardrails.run_all(query)
        if is_refused:
            return {
                "refused": True,
                "refusal_category": refusal_category,
                "refusal_message": refusal_msg,
                "context": []
            }
            
        # 2. Retrieve context
        context = self.retriever.retrieve(query)
        
        return {
            "refused": False,
            "refusal_category": None,
            "refusal_message": None,
            "context": context
        }
