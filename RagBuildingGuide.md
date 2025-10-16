# Complete Guide to Building RAG Applications

Based on AI Engineering Bootcamp (AIE8) Course Materials

---

## Table of Contents
1. [Creating a Retriever](#1-creating-a-retriever)
2. [Setting Up LLM and Prompts](#2-setting-up-llm-and-prompts)
3. [Building RAG Chains](#3-building-rag-chains)
4. [Complete Examples](#4-complete-examples)

---

## 1. Creating a Retriever

A retriever is the "R" in RAG - it finds relevant documents from your knowledge base to provide context for the LLM.

### Step 1.1: Load Your Documents

**Option A: Text Files (Simple)**
```python
from langchain_community.document_loaders import TextLoader

loader = TextLoader("path/to/file.txt")
documents = loader.load()
```

**Option B: PDFs (Common)**
```python
from langchain_community.document_loaders import PyMuPDFLoader

loader = PyMuPDFLoader("path/to/file.pdf")
documents = loader.load()  # Returns list of Document objects
```

**Option C: YouTube Videos**
```python
from aimakerspace.text_utils import YouTubeLoader

loader = YouTubeLoader("https://youtube.com/watch?v=...", include_metadata=True)
documents = loader.load_documents()
```

### Step 1.2: Chunk Your Documents

Break large documents into smaller, manageable pieces.

**Simple Approach (Character-based)**
```python
from langchain.text_splitter import CharacterTextSplitter

text_splitter = CharacterTextSplitter(
    chunk_size=1000,      # Characters per chunk
    chunk_overlap=200     # Overlap to maintain context
)

chunks = text_splitter.split_documents(documents)
```

**Advanced Approach (Token-based with recursive splitting)**
```python
import tiktoken
from langchain.text_splitter import RecursiveCharacterTextSplitter

def tiktoken_len(text):
    """Count tokens using tiktoken"""
    tokens = tiktoken.get_encoding("cl100k_base").encode(text)
    return len(tokens)

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=750,           # Tokens per chunk
    chunk_overlap=0,          # No overlap
    length_function=tiktoken_len,
)

chunks = text_splitter.split_documents(documents)
```

**Key Chunking Principles:**
- Typical chunk size: 500-1500 characters/tokens
- Overlap helps preserve context across boundaries
- Too small → lose context; Too large → dilute relevance
- RecursiveCharacterTextSplitter splits on: `\n\n` → `\n` → ` ` → character

### Step 1.3: Set Up Embeddings

Convert text into vector representations for similarity search.

```python
from langchain_openai import OpenAIEmbeddings

# Most common embedding model (cheap and effective)
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

# Or for higher quality (more expensive)
embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
```

**Important:**
- `text-embedding-3-small`: 1536 dimensions, 8191 token context
- Always use the SAME embedding model for indexing and querying

### Step 1.4: Create Vector Database

Store your chunks with their embeddings for fast retrieval.

**Option A: In-Memory (Qdrant - Simple)**
```python
from langchain_community.vectorstores import Qdrant

vectorstore = Qdrant.from_documents(
    chunks,
    embeddings,
    location=":memory:",          # In-memory (not persistent)
    collection_name="my_docs"
)
```

**Option B: In-Memory (Qdrant - Advanced Setup)**
```python
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams

# Create client
client = QdrantClient(":memory:")

# Create collection with specific configuration
client.create_collection(
    collection_name="knowledge_base",
    vectors_config=VectorParams(
        size=1536,                # Embedding dimension
        distance=Distance.COSINE  # Distance metric
    ),
)

# Create vector store
vector_store = QdrantVectorStore(
    client=client,
    collection_name="knowledge_base",
    embedding=embeddings,
)

# Add documents
vector_store.add_documents(documents=chunks)
```

**Option C: Custom Vector Database (From Scratch)**
```python
from aimakerspace.vectordatabase import VectorDatabase
from aimakerspace.openai_utils.embedding import EmbeddingModel
import asyncio

# Create embedding model
embedding_model = EmbeddingModel()

# Create vector database
vector_db = VectorDatabase(embedding_model=embedding_model)

# Build from list of text chunks
vector_db = asyncio.run(vector_db.abuild_from_list(chunk_texts))

# Search by text
results = vector_db.search_by_text("your query here", k=3)
```

### Step 1.5: Create the Retriever

Convert your vector store into a retriever interface.

```python
# Basic retriever
retriever = vectorstore.as_retriever(
    search_kwargs={"k": 5}  # Return top 5 most similar chunks
)

# Test it
relevant_docs = retriever.invoke("What is machine learning?")
```

### Advanced Retrieval Options

**A. BM25 Retriever (Keyword-based)**
```python
from langchain_community.retrievers import BM25Retriever

bm25_retriever = BM25Retriever.from_documents(chunks)
bm25_retriever.k = 5  # Number of results
```

**B. Contextual Compression (Reranking)**
```python
from langchain.retrievers.contextual_compression import ContextualCompressionRetriever
from langchain_cohere import CohereRerank

# Create base retriever
base_retriever = vectorstore.as_retriever(search_kwargs={"k": 10})

# Add reranker
compressor = CohereRerank(model="rerank-v3.5")
compression_retriever = ContextualCompressionRetriever(
    base_compressor=compressor,
    base_retriever=base_retriever
)
```

**C. Multi-Query Retriever**
```python
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4.1-nano")
multi_query_retriever = MultiQueryRetriever.from_llm(
    retriever=vectorstore.as_retriever(),
    llm=llm
)
```

**D. Parent Document Retriever**
```python
from langchain.retrievers import ParentDocumentRetriever
from langchain.storage import InMemoryStore

# Create parent and child splitters
parent_splitter = RecursiveCharacterTextSplitter(chunk_size=2000)
child_splitter = RecursiveCharacterTextSplitter(chunk_size=400)

# Create document store for parents
store = InMemoryStore()

# Create retriever
parent_document_retriever = ParentDocumentRetriever(
    vectorstore=vectorstore,
    docstore=store,
    child_splitter=child_splitter,
)

# Add documents
parent_document_retriever.add_documents(documents)
```

---

## 2. Setting Up LLM and Prompts

### Step 2.1: Initialize the LLM

**OpenAI Models**
```python
from langchain_openai import ChatOpenAI

# Standard models
llm = ChatOpenAI(model="gpt-4.1-mini")      # Fast and cheap
llm = ChatOpenAI(model="gpt-4.1-nano")     # Smallest/cheapest
llm = ChatOpenAI(model="gpt-4o")           # Most capable

# With configuration
llm = ChatOpenAI(
    model="gpt-4.1-mini",
    temperature=0.7,      # Creativity (0=deterministic, 1=creative)
    max_tokens=500,       # Max response length
)
```

**Local Models (Ollama)**
```python
from langchain_ollama import ChatOllama

llm = ChatOllama(
    model="llama3.2:3b",
    temperature=0.7,
)
```

### Step 2.2: Create Prompt Templates

Prompts are instructions that tell the LLM how to use the retrieved context.

**Simple Prompt Template**
```python
from langchain_core.prompts import ChatPromptTemplate

RAG_TEMPLATE = """
You are a helpful assistant. Use the context below to answer the question.

If you don't know the answer based on the context, say "I don't know."

Context:
{context}

Question:
{question}

Answer:
"""

prompt = ChatPromptTemplate.from_template(RAG_TEMPLATE)
```

**Multi-Message Prompt (System + User)**
```python
from langchain_core.prompts import ChatPromptTemplate

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful AI assistant. Answer questions based only on the provided context."),
    ("user", """
    Context: {context}
    
    Question: {query}
    
    Provide a clear and concise answer based on the context above.
    """)
])
```

**Advanced Prompt with Instructions**
```python
DETAILED_RAG_TEMPLATE = """
You are a knowledgeable assistant that answers questions based strictly on provided context.

Instructions:
- Only answer questions using information from the provided context
- If the context doesn't contain relevant information, respond with "I don't know"
- Be accurate and cite specific parts of the context when possible
- Keep responses concise and direct
- Do not use external knowledge

Context:
{context}

Question:
{question}

Answer:
"""

prompt = ChatPromptTemplate.from_template(DETAILED_RAG_TEMPLATE)
```

**Custom Role-Based Prompts (From Scratch)**
```python
from aimakerspace.openai_utils.prompts import SystemRolePrompt, UserRolePrompt

# System message
system_prompt = SystemRolePrompt(
    "You are a helpful AI assistant. Answer based only on the provided context.",
    strict=True
)

# User message template
user_prompt = UserRolePrompt(
    """Context: {context}
    
    Question: {user_query}
    
    Provide your answer based solely on the context above.""",
    strict=True
)

# Create messages
messages = [
    system_prompt.create_message(),
    user_prompt.create_message(context=context, user_query=query)
]
```

### Prompt Best Practices

1. **Be Explicit**: Tell the LLM to ONLY use the provided context
2. **Handle Unknowns**: Instruct what to say when answer isn't in context
3. **Set Tone**: Specify if you want concise, detailed, formal, etc.
4. **Format Output**: Request specific formats (bullet points, paragraphs, etc.)
5. **Prevent Hallucination**: Emphasize not using external knowledge

---

## 3. Building RAG Chains

RAG chains connect: Retrieval → Prompt → LLM → Output

### Method 1: LCEL (LangChain Expression Language)

**Basic LCEL Chain**
```python
from langchain_core.output_parsers import StrOutputParser
from operator import itemgetter

# Create chain using | operator
rag_chain = (
    {"context": retriever, "question": itemgetter("question")}
    | prompt
    | llm
    | StrOutputParser()
)

# Use it
response = rag_chain.invoke({"question": "What is machine learning?"})
print(response)
```

**Detailed LCEL Chain (with context passing)**
```python
from langchain_core.runnables import RunnablePassthrough

rag_chain = (
    # Step 1: Retrieve context and pass question
    {"context": itemgetter("question") | retriever, "question": itemgetter("question")}
    
    # Step 2: Keep context available
    | RunnablePassthrough.assign(context=itemgetter("context"))
    
    # Step 3: Format with prompt, generate with LLM, and keep context
    | {"response": prompt | llm, "context": itemgetter("context")}
)

# Use it (returns both response and context)
result = rag_chain.invoke({"question": "What is RAG?"})
print(result["response"].content)
print(f"\nUsed {len(result['context'])} documents")
```

**Understanding LCEL Components:**

1. **Pipe Operator `|`**: Chains components together
   ```python
   output = component1 | component2 | component3
   ```

2. **`itemgetter("key")`**: Extracts values from dictionaries
   ```python
   from operator import itemgetter
   extract_question = itemgetter("question")
   ```

3. **`RunnablePassthrough`**: Passes data through unchanged
   ```python
   from langchain_core.runnables import RunnablePassthrough
   ```

4. **`StrOutputParser()`**: Converts LLM output to string
   ```python
   from langchain_core.output_parsers import StrOutputParser
   ```

### Method 2: LangGraph (For Complex Workflows)

**Basic LangGraph RAG**
```python
from langgraph.graph import START, StateGraph
from typing_extensions import List, TypedDict
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser

# Define state
class State(TypedDict):
    question: str
    context: List[Document]
    response: str

# Define nodes
def retrieve(state: State):
    """Retrieval node"""
    retrieved_docs = retriever.invoke(state["question"])
    return {"context": retrieved_docs}

def generate(state: State):
    """Generation node"""
    generator_chain = prompt | llm | StrOutputParser()
    response = generator_chain.invoke({
        "query": state["question"],
        "context": state["context"]
    })
    return {"response": response}

# Build graph
graph_builder = StateGraph(State)
graph_builder.add_sequence([retrieve, generate])
graph_builder.add_edge(START, "retrieve")

# Compile
graph = graph_builder.compile()

# Use it
response = graph.invoke({"question": "What is RAG?"})
print(response["response"])
```

**LangGraph with Conditional Logic**
```python
from langgraph.graph import END

def check_context_quality(state: State):
    """Route based on retrieved context quality"""
    if len(state["context"]) == 0:
        return "no_context"
    return "has_context"

def no_context_response(state: State):
    """Handle case with no retrieved context"""
    return {"response": "I don't have enough information to answer that question."}

# Build graph with conditional routing
graph_builder = StateGraph(State)
graph_builder.add_node("retrieve", retrieve)
graph_builder.add_node("generate", generate)
graph_builder.add_node("no_context", no_context_response)

# Add conditional edges
graph_builder.add_edge(START, "retrieve")
graph_builder.add_conditional_edges(
    "retrieve",
    check_context_quality,
    {
        "has_context": "generate",
        "no_context": "no_context"
    }
)
graph_builder.add_edge("generate", END)
graph_builder.add_edge("no_context", END)

graph = graph_builder.compile()
```

### Method 3: Custom Pipeline (From Scratch)

```python
from aimakerspace.openai_utils.chatmodel import ChatOpenAI
from aimakerspace.vectordatabase import VectorDatabase

class RetrievalAugmentedQAPipeline:
    def __init__(self, vector_db_retriever: VectorDatabase, llm: ChatOpenAI):
        self.vector_db_retriever = vector_db_retriever
        self.llm = llm
    
    def run_pipeline(self, user_query: str, k: int = 3):
        # Step 1: Retrieve relevant documents
        context_list = self.vector_db_retriever.search_by_text(
            user_query, 
            k=k,
            return_as_text=True
        )
        context = "\n\n".join(context_list)
        
        # Step 2: Format prompt
        system_message = {
            "role": "system",
            "content": "You are a helpful assistant. Answer based on the context provided."
        }
        user_message = {
            "role": "user",
            "content": f"Context:\n{context}\n\nQuestion: {user_query}"
        }
        
        # Step 3: Generate response
        response = self.llm.run([system_message, user_message])
        
        return {
            "response": response,
            "context": context_list
        }

# Use it
pipeline = RetrievalAugmentedQAPipeline(
    vector_db_retriever=vector_db,
    llm=chat_llm
)

result = pipeline.run_pipeline("What is RAG?", k=3)
print(result["response"])
```

---

## 4. Complete Examples

### Example 1: Simple RAG (Minimal Code)

```python
from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Qdrant
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# 1. Load documents
loader = TextLoader("data.txt")
documents = loader.load()

# 2. Chunk
splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
chunks = splitter.split_documents(documents)

# 3. Create vector store
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
vectorstore = Qdrant.from_documents(chunks, embeddings, location=":memory:")

# 4. Create retriever
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

# 5. Set up LLM and prompt
llm = ChatOpenAI(model="gpt-4.1-mini")
prompt = ChatPromptTemplate.from_template(
    "Context: {context}\n\nQuestion: {question}\n\nAnswer based on context:"
)

# 6. Build chain
rag_chain = (
    {"context": retriever, "question": lambda x: x}
    | prompt
    | llm
    | StrOutputParser()
)

# 7. Use it
answer = rag_chain.invoke("What is this document about?")
print(answer)
```

### Example 2: Production RAG with LCEL

```python
import tiktoken
from langchain_community.document_loaders import PyMuPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_qdrant import QdrantVectorStore
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams
from operator import itemgetter

# Load documents
loader = PyMuPDFLoader("document.pdf")
documents = loader.load()

# Chunk with token counting
def tiktoken_len(text):
    tokens = tiktoken.get_encoding("cl100k_base").encode(text)
    return len(tokens)

splitter = RecursiveCharacterTextSplitter(
    chunk_size=750,
    chunk_overlap=50,
    length_function=tiktoken_len
)
chunks = splitter.split_documents(documents)

# Set up vector store
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
client = QdrantClient(":memory:")

client.create_collection(
    collection_name="knowledge_base",
    vectors_config=VectorParams(size=1536, distance=Distance.COSINE)
)

vector_store = QdrantVectorStore(
    client=client,
    collection_name="knowledge_base",
    embedding=embeddings
)
vector_store.add_documents(chunks)

# Create retriever
retriever = vector_store.as_retriever(search_kwargs={"k": 5})

# Set up LLM and prompt
llm = ChatOpenAI(model="gpt-4.1-mini", temperature=0)

prompt = ChatPromptTemplate.from_template("""
You are a helpful assistant. Use the context below to answer the question.
If you don't know the answer, say "I don't know."

Context:
{context}

Question:
{question}

Answer:
""")

# Build production chain
rag_chain = (
    {"context": itemgetter("question") | retriever, "question": itemgetter("question")}
    | RunnablePassthrough.assign(context=itemgetter("context"))
    | {"response": prompt | llm | StrOutputParser(), "context": itemgetter("context")}
)

# Use it
result = rag_chain.invoke({"question": "What are the main findings?"})
print(f"Answer: {result['response']}")
print(f"\nSources used: {len(result['context'])} documents")
```

### Example 3: Advanced RAG with LangGraph

```python
from langgraph.graph import START, END, StateGraph
from typing import List, TypedDict
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from langchain_community.vectorstores import Qdrant
from langchain_core.prompts import ChatPromptTemplate

# Define state
class RAGState(TypedDict):
    question: str
    context: List[Document]
    response: str
    has_context: bool

# Nodes
def retrieve_node(state: RAGState):
    """Retrieve relevant documents"""
    docs = retriever.invoke(state["question"])
    return {
        "context": docs,
        "has_context": len(docs) > 0
    }

def check_context(state: RAGState):
    """Check if we have valid context"""
    return "generate" if state["has_context"] else "no_context"

def generate_node(state: RAGState):
    """Generate response from context"""
    chain = prompt | llm | StrOutputParser()
    response = chain.invoke({
        "context": state["context"],
        "question": state["question"]
    })
    return {"response": response}

def no_context_node(state: RAGState):
    """Handle no context scenario"""
    return {"response": "I don't have enough information to answer that question."}

# Build graph
graph = StateGraph(RAGState)

# Add nodes
graph.add_node("retrieve", retrieve_node)
graph.add_node("generate", generate_node)
graph.add_node("no_context", no_context_node)

# Add edges
graph.add_edge(START, "retrieve")
graph.add_conditional_edges(
    "retrieve",
    check_context,
    {"generate": "generate", "no_context": "no_context"}
)
graph.add_edge("generate", END)
graph.add_edge("no_context", END)

# Compile
rag_app = graph.compile()

# Use it
result = rag_app.invoke({"question": "What is RAG?"})
print(result["response"])
```

---

## Quick Reference

### Typical RAG Flow
1. **Load** documents → 2. **Chunk** documents → 3. **Embed** chunks → 4. **Store** in vector DB → 5. **Retrieve** relevant chunks → 6. **Format** with prompt → 7. **Generate** response

### Common Patterns

**Simple RAG**:
```python
retriever → prompt → llm → output
```

**RAG with Context Tracking**:
```python
{context: retriever, question: passthrough} → prompt → llm → {response, context}
```

**Multi-Stage RAG**:
```python
retriever → reranker → prompt → llm → output
```

### Key Parameters to Tune

1. **Chunk Size**: 500-1500 (balance context vs. precision)
2. **Chunk Overlap**: 50-200 (maintain context across boundaries)
3. **k (retrieval)**: 3-10 (number of chunks to retrieve)
4. **Temperature**: 0-0.3 for factual, 0.7-1.0 for creative
5. **Embedding Model**: `text-embedding-3-small` (cheap) vs `-large` (quality)

---

## Additional Resources

- **LangChain Docs**: https://python.langchain.com/
- **LangGraph Docs**: https://langchain-ai.github.io/langgraph/
- **Qdrant Docs**: https://qdrant.tech/documentation/
- **OpenAI Embeddings**: https://platform.openai.com/docs/guides/embeddings

---

*This guide was compiled from AI Engineering Bootcamp (AIE8) course materials covering sessions 2-9.*

