"""
Stack Sage FastAPI Server

A simple, elegant API for the Magic: The Gathering rules assistant.
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, field_validator
from typing import Optional, List
import os

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from backend.core.multi_agent_graph import invoke_graph, invoke_graph_streaming
from backend.core.deck_validator import DeckValidator
from backend.core.deck_models import Deck, DeckCard

# Create FastAPI app
app = FastAPI(
    title="Stack Sage API",
    description="An intelligent Magic: The Gathering rules assistant",
    version="1.0.0"
)

# Setup rate limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Enable CORS for local development
cors_origins = os.getenv("CORS_ALLOW_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response models
class QuestionRequest(BaseModel):
    question: str
    
    @field_validator("question")
    @classmethod
    def validate_question(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Question cannot be empty")
        if len(v) > 2000:
            raise ValueError("Question too long (max 2000 chars)")
        return v
    
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
    tools_used: Optional[List[str]] = None
    citations: Optional[List[str]] = None


class HealthResponse(BaseModel):
    status: str
    message: str


class DeckValidateRequest(BaseModel):
    decklist: str
    format: str
    commander: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "decklist": "4 Lightning Bolt\n4 Monastery Swiftspear\n52 Mountain",
                "format": "modern",
                "commander": None
            }
        }


class DeckValidateResponse(BaseModel):
    is_legal: bool
    format: str
    total_cards: int
    errors: List[str]
    warnings: List[str]


class CardSearchRequest(BaseModel):
    # Primary search field
    card_name: Optional[str] = None
    
    # Advanced filters (optional)
    colors: Optional[str] = None
    mana_value: Optional[str] = None
    mana_cost: Optional[str] = None
    power: Optional[str] = None
    toughness: Optional[str] = None
    format_legal: Optional[str] = None
    card_type: Optional[str] = None
    keywords: Optional[str] = None
    text: Optional[str] = None
    rarity: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "card_name": "Lightning Bolt",
                "colors": "r",
                "mana_value": "3",
                "power": "3",
                "card_type": "creature",
                "format_legal": "standard"
            }
        }


class CardSearchResponse(BaseModel):
    total_cards: int
    query: str
    cards: List[dict]
    success: bool


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
@limiter.limit("10/minute")
async def ask_question(question_request: QuestionRequest, request: Request):
    """
    Ask Stack Sage a question about Magic: The Gathering rules.
    
    Uses an intelligent multi-agent system where:
    - A Planner agent analyzes your question using AI
    - Specialist agents (Cards, Rules, Interaction, Judge, Meta) are routed to dynamically
    - Each agent focuses on their expertise area
    - The system provides accurate, verified answers
    """
    if not question_request.question or not question_request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    
    try:
        # Process the question through the Multi-Agent Graph
        result = invoke_graph(question_request.question.strip())
        answer = result.get("response", "I couldn't generate an answer.")
        
        # Convert citation objects to strings
        citations = result.get("citations", [])
        citation_strings = []
        for citation in citations:
            if isinstance(citation, dict):
                # Format: "Card: Lightning Bolt" or "Rule: 702.66"
                citation_strings.append(f"{citation.get('type', 'source').title()}: {citation.get('id', 'Unknown')}")
            else:
                citation_strings.append(str(citation))
        
        return {
            "question": question_request.question.strip(),
            "answer": answer,
            "success": True,
            "tools_used": result.get("tools_used", []),
            "citations": citation_strings
        }
    
    except Exception as e:
        # Log the error for debugging
        print(f"Error processing question: {str(e)}")
        
        # Return a user-friendly error
        return {
            "question": question_request.question.strip(),
            "answer": "I encountered an error processing your question. Please try again shortly.",
            "success": False,
            "tools_used": [],
            "citations": []
        }


@app.post("/ask/stream")
@limiter.limit("10/minute")
async def ask_stream(question_request: QuestionRequest, request: Request):
    """
    Ask Stack Sage a question and stream the answer in real-time using Server-Sent Events.
    
    Uses the same multi-agent system as /ask but streams the final answer as it's generated.
    """
    if not question_request.question or not question_request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    
    async def generate():
        try:
            # Stream answer chunks
            for chunk in invoke_graph_streaming(question_request.question.strip()):
                yield f"data: {chunk}\n\n"
        except Exception as e:
            print(f"Error streaming answer: {str(e)}")
            yield f"data: Error processing question\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")


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


@app.post("/validate-deck", response_model=DeckValidateResponse)
async def validate_deck(request: DeckValidateRequest):
    """
    Validate an MTG deck for format legality.
    
    Accepts a decklist in text format (e.g., "4 Lightning Bolt") and validates
    it according to the specified format rules.
    """
    if not request.decklist or not request.decklist.strip():
        raise HTTPException(status_code=400, detail="Decklist cannot be empty")
    
    if not request.format or not request.format.strip():
        raise HTTPException(status_code=400, detail="Format must be specified")
    
    try:
        # Parse the decklist
        mainboard = []
        lines = request.decklist.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#') or line.startswith('//'):
                continue
            
            # Parse format: "4 Card Name" or "Card Name"
            parts = line.split(' ', 1)
            if len(parts) == 2 and parts[0].isdigit():
                quantity = int(parts[0])
                card_name = parts[1].strip()
            else:
                quantity = 1
                card_name = line
            
            if card_name:
                mainboard.append(DeckCard(name=card_name, quantity=quantity))
        
        if not mainboard:
            raise HTTPException(status_code=400, detail="No valid cards found in decklist")
        
        # Create deck object
        deck = Deck(
            name="User Deck",
            format=request.format.strip(),
            mainboard=mainboard,
            sideboard=[],
            commander=request.commander
        )
        
        # Validate the deck
        validator = DeckValidator()
        result = validator.validate(deck)
        
        return {
            "is_legal": result.is_legal,
            "format": result.format,
            "total_cards": result.total_cards,
            "errors": result.errors,
            "warnings": result.warnings
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error validating deck: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error validating deck: {str(e)}")


@app.post("/search-cards", response_model=CardSearchResponse)
async def search_cards(request: CardSearchRequest):
    """
    Search for MTG cards using advanced criteria.
    
    Search by colors, mana cost, power/toughness, card type, format legality,
    keywords, oracle text, and rarity.
    """
    try:
        # Import scryfall here to avoid circular imports
        from backend.core.scryfall import ScryfallAPI
        
        scryfall = ScryfallAPI()
        
        # Build Scryfall search query
        query_parts = []
        
        # Debug logging
        print(f"[DEBUG] Received request - card_name: '{request.card_name}', colors: '{request.colors}'")
        
        # Primary search: Card name (fuzzy search)
        if request.card_name and request.card_name.strip():
            # Use Scryfall's fuzzy name search
            card_name_query = f'name:"{request.card_name.strip()}"'
            query_parts.append(card_name_query)
            print(f"[DEBUG] Added card name query: {card_name_query}")
        
        # Advanced filters
        if request.colors:
            query_parts.append(f"c:{request.colors}")
        if request.mana_value:
            mv = request.mana_value
            query_parts.append(f"mv{mv}" if any(op in mv for op in ['<', '>', '=']) else f"mv={mv}")
        if request.mana_cost:
            query_parts.append(f"m:{request.mana_cost}")
        if request.power:
            pow_val = request.power
            query_parts.append(f"pow{pow_val}" if any(op in pow_val for op in ['<', '>', '=']) else f"pow={pow_val}")
        if request.toughness:
            tou_val = request.toughness
            query_parts.append(f"tou{tou_val}" if any(op in tou_val for op in ['<', '>', '=']) else f"tou={tou_val}")
        if request.format_legal:
            query_parts.append(f"f:{request.format_legal}")
        if request.card_type:
            query_parts.append(f"t:{request.card_type}")
        if request.keywords:
            query_parts.append(f"o:{request.keywords}")
        if request.text:
            query_parts.append(f'o:"{request.text}"')
        if request.rarity:
            query_parts.append(f"r:{request.rarity}")
        
        if not query_parts:
            print(f"[DEBUG] No query parts generated! Full request: {request.dict()}")
            raise HTTPException(
                status_code=400, 
                detail=f"Please provide at least one search criterion. Received: card_name='{request.card_name}'"
            )
        
        # Join query parts
        search_query = " ".join(query_parts)
        
        # Determine ordering
        if request.format_legal and request.format_legal.lower() in ['standard', 'pioneer', 'modern']:
            order = 'released'
        else:
            order = 'edhrec'
        
        # Make API call to Scryfall
        url = f"{scryfall.BASE_URL}/cards/search"
        params = {
            'q': search_query,
            'order': order,
            'unique': 'cards',
            'dir': 'desc'
        }
        
        response = scryfall.session.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        total_cards = data.get('total_cards', 0)
        
        if total_cards == 0:
            return {
                "total_cards": 0,
                "query": search_query,
                "cards": [],
                "success": True
            }
        
        # Get top results (limit to 20)
        cards_data = data.get('data', [])[:20]
        
        # Validate format legality if specified
        if request.format_legal:
            validated_cards = []
            for card_data in cards_data:
                legalities = card_data.get('legalities', {})
                card_legal = legalities.get(request.format_legal.lower(), 'not_legal')
                
                if card_legal == 'legal':
                    validated_cards.append(card_data)
            
            cards_data = validated_cards
        
        # Format cards for response
        formatted_cards = []
        for card_data in cards_data:
            card_info = {
                "name": card_data.get('name', 'Unknown'),
                "mana_cost": card_data.get('mana_cost', ''),
                "type_line": card_data.get('type_line', ''),
                "oracle_text": card_data.get('oracle_text', ''),
                "power": card_data.get('power'),
                "toughness": card_data.get('toughness'),
                "image_url": card_data.get('image_uris', {}).get('normal', ''),
                "scryfall_url": card_data.get('scryfall_uri', ''),
                "rarity": card_data.get('rarity', ''),
                "set_name": card_data.get('set_name', ''),
                "collector_number": card_data.get('collector_number', '')
            }
            formatted_cards.append(card_info)
        
        return {
            "total_cards": total_cards,
            "query": search_query,
            "cards": formatted_cards,
            "success": True
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error searching cards: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error searching cards: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    
    print("=" * 60)
    print("📘 Starting Stack Sage API Server")
    print("=" * 60)
    print("\n🧠 Multi-Agent System Active:")
    print("   • AI-Powered Planner for intelligent routing")
    print("   • Specialist agents: Card, Rules, Interaction, Judge, Meta")
    print("   • Dynamic agent selection based on question analysis")
    print("\n🚀 Server will run on http://localhost:8000")
    print("📖 API docs available at http://localhost:8000/docs")
    print("\nPress CTRL+C to stop the server\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

