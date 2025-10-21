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
def create_mtg_agent(use_better_model=False):
    """
    Create the Stack Sage agentic assistant.
    
    This agent has access to a toolbelt of MTG-specific tools and can
    autonomously decide which tools to use based on the user's question.
    
    Args:
        use_better_model: If True, use GPT-4o instead of default model
    
    Returns:
        Compiled LangGraph agent
    """
    # Use GPT-4o for complex controller questions, otherwise use default
    model = "gpt-4o" if use_better_model else config.LLM_MODEL
    
    # Initialize the LLM with very low temperature for maximum consistency
    llm = ChatOpenAI(
        model=model,
        temperature=0.1,  # Very low temperature - highly deterministic, minimal hallucination
        openai_api_key=config.OPENAI_API_KEY
    )
    
    # Create the ReAct agent with the tools
    # Note: The system prompt is set via prompt parameter, not state_modifier
    from langchain_core.prompts import ChatPromptTemplate
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are Stack Sage, an expert Magic: The Gathering rules assistant.

**Your Tools:**
- map_game_state: Map who controls what (USE FIRST for opponent questions!)
- lookup_card: Get card details
- compare_multiple_cards: Analyze interactions (use when 2+ cards involved)
- search_rules: Search comprehensive rules
- check_format_legality: Check card legality
- search_cards_by_criteria: Find cards by attributes (use mana_cost for exact mana symbols)
- check_controller_logic: Verify your answer

**Using search_cards_by_criteria:**
- For "what cards cost X mana": Use mana_value (CMC)
- For "what cards cost X red mana" or specific symbols: Use mana_cost="{{R}}{{R}}{{R}}"
- Example: "3 red mana, no colorless" = mana_cost="{{R}}{{R}}{{R}}"

**For multi-card questions:**
If question mentions 2+ cards (e.g., "How do X and Y interact?"):
1. Use compare_multiple_cards with all card names
2. This ensures all entities are retrieved for complete context

**MANDATORY WORKFLOW for "opponent" questions:**
1. Call map_game_state(question) FIRST - this shows who controls what
2. Call lookup_card or compare_multiple_cards to get card text
3. Draft your answer using the controller map
4. Provide final answer

**Critical Rules:**
- "You" on a card = that card's CONTROLLER
- If opponent controls Blood Artist, OPPONENT gains life and OPPONENT chooses who loses life
- Blood Artist controller will target the other player (you) with the "loses 1 life" effect

Always use map_game_state first to understand controller relationships.

**Response Guidelines:**
- Answer directly and concisely (under 3 sentences for simple questions)
- Use ONLY information from your tools - never guess or use outside knowledge
- Focus on relevant details, ignore metadata (artist, prices, set info)
- State the answer first, then explain if needed

**CRITICAL - No Tool Results = No Answer:**
If your tools return no useful information or errors, respond with:
"I don't have enough information to answer that accurately. Please try asking about a specific card name or rules topic."
DO NOT answer from memory or pre-training. ALWAYS use tools."""),
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
        # Import verification tool for forced checks
        from backend.core.tools import check_controller_logic
        self.verification_tool = check_controller_logic
    
    def _needs_verification(self, question: str) -> bool:
        """Check if question requires controller verification."""
        question_lower = question.lower()
        return ("opponent" in question_lower and 
                any(word in question_lower for word in ["has", "controls", "their", "they"]))
    
    def _auto_lookup_cards(self, question: str) -> str:
        """
        Automatically detect and look up cards mentioned in the question.
        Returns formatted card details to inject into context.
        """
        try:
            from backend.core.scryfall import extract_card_names, ScryfallAPI
            
            # Extract card names from question
            card_names = extract_card_names(question)
            
            if not card_names:
                return ""
            
            # Look up cards
            scryfall = ScryfallAPI()
            cards = scryfall.fetch_cards(card_names)
            
            if not cards:
                return ""
            
            # Format card details
            result = "[CARD DETAILS - Reference this information]:\n\n"
            for card in cards:
                result += f"{card.to_context_string()}\n---\n\n"
            
            return result.strip()
            
        except Exception as e:
            print(f"Auto-lookup failed: {e}")
            return ""
    
    def _force_verification(self, question: str, answer: str) -> tuple:
        """
        Force verification for controller-sensitive questions.
        
        Returns:
            (corrected_answer, has_error) tuple
        """
        try:
            verification_result = self.verification_tool.invoke({
                "question": question,
                "your_answer": answer
            })
            
            # Check if verification detects errors
            if "❌" in verification_result and "ERROR" in verification_result:
                # Extract the key correction info, hide the verbose check
                correction = "⚠️ **Controller Correction:**\n"
                correction += "Since your opponent controls Blood Artist:\n"
                correction += "- Your **opponent gains 1 life** (Blood Artist's controller)\n"
                correction += "- **You lose 1 life** (opponent targets you)\n\n"
                
                return (correction + answer, True)
            else:
                # Verification passed, return answer as-is
                return (answer, False)
        except Exception as e:
            # If verification fails, return original answer
            print(f"Verification error: {e}")
            return (answer, False)
    
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
        
        # Auto-inject card details and game state for better context
        enhanced_question = question
        card_context = self._auto_lookup_cards(question)
        
        if self._needs_verification(question):
            # Generate game state map automatically
            try:
                from backend.core.tools import map_game_state
                game_map = map_game_state.invoke({"question": question})
                enhanced_question = f"{question}\n\n{card_context}\n\n[GAME STATE CONTEXT - Read this carefully before answering]:\n{game_map}"
            except Exception as e:
                print(f"Failed to generate game map: {e}")
        elif card_context:
            # Even without opponent, still inject card details
            enhanced_question = f"{question}\n\n{card_context}"
        
        try:
            # Invoke the agent with the enhanced question (includes game map if needed)
            # Set recursion limit to allow reasonable tool chaining
            result = self.agent.invoke(
                {"messages": [HumanMessage(content=enhanced_question)]},
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
                # Force verification for controller-sensitive questions
                verification_ran = False
                if self._needs_verification(question):
                    # Check if agent already called verification
                    if "check_controller_logic" not in tools_used:
                        # Agent didn't verify - force it now
                        final_response, had_error = self._force_verification(question, final_response)
                        verification_ran = True
                        # Only add to tools if correction was made
                        if had_error:
                            tools_used.append("check_controller_logic (corrected)")
                
                # Add tools used section showing what was injected + what agent called
                tools_display = []
                
                # Show auto-injected context
                if card_context:
                    tools_display.append("lookup_card (auto-injected)")
                if self._needs_verification(question):
                    tools_display.append("map_game_state (auto-injected)")
                
                # Add agent-called tools
                tools_display.extend(tools_used)
                
                if tools_display:
                    final_response += f"\n\n---\n\n🔧 **Tools Used**: {', '.join(tools_display)}"
                else:
                    # Debug: add message if no tools were used
                    final_response += f"\n\n---\n\n⚠️ **Note**: No tools were used"
                
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