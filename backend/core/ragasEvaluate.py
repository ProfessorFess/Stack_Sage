"""
Ragas Evaluation Script for Stack Sage RAG Pipeline

This script evaluates the agentic RAG pipeline using Ragas metrics to measure
tool call accuracy, response quality, and goal adherence across diverse MTG questions.
"""

from ragas import evaluate, EvaluationDataset, SingleTurnSample
from ragas.metrics import (
    ResponseRelevancy,
    Faithfulness,
    FactualCorrectness,
    LLMContextRecall,
    ContextEntityRecall,
    NoiseSensitivity
)
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from ragas.integrations.langgraph import convert_to_ragas_messages
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.messages import HumanMessage
from backend.core.rag_pipeline import agent
from backend.core.config import config


# Test dataset: diverse MTG questions covering all agent capabilities
TEST_QUESTIONS = [
    # Simple card lookups (Easy)
    {
        "question": "What does Lightning Bolt do?",
        "reference": "Lightning Bolt is an instant that deals 3 damage to any target for one red mana.",
        "difficulty": "easy"
    },
    {
        "question": "What is the mana cost of Counterspell?",
        "reference": "Counterspell costs two blue mana (UU).",
        "difficulty": "easy"
    },
    {
        "question": "What type of card is Sol Ring?",
        "reference": "Sol Ring is an artifact that taps for two colorless mana.",
        "difficulty": "easy"
    },
    
    # Controller logic (Medium-Hard)
    {
        "question": "If my opponent controls Blood Artist, and one of my creatures dies, what happens?",
        "reference": "Your opponent gains 1 life (because they control Blood Artist), and your opponent chooses a target player to lose 1 life (likely targeting you).",
        "difficulty": "hard"
    },
    {
        "question": "If my opponent has Doubling Season and I cast a planeswalker, does it enter with double loyalty?",
        "reference": "No, Doubling Season only affects permanents its controller controls. Since your opponent controls Doubling Season and you control the planeswalker, it enters with normal loyalty.",
        "difficulty": "hard"
    },
    
    # Multi-card interactions (Medium-Hard)
    {
        "question": "How do Rest in Peace and Leyline of the Void interact?",
        "reference": "Both are graveyard hate enchantments that prevent cards from going to graveyards. Rest in Peace exiles cards instead of going to graveyards as a replacement effect, while Leyline of the Void exiles opponent cards. They work together but Rest in Peace affects all players.",
        "difficulty": "medium"
    },
    {
        "question": "If I cast Counterspell targeting my opponent's Lightning Bolt, what happens?",
        "reference": "Lightning Bolt is countered and goes to the graveyard instead of resolving. The damage is not dealt.",
        "difficulty": "easy"
    },
    {
        "question": "Can I use Path to Exile on my own creature?",
        "reference": "Yes, you can target your own creature with Path to Exile. It will be exiled and you will search your library for a basic land card.",
        "difficulty": "medium"
    },
    
    # Rules queries (Medium)
    {
        "question": "How does the stack work?",
        "reference": "The stack is a zone where spells and abilities wait to resolve. Objects on the stack resolve in last-in-first-out order. Players can respond to items on the stack by adding more spells or abilities.",
        "difficulty": "medium"
    },
    {
        "question": "What are state-based actions?",
        "reference": "State-based actions are game rules that are automatically checked and applied whenever a player would receive priority. Examples include creatures with 0 or less toughness dying, players with 0 or less life losing, and legends being removed if multiples exist.",
        "difficulty": "medium"
    },
    {
        "question": "What is first strike and how does it work?",
        "reference": "First strike is a keyword ability that lets a creature deal combat damage before creatures without first strike. If a creature with first strike deals lethal damage, the opposing creature won't deal damage back.",
        "difficulty": "easy"
    },
    
    # Format legality (Easy)
    {
        "question": "Is Black Lotus legal in Vintage?",
        "reference": "Yes, Black Lotus is legal but restricted (limited to 1 copy) in Vintage.",
        "difficulty": "easy"
    },
    {
        "question": "Can I play Counterspell in Standard?",
        "reference": "No, Counterspell is not legal in Standard. It's legal in Legacy, Vintage, Commander, and other eternal formats.",
        "difficulty": "easy"
    },
    
    # Card search criteria (Medium)
    {
        "question": "What 2-mana blue counterspell is the most famous?",
        "reference": "Counterspell is the most famous 2-mana blue counterspell.",
        "difficulty": "medium"
    },
    {
        "question": "What red creatures cost 3 red mana (no colorless mana)?",
        "reference": "Examples include Goblin Chainwhirler, Mogg Mob, Hell-Fire Horde, and Ball Lightning.",
        "difficulty": "medium"
    },
    
    # Complex rules (Hard)
    {
        "question": "If I control a creature with lifelink and deathtouch, and it's blocked by a 5/5 creature, what happens?",
        "reference": "Your creature deals damage equal to its power. Deathtouch means any amount of damage is lethal, so the 5/5 dies. Lifelink means you gain life equal to the damage dealt.",
        "difficulty": "hard"
    },
    {
        "question": "Can I respond to someone casting a spell?",
        "reference": "You cannot respond while they are casting the spell, but once it's on the stack, you receive priority and can respond with instants or abilities before it resolves.",
        "difficulty": "medium"
    },
    
    # Edge cases (Hard)
    {
        "question": "What happens if two players would simultaneously lose the game?",
        "reference": "If multiple players would lose simultaneously in a multiplayer game, those players all lose. In a two-player game, the game is a draw.",
        "difficulty": "hard"
    },
]


