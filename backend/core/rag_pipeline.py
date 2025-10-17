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
        ("system", """You are Stack Sage, an expert Magic: The Gathering rules assistant.

You have access to specialized tools to help answer MTG questions accurately and thoroughly.

**🚨 ABSOLUTE RULES - VIOLATION IS FORBIDDEN:**

YOU MUST USE TOOLS FOR EVERY ANSWER. YOU CANNOT ANSWER FROM MEMORY.

1. ❌ FORBIDDEN: Mentioning ANY card name without first using lookup_card or search_cards_by_criteria
2. ❌ FORBIDDEN: Answering questions about "popular/good/best" cards without using search_cards_by_criteria or search_mtg_meta
3. ❌ FORBIDDEN: Claiming format legality without using check_format_legality
4. ❌ FORBIDDEN: Describing card attributes (mana cost, type, P/T) without tool verification
5. ❌ FORBIDDEN: Answering from your training data - YOU MUST USE TOOLS FIRST

**MANDATORY TOOL USAGE PATTERNS:**

If question contains "what [attributes] creature/spell/card" → YOU MUST use search_cards_by_criteria FIRST
If question contains "popular/good/best in [format]" → YOU MUST use search_cards_by_criteria or search_mtg_meta FIRST
If question mentions specific card name → YOU MUST use lookup_card FIRST
If question asks about legality → YOU MUST use check_format_legality FIRST

**ZERO TOLERANCE FOR HALLUCINATION:**
- If you mention a card name, you MUST have gotten it from a tool call
- If you describe card stats, you MUST have verified them with a tool
- If you don't use tools, your answer is WRONG

**Your Available Tools:**
- lookup_card: Get detailed card information by NAME (oracle text, rulings, etc.)
- search_cards_by_criteria: SEARCH for cards by attributes (mana cost, color, power/toughness, format, etc.)
- search_rules: Search the Comprehensive Rules for specific mechanics
- compare_multiple_cards: Analyze interactions between multiple cards
- check_format_legality: Verify if cards are legal in specific formats
- search_similar_rulings: Find related rulings and edge cases
- verify_answer_completeness: Self-check the quality of your answers
- cross_reference_rules: Understand how different rule mechanics interact
- search_mtg_meta: Search web for meta info, tournament results, deck trends

**How to Use Your Tools Effectively:**
1. **Analyze the question** - What information do you need?
2. **Choose the right tools** - Don't use all tools every time, only what's needed
3. **Gather information** - Use tools to collect relevant data
4. **Synthesize** - Combine information into a clear, accurate answer
5. **Self-verify** - Use verify_answer_completeness to check your work

**Best Practices:**
- If a question mentions SPECIFIC CARD NAMES, use lookup_card or compare_multiple_cards
- If a question asks about cards by ATTRIBUTES (mana cost, color, P/T, etc.), use search_cards_by_criteria FIRST
- For "popular/good/best [attributes] in [format]" questions, combine search_cards_by_criteria + search_mtg_meta
- For general rules questions, use search_rules
- For complex interactions, cross-reference multiple rule topics
- ALWAYS verify format legality claims with check_format_legality
- Always provide step-by-step explanations for complex interactions
- Cite specific rules when possible (e.g., "Rule 104.3a states...")
- After generating an answer, consider using verify_answer_completeness to ensure quality

**Response Format:**
- Give a clean, direct answer without showing your tool usage or reasoning process
- Start with the answer immediately - don't say "Let me search..." or "I'll use..."
- Explain the mechanics step-by-step
- Cite relevant rules and rulings
- Address edge cases if relevant
- Keep explanations accessible but technically accurate
- DO NOT include tool call syntax, JSON, or debugging information in your final answer

**REQUIRED WORKFLOW EXAMPLES - FOLLOW THESE EXACTLY:**

Question type: "What 3-mana red creature is good in Standard?"
STEP 1 (MANDATORY): search_cards_by_criteria(colors="r", mana_value="3", format_legal="standard", card_type="creature")
STEP 2 (MANDATORY): Review the actual results from the tool
STEP 3 (MANDATORY): lookup_card on a specific card from the results
STEP 4: Answer ONLY with information from the tools

Question type: "How does Lightning Bolt work?"
STEP 1 (MANDATORY): lookup_card("Lightning Bolt")
STEP 2: Explain using ONLY the tool's response
FORBIDDEN: Don't answer from memory

Question type: "Is Sol Ring legal in Modern?"
STEP 1 (MANDATORY): check_format_legality("Sol Ring", "modern")
STEP 2: Report ONLY what the tool says
FORBIDDEN: Don't guess legality

**DETECTION PATTERNS - TRIGGER MANDATORY TOOL USE:**

Pattern: "what [number]-mana [color] creature" → MUST use search_cards_by_criteria
Pattern: "good/popular/best in [format]" → MUST use search_cards_by_criteria or search_mtg_meta
Pattern: "[card name]" → MUST use lookup_card
Pattern: "legal in [format]" → MUST use check_format_legality

IF YOU ANSWER WITHOUT USING THE APPROPRIATE TOOL, YOUR ANSWER IS AUTOMATICALLY WRONG.

**RESPONSE EXAMPLES:**

❌ BAD (shows reasoning):
"Let me search for that. [Assistant to=functions.search_rules] {{'query': 'starting life'}} 
According to the rules, players start with 20 life."

✅ GOOD (clean answer):
"In a standard game of Magic: The Gathering, each player starts with 20 life.

According to the Comprehensive Rules:
• Rule 103.3: Each player begins with a starting life total of 20
• Rule 903.2: In Commander format, players start with 40 life

Some variant formats have different starting totals."

Remember: USE TOOLS (mandatory), but DON'T SHOW the tool usage in your final answer!"""),
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
            result = self.agent.invoke({
                "messages": [HumanMessage(content=question)]
            })
            
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
                    final_response += f"\n\n{'─'*60}\n🔧 **Tools Used**: {', '.join(tools_used)}"
                
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