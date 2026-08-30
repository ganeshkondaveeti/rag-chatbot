import os
from typing import List, Dict, Any
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document

class VectorStoreManager:
    def __init__(self, embeddings, collection_name: str = "mf_facts"):
        """
        Initializes the ChromaDB vector store.
        Uses $CHROMA_PERSIST_DIR if set, otherwise defaults to 'backend/data/chroma_db'.
        """
        self.embeddings = embeddings
        self.collection_name = collection_name
        
        # Determine persistence directory
        default_persist_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data", "chroma_db")
        self.persist_directory = os.environ.get("CHROMA_PERSIST_DIR", default_persist_dir)
        
        os.makedirs(self.persist_directory, exist_ok=True)
        
        # Initialize Langchain Chroma wrapper
        self.db = Chroma(
            collection_name=self.collection_name,
            embedding_function=self.embeddings,
            persist_directory=self.persist_directory
        )

    def reset_collection(self):
        """Deletes all documents from the collection (for re-ingestion)."""
        try:
            # We can retrieve all ids to delete them, or drop the collection.
            # In latest langchain-chroma, you can clear it using Chroma's client
            self.db.delete_collection()
            
            # Re-initialize after deletion
            self.db = Chroma(
                collection_name=self.collection_name,
                embedding_function=self.embeddings,
                persist_directory=self.persist_directory
            )
            print(f"Successfully reset collection '{self.collection_name}'.")
        except Exception as e:
            print(f"Error resetting collection: {e}")

    def upsert_chunks(self, chunks: List[Dict[str, Any]]):
        """
        Takes a list of dictionaries (with 'content' and 'metadata') and upserts them into ChromaDB.
        """
        documents = []
        ids = []
        
        for i, chunk in enumerate(chunks):
            # Create a unique ID: {scheme_slug}_{section}_{index}
            scheme_name = chunk["metadata"].get("scheme_name", "unknown")
            section = chunk["metadata"].get("section", "unknown")
            
            # Slugify strings for clean IDs
            scheme_slug = scheme_name.lower().replace(" ", "-")
            section_slug = section.lower().replace(" ", "-")
            
            doc_id = f"{scheme_slug}_{section_slug}_{i}"
            
            doc = Document(
                page_content=chunk["content"],
                metadata=chunk["metadata"]
            )
            
            documents.append(doc)
            ids.append(doc_id)
            
        if documents:
            self.db.add_documents(documents=documents, ids=ids)
            print(f"Successfully upserted {len(documents)} chunks to '{self.collection_name}'.")
            
    def get_collection_count(self) -> int:
        """Returns the number of documents in the collection."""
        return len(self.db.get()['ids'])
