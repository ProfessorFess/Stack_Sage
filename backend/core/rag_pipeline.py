"""
Agentic RAG Pipeline for Stack Sage

This module implements an agentic approach to MTG rules assistance using LangGraph.
The agent can dynamically choose which tools to use based on the user's question.
"""

from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from backend.core.config import config
from backend.core.tools import ALL_TOOLS


# Create the agentic LLM with tools
def create_mtg_agent():
    """
    Create the Stack Sage agentic assistant.
    
    This agent has access to a toolbelt of MTG-specific tools and can
    autonomously decide which tools to use based on the user's question.
    
    Returns:
        Compiled LangGraph agent
    """
    # Initialize the LLM with lower temperature for more consistent tool usage
    llm = ChatOpenAI(
        model=config.LLM_MODEL,
        temperature=0.1,  # Lower temperature = more deterministic, follows instructions better
        openai_api_key=config.OPENAI_API_KEY
    )
    
    # Create the ReAct agent with the tools
    # Note: The system prompt is set via prompt parameter, not state_modifier
    from langchain_core.prompts import ChatPromptTemplate
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are Stack Sage, an expert Magic: The Gathering rules assistant with access to specialized tools.

**Your Tools:**
- search_rules: Search MTG Comprehensive Rules
- lookup_card: Get card details by name
- search_cards_by_criteria: Find cards by attributes (color, mana cost, P/T, format)
- check_format_legality: Check if a card is legal in a format
- compare_multiple_cards: Analyze card interactions
- search_mtg_meta: Search web for current meta/tournament data

**Guidelines:**
- Use tools to verify information and provide accurate answers
- For card names: use lookup_card or search_cards_by_criteria
- For game rules: use search_rules  
- For format questions: use check_format_legality
- For meta/popularity: use search_mtg_meta

After using tools to gather information, provide a clear answer without showing the tool usage process."""),
        ("placeholder", "{messages}"),
    ])
    
    agent = create_react_agent(llm, ALL_TOOLS, prompt=prompt)
    
    return agent


# Create the global agent instance
agent = create_mtg_agent()


# Legacy interface for backward compatibility with CLI
class AgentWrapper:
    """Wrapper to provide the same interface as the old graph."""
    
    def __init__(self, agent):
        self.agent = agent
    
    def invoke(self, state: dict) -> dict:
        """
        Invoke the agent with a question.
        
        Args:
            state: Dictionary with 'question' key
            
        Returns:
            Dictionary with 'response' key
        """
        question = state.get("question", "")
        
        if not question:
            return {"response": "Please ask a question about Magic: The Gathering."}
        
        try:
            # Invoke the agent with the question
            # Set recursion limit to allow reasonable tool chaining
            result = self.agent.invoke(
                {"messages": [HumanMessage(content=question)]},
                config={"recursion_limit": 15}  # Limit tool chaining to prevent loops
            )
            
            # Extract ONLY the final answer, not the reasoning/tool calls
            messages = result.get("messages", [])
            
            # Track which tools were used
            tools_used = []
            for msg in messages:
                if hasattr(msg, 'tool_calls') and msg.tool_calls:
                    for tool_call in msg.tool_calls:
                        tool_name = tool_call.get('name', 'unknown')
                        if tool_name not in tools_used:
                            tools_used.append(tool_name)
            
            # Filter to get only the final AI response (not tool calls or reasoning)
            final_response = None
            for msg in reversed(messages):  # Start from the end
                # Look for AIMessage that's not a tool call
                if hasattr(msg, 'type') and msg.type == 'ai':
                    # Check if this is a final answer (not a tool call)
                    if hasattr(msg, 'tool_calls') and msg.tool_calls:
                        # This is a tool call, skip it
                        continue
                    
                    # This is the final answer
                    if hasattr(msg, 'content') and msg.content:
                        # Clean up any remaining agent reasoning artifacts
                        content = msg.content
                        
                        # Remove any remaining tool call syntax
                        import re
                        # Remove patterns like [Assistant to=functions.tool_name]
                        content = re.sub(r'\[Assistant to=functions\.\w+\].*?\n', '', content)
                        # Remove JSON-like tool call syntax
                        content = re.sub(r'\{[^}]*"query"[^}]*\}', '', content)
                        
                        final_response = content.strip()
                        break
            
            if final_response:
                # Add tools used section if any tools were called
                if tools_used:
                    final_response += f"\n\n---\n\n🔧 **Tools Used**: {', '.join(tools_used)}"
                else:
                    # Debug: add message if no tools were used (shouldn't happen with our strict prompts)
                    final_response += f"\n\n---\n\n⚠️ **Note**: No tools were used (this might indicate an issue)"
                
                return {"response": final_response}
            else:
                # Fallback: try to get any AI message content
                for msg in reversed(messages):
                    if hasattr(msg, 'content') and msg.content and len(msg.content) > 20:
                        response = msg.content
                        if tools_used:
                            response += f"\n\n{'─'*60}\n🔧 **Tools Used**: {', '.join(tools_used)}"
                        return {"response": response}
                
                return {"response": "I encountered an error processing your question."}
            
        except Exception as e:
            error_msg = str(e)
            
            # Handle recursion limit specifically
            if "recursion" in error_msg.lower() or "GRAPH_RECURSION_LIMIT" in error_msg:
                return {
                    "response": """🔄 Agent Complexity Limit Reached

The agent tried too many steps to answer your question.

**What to do:**
1. ✅ Try asking a more specific question
2. ✅ Break complex questions into smaller parts
3. ✅ Ask about one card or concept at a time

**Examples:**
- Instead of: "compare all red creatures in standard"
- Try: "what are good 3-mana red creatures in standard"

Please rephrase and try again! 💡"""
                }
            
            # Handle rate limiting specifically
            if "rate_limit" in error_msg.lower() or "429" in error_msg:
                return {
                    "response": """⏱️ Rate Limit Exceeded

I tried to answer your question but hit OpenAI's rate limit (too many tokens used in a short time).

**What to do:**
1. ✅ Wait a few seconds and ask again
2. ✅ Try a simpler/more specific question
3. ✅ For meta questions, make them more focused

**Why this happened:**
Your question likely triggered multiple tool calls (web search + card lookups), 
which used a lot of tokens quickly.

**Tip:** Instead of "top 3 cards in standard", try:
- "what 3-mana creatures are popular in standard"
- "is [specific card] good in standard"

Please try again in a few seconds! 🕐"""
                }
            
            # Generic error handling
            return {"response": f"Error: {str(e)}\n\nPlease try rephrasing your question."}


# Create wrapped graph instance for backward compatibility
graph = AgentWrapper(agent)

if __name__ == "__main__":
    print(graph.invoke({"question": "What is the effect of Rest in Peace?"}))