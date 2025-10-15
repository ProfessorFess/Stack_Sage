📘 Stack Sage

An intelligent Magic: The Gathering rules companion powered by retrieval-augmented generation (RAG).

Stack Sage is an AI-powered MTG rules assistant that can explain complex card interactions, stack resolutions, and game mechanics in plain language.
By combining official Comprehensive Rules data with live card information from the Scryfall API, it reasons step-by-step through questions like:

“What happens if I copy Dockside Extortionist with Spark Double?”
“Does Rest in Peace stop Unearth?”

Stack Sage retrieves the relevant cards and rule sections, interprets their relationships, and generates a clear, citation-backed explanation — just like a digital judge who never sleeps.

🧠 Core Features
	•	RAG-Driven Reasoning — combines card data and rules text using a retrieval-augmented LLM pipeline.
	•	Contextual Rule Retrieval — semantically searches the Comprehensive Rules by rule numbers and topics.
	•	Dynamic Card Lookup — pulls up-to-date Oracle text and rulings from the Scryfall API.
	•	Structured Explanations — outputs results with summaries, rule references, and reasoning steps.
	•	CLI Interface (current phase) — query directly from your terminal:
    •	Future Plans: FastAPI backend, React frontend, and “Judge Mode” for formal rule citations.

⚙️ Tech Stack
Data: Scryfall API, Magic: The Gathering Comprehensive Rules
Retrieval: ChromaDB (Vector Store), tiktoken (tokenizer)
Reasoning: Some Compatible LLM (Undecided)
Backend: Python (Expressed via CLI → FastAPI later)
Frontend: React (Vite) [planned]

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
