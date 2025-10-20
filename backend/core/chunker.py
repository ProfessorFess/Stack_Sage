from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from backend.core.document_loader import load_pdf
import re
from typing import List

def extract_rule_metadata(text: str) -> dict:
    """
    Extract rule number and title from a chunk.
    
    Args:
        text: Text chunk to analyze
        
    Returns:
        Dict with rule_number, title, and keywords
    """
    metadata = {
        "rule_number": None,
        "title": None,
        "keywords": []
    }
    
    # Match rule numbers like "405.", "405.1", "100.6a"
    rule_match = re.search(r'^(\d{3,}\.\w*)', text.strip(), re.MULTILINE)
    if rule_match:
        metadata["rule_number"] = rule_match.group(1)
    
    # Extract title from first line if it looks like a header
    first_line = text.split('\n')[0].strip()
    if len(first_line) < 100 and (first_line.istitle() or first_line.isupper()):
        metadata["title"] = first_line
    
    # Extract keywords for common MTG concepts
    concept_keywords = [
        "stack", "priority", "state-based", "combat", "mana", "tap", "untap",
        "triggered", "activated", "static", "replacement", "phase", "step",
        "turn", "upkeep", "draw", "main", "attack", "block", "damage",
        "graveyard", "exile", "library", "hand", "battlefield", "command zone"
    ]
    
    text_lower = text.lower()
    for keyword in concept_keywords:
        if keyword in text_lower:
            metadata["keywords"].append(keyword)
    
    return metadata

def chunk_mtg_rules(text: str, chunk_size: int = 800, chunk_overlap: int = 150) -> List[Document]:
    """
    Chunk MTG Comprehensive Rules with rule-aware splitting.
    
    Splits on rule headers while preserving section numbers and titles.
    Returns Documents with rich metadata for better retrieval.
    
    Args:
        text: The full rules text
        chunk_size: Target size for chunks
        chunk_overlap: Overlap between chunks
        
    Returns:
        List of Document objects with metadata
    """
    # First, try to split on major rule boundaries
    # Pattern: Rule numbers like "405." or "100.6a" at start of line
    rule_pattern = r'(?=^\d{3,}\.\w*\s+)'
    
    # Split on rule headers
    rule_sections = re.split(rule_pattern, text, flags=re.MULTILINE)
    
    documents = []
    
    for section in rule_sections:
        if not section.strip():
            continue
        
        # If section is small enough, keep it as one chunk
        if len(section) <= chunk_size:
            metadata = extract_rule_metadata(section)
            doc = Document(
                page_content=section.strip(),
                metadata=metadata
            )
            documents.append(doc)
        else:
            # Section is too large, need to split further
            # But preserve the rule header in each sub-chunk
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                separators=["\n\n", "\n", ". ", " ", ""],
                length_function=len,
            )
            
            sub_chunks = splitter.split_text(section)
            base_metadata = extract_rule_metadata(section)
            
            for i, sub_chunk in enumerate(sub_chunks):
                # Update metadata for sub-chunks
                metadata = base_metadata.copy()
                metadata["sub_chunk"] = i
                metadata.update(extract_rule_metadata(sub_chunk))
                
                doc = Document(
                    page_content=sub_chunk.strip(),
                    metadata=metadata
                )
                documents.append(doc)
    
    return documents

def chunk_text(text: str, chunk_size: int = 700, chunk_overlap: int = 100) -> list[str]:
    """
    Legacy function - chunk text into smaller segments.
    
    Args:
        text: The text to chunk.
        chunk_size: The size of each chunk.
        chunk_overlap: The overlap between chunks.
        
    Returns:
        List of text chunks.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
    )
    return splitter.split_text(text)

if __name__ == "__main__":
    print("Chunking MTG Comprehensive Rules PDF...")
    docs = load_pdf()
    print(f"Loaded {len(docs)} pages")
    
    # Combine all pages into one text
    full_text = "\n\n".join([doc.page_content for doc in docs])
    print(f"Total characters: {len(full_text):,}")
    
    # Chunk the full text
    chunks = chunk_text(full_text)
    print(f"Chunked into {len(chunks)} segments")
    
    print(f"\nFirst chunk preview:\n{chunks[0][:200]}...")
    print(f"\nLast chunk preview:\n...{chunks[-1][-200:]}")