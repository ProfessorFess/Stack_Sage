# Stack Sage Backend Setup Guide

## Environment Setup

### 1. Virtual Environment

A virtual environment has been created at `backend/venv/`.

**To activate the virtual environment:**

```bash
# From the backend directory
cd backend
source venv/bin/activate
```

**To deactivate:**
```bash
deactivate
```

### 2. Environment Variables

API keys and configuration are managed through environment variables.

**Set up your `.env` file:**

```bash
# From the project root
cp .env.example .env
```

Then edit `.env` and add your API key:

```bash
# For OpenAI
OPENAI_API_KEY=sk-proj-your_actual_key_here
LLM_PROVIDER=openai
LLM_MODEL=gpt-4

# OR for Anthropic Claude
ANTHROPIC_API_KEY=sk-ant-your_actual_key_here
LLM_PROVIDER=anthropic
LLM_MODEL=claude-3-5-sonnet-20241022
```

### 3. Using Configuration in Code

```python
from backend.core.config import config

# Access settings
api_key = config.get_api_key()
model = config.LLM_MODEL
chroma_dir = config.CHROMA_PERSIST_DIRECTORY

# Validate configuration
config.validate()
```

### 4. Testing Configuration

```bash
# With venv activated
python -m core.config
```

## Installed Packages

- `python-dotenv` - Environment variable management
- `chromadb` - Vector database for embeddings
- `openai` - OpenAI API client
- `anthropic` - Anthropic Claude API client
- `tiktoken` - Tokenizer for counting tokens
- `requests` - HTTP library for API calls

## Next Steps

1. ✅ Virtual environment created
2. ✅ Dependencies installed
3. ⏭️ Create your `.env` file
4. ⏭️ Add your API key
5. ⏭️ Start building your RAG pipeline!

## Troubleshooting

**If you need to reinstall packages:**
```bash
source venv/bin/activate
pip install -r requirements.txt
```

**If you need to update packages:**
```bash
source venv/bin/activate
pip install --upgrade -r requirements.txt
```

