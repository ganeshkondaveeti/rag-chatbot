import json
import os
import glob
from typing import List, Dict, Any
from langchain_text_splitters import RecursiveCharacterTextSplitter

class DocumentChunker:
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""]
        )

    def chunk_section(self, section: Dict[str, Any], metadata_template: Dict[str, str]) -> List[Dict[str, Any]]:
        """
        Chunks a single section. Keeps small sections whole, splits large sections.
        Returns a list of chunk dictionaries with content and metadata.
        """
        content = section["content"]
        section_name = section["section_name"]
        
        # Metadata specific to this section
        metadata = metadata_template.copy()
        metadata["section"] = section_name

        chunks = []
        
        if len(content) <= self.chunk_size:
            # Keep small sections whole (e.g. NAV, Tax Info, Fund Details)
            chunks.append({
                "content": content,
                "metadata": metadata
            })
        else:
            # Split large sections (e.g. Fund Overview)
            text_chunks = self.splitter.split_text(content)
            for text_chunk in text_chunks:
                chunks.append({
                    "content": text_chunk,
                    "metadata": metadata.copy()
                })
                
        return chunks

    def process_file(self, filepath: str) -> List[Dict[str, Any]]:
        """
        Reads a processed JSON file and chunks all its sections.
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        metadata_template = {
            "scheme_name": data["scheme_name"],
            "source_url": data["source_url"],
            "scrape_date": data["scrape_date"]
        }
        
        all_chunks = []
        for section in data.get("sections", []):
            all_chunks.extend(self.chunk_section(section, metadata_template))
            
        return all_chunks

    def process_directory(self, directory: str) -> List[Dict[str, Any]]:
        """
        Processes all JSON files in the given directory.
        """
        all_chunks = []
        files = glob.glob(os.path.join(directory, "*.json"))
        for filepath in files:
            all_chunks.extend(self.process_file(filepath))
        return all_chunks

if __name__ == "__main__":
    # Simple test script
    chunker = DocumentChunker()
    processed_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data", "processed")
    chunks = chunker.process_directory(processed_dir)
    print(f"Total chunks generated: {len(chunks)}")
    for i, chunk in enumerate(chunks[:3]):
        print(f"\nChunk {i+1}:")
        print(f"Metadata: {chunk['metadata']}")
        print(f"Content length: {len(chunk['content'])}")
        print(f"Content: {repr(chunk['content'][:100])}...")
