from langchain_groq import ChatGroq
from src.config import config

class LLMClient:
    def __init__(self):
        if not config.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY is not set.")
            
        self.llm = ChatGroq(
            api_key=config.GROQ_API_KEY,
            model=config.GROQ_MODEL,
            temperature=0.0,
            max_tokens=256,
            timeout=30,
            max_retries=2
        )
        
    def generate(self, prompt: str) -> str:
        """Generates a response from the LLM based on the prompt."""
        response = self.llm.invoke(prompt)
        return response.content
