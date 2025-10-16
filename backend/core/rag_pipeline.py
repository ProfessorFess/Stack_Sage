from backend.core.llm_client import MTGLLMClient
from backend.core.retriever import MTGRetriever
from backend.core.scryfall import get_card_context, extract_card_names
from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict, List
from langchain_core.documents import Document

retriever = MTGRetriever()
llm_client = MTGLLMClient()

class State(TypedDict):
    question: str
    card_context: str
    rules_context: List[Document]
    response: str

def fetch_cards(state: State) -> State:
    """
    Fetch card information from Scryfall.
    """
    card_context = get_card_context(state["question"])
    return {"card_context": card_context}

def retrieve_rules(state: State) -> State:
    """
    Retrieve relevant rules from vector store.
    """
    rules_context = retriever.get_relevant_documents(state["question"])
    return {"rules_context": rules_context}

def generate(state: State) -> State:
    """
    Generate the answer to the question.
    """
    # Combine card and rules context
    full_context = ""
    if state.get("card_context"):
        full_context += state["card_context"] + "\n\n"
    
    # Add rules context
    rules_str = "\n\n".join([doc.page_content for doc in state.get("rules_context", [])])
    if rules_str:
        full_context += "=== RELEVANT RULES ===\n\n" + rules_str
    
    response = llm_client.generate_answer(state["question"], full_context)
    return {"response": response}

def end(state: State) -> State:
    """
    End the pipeline.
    """
    return {"response": state["response"]}

def check_context_quality(state: State) -> str:
    """
    Route based on the quality/length of retrieved context.
    """
    has_cards = bool(state.get("card_context"))
    has_rules = bool(state.get("rules_context"))
    
    if not has_cards and not has_rules:
        return "no_context"
    return "has_context"

def no_context_response(state: State) -> State:
    """
    Handle case where there is no retrieved context.
    """
    return {"response": "I could not find any relevant information to answer your question."}

graph_builder = StateGraph(State)
graph_builder.add_node("fetch_cards", fetch_cards)
graph_builder.add_node("retrieve_rules", retrieve_rules)
graph_builder.add_node("generate", generate)
graph_builder.add_node("no_context", no_context_response)

# Start with card fetching
graph_builder.add_edge(START, "fetch_cards")
# Then retrieve rules
graph_builder.add_edge("fetch_cards", "retrieve_rules")
# Check if we have context
graph_builder.add_conditional_edges(
    "retrieve_rules",
    check_context_quality,
    {
        "has_context": "generate",
        "no_context": "no_context"
    }
)
graph_builder.add_edge("generate", END)
graph_builder.add_edge("no_context", END)

graph = graph_builder.compile()

if __name__ == "__main__":
    print(graph.invoke({"question": "What is the effect of Rest in Peace?"}))