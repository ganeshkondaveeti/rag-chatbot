import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage

load_dotenv()

def test_groq():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key or api_key.startswith("gsk_xxxx"):
        print("Skipping Groq test: Please set a valid GROQ_API_KEY in .env")
        return

    print("Testing Groq API connectivity...")
    model_name = os.getenv("GROQ_MODEL", "llama3-8b-8192") # Fallback to a fast model if not set
    try:
        chat = ChatGroq(temperature=0, model_name=model_name)
        response = chat.invoke([HumanMessage(content="Hello, are you there? Reply with just 'Yes'.")])
        print(f"Success! Response: {response.content}")
    except Exception as e:
        print(f"Failed to connect to Groq: {e}")

if __name__ == "__main__":
    test_groq()
