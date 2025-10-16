"""
Document loader for MTG Comprehensive Rules.

This module loads the Magic: The Gathering Comprehensive Rules PDF
and extracts the text content.
"""

from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader


def load_pdf(file_path: str = None):
    """
    Load a PDF file and return a list of documents.
    
    Args:
        file_path: Path to the PDF file. If None, uses default rules PDF.
        
    Returns:
        List of Document objects from the PDF
    """
    if file_path is None:
        # Default to the Comprehensive Rules PDF
        file_path = Path(__file__).parent.parent / "data" / "MagicCompRules.pdf"
    
    loader = PyPDFLoader(str(file_path))
    return loader.load()


if __name__ == "__main__":
    print("Loading MTG Comprehensive Rules PDF...")
    docs = load_pdf()
    print(f"Loaded {len(docs)} pages")
    print(f"\nFirst page preview:\n{docs[0].page_content[:500]}...")