def run_agent_and_extract_data(question: str) -> dict:
    """
    Execute the agent and extract data for Ragas evaluation.
    
    Returns dict with:
        - response: Final answer
        - retrieved_contexts: List of contexts from tools
        - messages: Full message trace
    """
    print(f"\n🤔 Processing: {question[:60]}...")
    
    try:
        # Invoke agent with full message trace
        result = agent.invoke(
            {"messages": [HumanMessage(content=question)]},
            config={"recursion_limit": 15}
        )
        
        messages = result.get("messages", [])
        
        # Extract retrieved contexts from tool calls
        retrieved_contexts = []
        for msg in messages:
            # Check for tool responses (ToolMessage)
            if hasattr(msg, 'type') and msg.type == 'tool':
                if hasattr(msg, 'content') and msg.content:
                    # Add tool output as context
                    retrieved_contexts.append(msg.content)
        
        # Extract final response
        final_response = None
        for msg in reversed(messages):
            if hasattr(msg, 'type') and msg.type == 'ai':
                if not (hasattr(msg, 'tool_calls') and msg.tool_calls):
                    if hasattr(msg, 'content') and msg.content:
                        final_response = msg.content.strip()
                        break
        
        if not final_response:
            final_response = "No response generated"
        
        # Clean up response (remove tool usage footer)
        if "---" in final_response and "Tools Used" in final_response:
            final_response = final_response.split("---")[0].strip()
        
        return {
            "response": final_response,
            "retrieved_contexts": retrieved_contexts if retrieved_contexts else ["No context retrieved"],
            "messages": messages
        }
        
    except Exception as e:
        print(f"❌ Error processing question: {e}")
        return {
            "response": f"Error: {str(e)}",
            "retrieved_contexts": ["Error occurred"],
            "messages": []
        }


def create_evaluation_dataset() -> EvaluationDataset:
    """
    Create Ragas evaluation dataset by running agent on test questions.
    """
    print("\n" + "="*80)
    print("🧪 RAGAS EVALUATION - STACK SAGE RAG PIPELINE")
    print("="*80)
    print(f"\n📊 Running {len(TEST_QUESTIONS)} test questions...\n")
    
    samples = []
    
    for i, test_case in enumerate(TEST_QUESTIONS, 1):
        question = test_case["question"]
        reference = test_case["reference"]
        difficulty = test_case["difficulty"]
        
        print(f"\n[{i}/{len(TEST_QUESTIONS)}] Difficulty: {difficulty.upper()}")
        
        # Run agent and extract data
        result = run_agent_and_extract_data(question)
        
        # Create Ragas sample
        sample = SingleTurnSample(
            user_input=question,
            response=result["response"],
            retrieved_contexts=result["retrieved_contexts"],
            reference=reference
        )
        
        samples.append(sample)
        print(f"✅ Completed")
    
    print("\n" + "="*80)
    print(f"✅ Dataset created with {len(samples)} samples")
    print("="*80)
    
    return EvaluationDataset(samples=samples)


