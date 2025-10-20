"""
Stack Sage FastAPI Server

A simple, elegant API for the Magic: The Gathering rules assistant.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.core.rag_pipeline import graph

# Create FastAPI app
app = FastAPI(
    title="Stack Sage API",
    description="An intelligent Magic: The Gathering rules assistant",
    version="1.0.0"
)

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Vite default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response models
class QuestionRequest(BaseModel):
    question: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "question": "What happens when Rest in Peace is on the battlefield?"
            }
        }


class AnswerResponse(BaseModel):
    question: str
    answer: str
    success: bool


class HealthResponse(BaseModel):
    status: str
    message: str


# Routes
@app.get("/", response_model=HealthResponse)
async def root():
    """Health check endpoint."""
    return {
        "status": "online",
        "message": "Stack Sage API is running! Visit /docs for API documentation."
    }


@app.get("/health", response_model=HealthResponse)
async def health():
    """Detailed health check."""
    return {
        "status": "healthy",
        "message": "All systems operational"
    }


@app.post("/ask", response_model=AnswerResponse)
async def ask_question(request: QuestionRequest):
    """
    Ask Stack Sage a question about Magic: The Gathering rules.
    
    The AI assistant will use its tools to search rules, look up cards,
    check format legality, and more to provide accurate answers.
    """
    if not request.question or not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    
    try:
        # Process the question through the RAG pipeline
        result = graph.invoke({"question": request.question.strip()})
        answer = result.get("response", "I couldn't generate an answer.")
        
        return {
            "question": request.question.strip(),
            "answer": answer,
            "success": True
        }
    
    except Exception as e:
        # Log the error for debugging
        print(f"Error processing question: {str(e)}")
        
        # Return a user-friendly error
        return {
            "question": request.question.strip(),
            "answer": f"I encountered an error processing your question: {str(e)}\n\nPlease try rephrasing your question or ask something else.",
            "success": False
        }


# Example questions endpoint for the frontend
@app.get("/examples")
async def get_examples():
    """Get example questions to help users get started."""
    return {
        "examples": [
            "What is the effect of Rest in Peace?",
            "How does Dockside Extortionist work with Spark Double?",
            "Does Rest in Peace stop Unearth?",
            "What happens when a player loses the game?",
            "How does the stack resolve?",
            "What is priority and how does it work?",
            "Is Black Lotus legal in Commander?",
            "Find red creatures with 3 power in Standard"
        ]
    }


if __name__ == "__main__":
    import uvicorn
    
    print("=" * 60)
    print("📘 Starting Stack Sage API Server")
    print("=" * 60)
    print("\n🚀 Server will run on http://localhost:8000")
    print("📖 API docs available at http://localhost:8000/docs")
    print("\nPress CTRL+C to stop the server\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

