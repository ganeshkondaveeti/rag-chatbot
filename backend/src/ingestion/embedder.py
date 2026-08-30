import os
from typing import List
from langchain_google_genai import GoogleGenerativeAIEmbeddings
class Embedder:
    """
    Wrapper around Gemini Embeddings.
    """
    def __init__(self, model_name: str = "models/gemini-embedding-001"):
        if "GOOGLE_API_KEY" not in os.environ:
            raise ValueError("GOOGLE_API_KEY environment variable not set.")
            
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model=model_name
        )

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self.embeddings.embed_documents(texts)

    def embed_query(self, query: str) -> List[float]:
        return self.embeddings.embed_query(query)