def run_evaluation():
    """
    Run Ragas evaluation with configured metrics and judge LLM.
    """
    # Create evaluation dataset
    dataset = create_evaluation_dataset()
    
    print("\n" + "="*80)
    print("⚙️  CONFIGURING EVALUATION METRICS")
    print("="*80)
    
    # Configure judge LLM (gpt-4o-mini)
    evaluator_llm = LangchainLLMWrapper(
        ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
            openai_api_key=config.OPENAI_API_KEY
        )
    )
    
    # Configure embeddings for context-based metrics
    evaluator_embeddings = LangchainEmbeddingsWrapper(
        OpenAIEmbeddings(
            model="text-embedding-3-small",
            openai_api_key=config.OPENAI_API_KEY
        )
    )
    
    # Define metrics
    metrics = [
        LLMContextRecall(llm=evaluator_llm),
        Faithfulness(llm=evaluator_llm),
        FactualCorrectness(llm=evaluator_llm),
        ResponseRelevancy(llm=evaluator_llm, embeddings=evaluator_embeddings),
        ContextEntityRecall(llm=evaluator_llm),
        NoiseSensitivity(llm=evaluator_llm),
    ]
    
    print("\n📋 Metrics configured:")
    for metric in metrics:
        print(f"  - {metric.__class__.__name__}")
    
    print("\n" + "="*80)
    print("🚀 RUNNING EVALUATION")
    print("="*80)
    print("\nThis may take several minutes...\n")
    
    # Run evaluation
    results = evaluate(
        dataset=dataset,
        metrics=metrics,
        llm=evaluator_llm,
        embeddings=evaluator_embeddings,
    )
    
    # Display results
    print("\n" + "="*80)
    print("📊 EVALUATION RESULTS")
    print("="*80)
    
    # Convert results to pandas DataFrame for better display
    df = results.to_pandas()
    
    # Show aggregate metrics
    print("\n🎯 AGGREGATE METRICS:")
    print("-" * 80)
    
    metric_columns = [col for col in df.columns if col not in ['user_input', 'response', 'retrieved_contexts', 'reference']]
    
    for col in metric_columns:
        if col in df.columns:
            mean_score = df[col].mean()
            print(f"  {col:30s}: {mean_score:.3f}")
    
    # Show per-question results
    print("\n" + "="*80)
    print("📝 PER-QUESTION RESULTS:")
    print("="*80)
    
    for idx, row in df.iterrows():
        print(f"\n[Q{idx+1}] {row['user_input'][:70]}...")
        print(f"  Response: {row['response'][:100]}...")
        print(f"  Scores:")
        for col in metric_columns:
            if col in row:
                print(f"    - {col:28s}: {row[col]:.3f}")
    
    # Summary statistics
    print("\n" + "="*80)
    print("📈 SUMMARY STATISTICS")
    print("="*80)
    
    total_questions = len(df)
    print(f"\n  Total Questions Evaluated: {total_questions}")
    
    # Count high-performing responses (avg score > 0.7)
    avg_scores = df[metric_columns].mean(axis=1)
    high_quality = (avg_scores > 0.7).sum()
    medium_quality = ((avg_scores >= 0.5) & (avg_scores <= 0.7)).sum()
    low_quality = (avg_scores < 0.5).sum()
    
    print(f"\n  Quality Distribution:")
    print(f"    - High Quality (>0.7):   {high_quality} questions ({high_quality/total_questions*100:.1f}%)")
    print(f"    - Medium Quality (0.5-0.7): {medium_quality} questions ({medium_quality/total_questions*100:.1f}%)")
    print(f"    - Low Quality (<0.5):    {low_quality} questions ({low_quality/total_questions*100:.1f}%)")
    
    print("\n" + "="*80)
    print("✅ EVALUATION COMPLETE")
    print("="*80)
    
    return results


if __name__ == "__main__":
    # Run the evaluation
    results = run_evaluation()

