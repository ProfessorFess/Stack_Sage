"""
LLM client for generating answers using retrieved context.

This module handles the generation of answers using OpenAI/Anthropic,
combining retrieved rules and card information into coherent responses.
"""

from typing import Optional
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from backend.core.config import config


class MTGLLMClient:
    """LLM client for Magic: The Gathering rules questions."""
    
    def __init__(self, model: Optional[str] = None, temperature: Optional[float] = None):
        """
        Initialize the LLM client.
        
        Args:
            model: LLM model to use (defaults to config)
            temperature: Temperature for generation (defaults to config)
        """
        self.model = model or config.LLM_MODEL
        self.temperature = temperature or config.LLM_TEMPERATURE
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            model=self.model,
            temperature=self.temperature,
            openai_api_key=config.OPENAI_API_KEY
        )
        
        # Create prompt template
        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", """You are Stack Sage, an expert Magic: The Gathering rules assistant.

You help players understand complex card interactions and game rules by providing clear, accurate explanations based on the official Comprehensive Rules and card oracle text.

Your responses should:
- Be accurate and cite relevant rules when possible
- Explain complex interactions step-by-step
- Use the provided context (cards and rules) to answer questions
- Be concise but complete
- Say "I don't have enough information" if the context doesn't contain the answer

Always base your answers on the provided context below."""),
            ("human", """Context Information:

{context}

Question: {question}

Please provide a clear, accurate answer based on the context above.""")
        ])
    
    def generate_answer(self, question: str, context: str) -> str:
        """
        Generate an answer using the LLM with retrieved context.
        
        Args:
            question: User's question
            context: Retrieved context (cards + rules)
            
        Returns:
            Generated answer
        """
        # Format the prompt with context and question
        messages = self.prompt_template.format_messages(
            context=context,
            question=question
        )
        
        # Generate response
        response = self.llm.invoke(messages)
        
        return response.content
    
    def generate_answer_stream(self, question: str, context: str):
        """
        Generate an answer with streaming (for CLI display).
        
        Args:
            question: User's question
            context: Retrieved context (cards + rules)
            
        Yields:
            Chunks of the generated answer
        """
        messages = self.prompt_template.format_messages(
            context=context,
            question=question
        )
        
        for chunk in self.llm.stream(messages):
            yield chunk.content


def create_llm_client() -> MTGLLMClient:
    """
    Create and return an LLM client instance.
    
    Returns:
        Configured MTGLLMClient
    """
    return MTGLLMClient()


# Example usage
if __name__ == "__main__":
    print("=" * 60)
    print("🤖 LLM Client Test")
    print("=" * 60)
    
    # Initialize client
    client = create_llm_client()
    print(f"\n✓ Initialized LLM: {client.model}")
    print(f"✓ Temperature: {client.temperature}\n")
    
    # Test with sample context
    test_question = "What happens when Rest in Peace is on the battlefield and a creature dies?"
    
    test_context = """=== RELEVANT CARDS ===

**Rest in Peace**
Type: Enchantment
Mana Cost: {1}{W}
Oracle Text: When this enchantment enters, exile all graveyards.
If a card or token would be put into a graveyard from anywhere, exile it instead.

Rulings:
1. While Rest in Peace is on the battlefield, abilities that trigger whenever a creature dies won't trigger because cards and tokens are never put into a player's graveyard.

=== RELEVANT RULES ===

700.4. The term dies means "is put into a graveyard from the battlefield."

704.5f If a creature has toughness 0 or less, it's put into its owner's graveyard. Regeneration can't replace this event.
"""
    
    print("=" * 60)
    print(f"Question: {test_question}")
    print("=" * 60)
    
    print("\n📝 Generating answer...\n")
    answer = client.generate_answer(test_question, test_context)
    
    print("Answer:")
    print("-" * 60)
    print(answer)
    print("-" * 60)
