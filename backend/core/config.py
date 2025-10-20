"""
Configuration management for Stack Sage.

This module loads environment variables and provides a centralized
configuration object for the application.
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
# Look for .env in the project root (two levels up from this file)
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


class Config:
    """Application configuration."""
    
    # ============================================
    # Environment
    # ============================================
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # ============================================
    # LLM Configuration
    # ============================================
    # API Keys
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
    COHERE_API_KEY: Optional[str] = os.getenv("COHERE_API_KEY")
    HUGGINGFACE_API_KEY: Optional[str] = os.getenv("HUGGINGFACE_API_KEY")
    
    # ============================================
    # Search API Configuration
    # ============================================
    TAVILY_API_KEY: Optional[str] = os.getenv("TAVILY_API_KEY")
    
    # LLM Settings
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "openai")
    # Default to gpt-4o-mini for cost efficiency (17x cheaper than gpt-4o)
    # Options: "gpt-4o-mini" (cheap, fast), "gpt-4o" (better reasoning), "gpt-3.5-turbo" (cheapest)
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o-mini")
    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.5"))
    LLM_MAX_TOKENS: int = int(os.getenv("LLM_MAX_TOKENS", "2000"))
    
    # ============================================
    # ChromaDB Configuration
    # ============================================
    CHROMA_PERSIST_DIRECTORY: str = os.getenv(
        "CHROMA_PERSIST_DIRECTORY",
        str(Path(__file__).parent.parent / "data" / "chroma_db")
    )
    CHROMA_COLLECTION_NAME: str = os.getenv("CHROMA_COLLECTION_NAME", "mtg_rules")
    
    # ============================================
    # Logging
    # ============================================
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    @classmethod
    def get_api_key(cls) -> str:
        """
        Get the API key for the configured LLM provider.
        
        Returns:
            str: The API key for the current provider.
            
        Raises:
            ValueError: If no API key is found for the configured provider.
        """
        provider_key_map = {
            "openai": cls.OPENAI_API_KEY,
            "anthropic": cls.ANTHROPIC_API_KEY,
            "cohere": cls.COHERE_API_KEY,
            "huggingface": cls.HUGGINGFACE_API_KEY,
        }
        
        api_key = provider_key_map.get(cls.LLM_PROVIDER.lower())
        
        if not api_key:
            raise ValueError(
                f"No API key found for provider '{cls.LLM_PROVIDER}'. "
                f"Please set the appropriate API key in your .env file."
            )
        
        return api_key
    
    @classmethod
    def validate(cls) -> bool:
        """
        Validate that required configuration is present.
        
        Returns:
            bool: True if configuration is valid.
            
        Raises:
            ValueError: If required configuration is missing.
        """
        try:
            cls.get_api_key()
            return True
        except ValueError as e:
            raise ValueError(f"Configuration validation failed: {e}")


# Create a singleton instance
config = Config()


if __name__ == "__main__":
    # Quick test to verify configuration
    print("Stack Sage Configuration")
    print("=" * 50)
    print(f"Environment: {config.ENVIRONMENT}")
    print(f"LLM Provider: {config.LLM_PROVIDER}")
    print(f"LLM Model: {config.LLM_MODEL}")
    print(f"ChromaDB Directory: {config.CHROMA_PERSIST_DIRECTORY}")
    print(f"Log Level: {config.LOG_LEVEL}")
    
    try:
        config.validate()
        print("\n✓ Configuration is valid!")
        print(f"✓ API key found for {config.LLM_PROVIDER}")
    except ValueError as e:
        print(f"\n✗ Configuration error: {e}")

