import os
import sys
import json
from dotenv import load_dotenv

load_dotenv()

# Ensure backend directory is in the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.src.config import config
from backend.src.ingestion.embedder import Embedder
from backend.src.ingestion.vectorstore import VectorStoreManager

def main():
    print("Initializing components...\n")
    embedder = Embedder(model_name=config.EMBEDDING_MODEL)
    vsm = VectorStoreManager(embedder.embeddings)
    
    collection = vsm.db.get(include=['embeddings', 'metadatas', 'documents'])
    
    total_chunks = len(collection['ids'])
    print(f"Total chunks in ChromaDB: {total_chunks}")
    
    if total_chunks > 0:
        print("\n--- Sample Chunk (First Item) ---")
        sample_id = collection['ids'][0]
        sample_doc = collection['documents'][0]
        sample_meta = collection['metadatas'][0]
        sample_emb = collection['embeddings'][0]
        
        print(f"ID: {sample_id}")
        print(f"Metadata: {json.dumps(sample_meta, indent=2)}")
        print(f"Content Length: {len(sample_doc)} chars")
        print(f"Content Snippet: {sample_doc[:150]}...")
        print(f"Embedding Dimension: {len(sample_emb)}")
        print(f"Embedding Values (first 5): {sample_emb[:5]}")
        print("-" * 33)
        
    print("\n--- Example Retrieval ---")
    query = "What is the expense ratio of HDFC Mid-Cap Opportunities Fund?"
    print(f"Query: '{query}'\n")
    
    results = vsm.db.similarity_search_with_score(query, k=2)
    for i, (doc, score) in enumerate(results):
        print(f"Result {i+1} (Score/Distance: {score:.4f}):")
        print(f"  Source: {doc.metadata.get('scheme_name')} - {doc.metadata.get('section')}")
        print(f"  Snippet: {doc.page_content[:200]}...")
        print()

if __name__ == "__main__":
    main()
