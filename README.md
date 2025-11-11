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
**Agent Framework**: LangGraph (Multi-Agent System)
**Data Sources**: Scryfall API, Magic: The Gathering Comprehensive Rules
**Vector Store**: Qdrant (with OpenAI embeddings)
**LLM**: OpenAI GPT-4o-mini (configurable)
**Backend**: Python + FastAPI
**Frontend**: React (Vite)
**Rate Limiting**: slowapi
**Testing**: ragas for RAG evaluation

🧩 Project Structure
```
stack-sage/
├── backend/
│   ├── api/                # FastAPI server
│   ├── cli/                # CLI entry point
│   ├── core/               # Multi-agent system & RAG
│   │   ├── agents/         # Specialized agents
│   │   └── ...
│   ├── data/               # Rules PDF & vector DB
│   └── requirements.txt
├── frontend/               # React + Vite UI
├── Makefile                # Development commands
├── dev.sh                  # Start both servers
└── env.example             # Environment template
```

---

## 🚀 Quickstart

### Prerequisites
- Python 3.9+
- Node.js 18+
- OpenAI API key

### 1. Clone and Setup Environment

```bash
git clone <your-repo-url>
cd Stack_Sage

# Copy environment template and add your API key
cp env.example .env
# Edit .env and add: OPENAI_API_KEY=sk-...
```

### 2. Install Dependencies

```bash
make install
```

Or manually:
```bash
cd backend && pip install -r requirements.txt
cd ../frontend && npm install
```

### 3. Build Vector Store (First Time Only)

```bash
python rebuild_vector_store.py
```

This indexes the MTG Comprehensive Rules into Qdrant (~2-3 minutes).

### 4. Start Development Servers

```bash
make dev
```

Or manually:
```bash
# Terminal 1 - Backend
make backend

# Terminal 2 - Frontend  
make frontend
```

**URLs:**
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## 💰 Model Costs

Stack Sage uses **gpt-4o-mini** by default for cost efficiency:

| Model | Input (per 1M tokens) | Output (per 1M tokens) | Use Case |
|-------|----------------------|------------------------|----------|
| **gpt-4o-mini** | $0.15 | $0.60 | Default (fast, cheap) |
| gpt-4o | $2.50 | $10.00 | Complex reasoning |
| gpt-3.5-turbo | $0.50 | $1.50 | Legacy option |

**Estimated costs per query:**
- Simple question: ~$0.001-0.003 (gpt-4o-mini)
- Complex interaction: ~$0.005-0.01 (gpt-4o-mini)

Change model in `.env`:
```bash
LLM_MODEL=gpt-4o  # For better reasoning
```

---

## 🛠️ Development Commands

```bash
make install   # Install all dependencies
make dev       # Run backend + frontend (parallel)
make backend   # Run only backend server
make frontend  # Run only frontend dev server
make clean     # Remove cache files
make help      # Show all commands
```

---

## 🔧 Troubleshooting

### "No API key found"
**Problem:** Missing or invalid OpenAI API key

**Solution:**
1. Copy `env.example` to `.env`
2. Add your key: `OPENAI_API_KEY=sk-...`
3. Restart the server

### "Collection not found" or "Vector store empty"
**Problem:** Rules haven't been indexed

**Solution:**
```bash
python rebuild_vector_store.py
```

### "Rate limit exceeded"
**Problem:** API has rate limiting (10 requests/minute per IP)

**Solution:**
- Wait 60 seconds between bursts
- Adjust in `backend/api/server.py` (line 159):
  ```python
  @limiter.limit("20/minute")  # Increase limit
  ```

### CORS errors in browser
**Problem:** Frontend can't reach backend

**Solution:**
```bash
# In .env, add your frontend URL:
CORS_ALLOW_ORIGINS=http://localhost:5173,http://localhost:3000
```

### Slow responses
**Problem:** Large context or cold start

**Solutions:**
- Use `gpt-4o-mini` (default, 5x faster than gpt-4o)
- Reduce retrieved chunks in `backend/core/config.py`
- First query after startup is slower (model loading)

---

## 🧙‍♂️ Vision

"Every ruling, explained like you're sitting across the table from a friendly Level 3 Judge."

Stack Sage aims to make Magic's intricate rules accessible to players, judges, and developers alike — a bridge between human understanding and the logical beauty of the stack.
