📘 Stack Sage

An intelligent Magic: The Gathering rules companion powered by **agentic RAG** (Retrieval-Augmented Generation).

Stack Sage is an AI-powered MTG rules assistant that can explain complex card interactions, stack resolutions, and game mechanics in plain language.
Using an **autonomous agent** with a specialized toolbelt, it dynamically decides how to answer your question — looking up cards, searching rules, checking format legality, and more.

"What happens if I copy Dockside Extortionist with Spark Double?"
"Does Rest in Peace stop Unearth?"
"Is Black Lotus legal in Commander?"

Stack Sage autonomously retrieves the relevant information, reasons through complex interactions, and generates clear, citation-backed explanations — just like a digital judge who never sleeps.

🤖 What Makes Stack Sage Agentic?

Unlike traditional RAG pipelines that follow a fixed sequence, Stack Sage uses a **ReAct (Reasoning + Acting) agent** that:
- **Analyzes** your question to understand what information is needed
- **Decides** which tools to use (card lookup, rules search, legality checks, etc.)
- **Reasons** through complex interactions step-by-step
- **Verifies** its own answers for completeness
- **Adapts** its approach based on your specific question

→ See [AGENTIC_FEATURES.md](AGENTIC_FEATURES.md) for full details on the agentic system

🧠 Core Features
	•	**Agentic Intelligence** — autonomous decision-making with 9 specialized tools
	•	**Dynamic Tool Selection** — uses only what's needed for each question
	•	**Advanced Card Search** — find cards by attributes (color, mana cost, P/T, format)
	•	**Anti-Hallucination** — strict rules prevent making up card names or false information
	•	**Self-Verification** — can evaluate and improve its own answers
	•	RAG-Driven Reasoning — combines card data and rules text using retrieval-augmented LLM pipeline
	•	Contextual Rule Retrieval — semantically searches the Comprehensive Rules
	•	Dynamic Card Lookup — pulls up-to-date Oracle text and rulings from the Scryfall API
	•	Format Legality Checks — verify cards in Standard, Modern, Commander, etc.
	•	Web Search Integration — current meta trends and tournament results (optional)
	•	CLI Interface (current phase) — query directly from your terminal
    •	Future Plans: FastAPI backend, React frontend, and "Judge Mode" for formal rule citations

⚙️ Tech Stack
**Agent Framework**: LangGraph (ReAct Agent with Tool Calling)
**Data Sources**: Scryfall API, Magic: The Gathering Comprehensive Rules
**Vector Store**: Qdrant (with OpenAI embeddings)
**LLM**: OpenAI GPT-4 (configurable)
**Tools**: 9 specialized MTG tools (card search, rules lookup, legality checks, meta search, etc.)
**Backend**: Python (CLI → FastAPI later)
**Frontend**: React (Vite) [planned]

🧩 Project Structure
stack-sage/
├── backend/
│   ├── cli/                # CLI entry point
│   ├── core/               # RAG logic and data access
│   ├── data/               # rule chunks, PDFs, vector DB
│   ├── api/                # (future) FastAPI endpoints
│   └── requirements.txt
├── frontend/               # (future) React UI
└── README.md

🧙‍♂️ Vision

“Every ruling, explained like you’re sitting across the table from a friendly Level 3 Judge.”

Stack Sage aims to make Magic’s intricate rules accessible to players, judges, and developers alike — a bridge between human understanding and the logical beauty of the stack.
