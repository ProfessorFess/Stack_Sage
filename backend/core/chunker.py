from langchain_text_splitters import RecursiveCharacterTextSplitter
from backend.core.document_loader import load_pdf

def chunk_text(text: str, chunk_size: int = 700, chunk_overlap: int = 100) -> list[str]:
    """
    Chunk text into smaller segments for processing.
    
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