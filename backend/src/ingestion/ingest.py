import os
import sys
from dotenv import load_dotenv

load_dotenv()

# Ensure backend directory is in the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from src.ingestion.chunker import DocumentChunker
from src.ingestion.embedder import Embedder
from src.ingestion.vectorstore import VectorStoreManager

async def main():
    print("--- Starting Ingestion Pipeline ---")
    
    # 0. Scrape Data
    from src.scraper.groww_scraper import GrowwScraper
    print("Scraping latest data from Groww...")
    scraper = GrowwScraper()
    await scraper.run_all()
    
    # 1. Initialize Chunker
    print("Initializing chunker...")
    chunker = DocumentChunker()
    processed_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data", "processed")
    
    # 2. Chunk Data
    print(f"Reading and chunking JSON files from {processed_dir}...")
    chunks = chunker.process_directory(processed_dir)
    print(f"Generated {len(chunks)} chunks.")
    
    # 3. Initialize Embedder
    print("Initializing Gemini embedder...")
    embedder = Embedder()
    embeddings = embedder.embeddings
    
    # 4. Initialize Vector Store
    print("Initializing ChromaDB...")
    vectorstore = VectorStoreManager(embeddings=embeddings)
    
    # 5. Reset and Upsert
    print("Resetting existing collection...")
    vectorstore.reset_collection()
    
    print("Upserting chunks to ChromaDB...")
    vectorstore.upsert_chunks(chunks)
    
    count = vectorstore.get_collection_count()
    print(f"--- Ingestion Complete ---")
    print(f"Total documents in ChromaDB collection '{vectorstore.collection_name}': {count}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
