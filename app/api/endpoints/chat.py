"""
Chatbot API endpoints using FastAPI APIRouter.
Single unified endpoint for Flutter/mobile apps - handles everything!
"""
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from app.schemas.chat_schema import (
    ChatRequest,
    MessageHistory,
    UnifiedChatResponse
)
from app.services.gemini_service import GeminiService
import json

# Mobile-friendly router with /api prefix
api_router = APIRouter(prefix="/api", tags=["api"])

# Lazy initialization - service will be created on first use
_gemini_service_instance = None

def get_gemini_service() -> GeminiService:
    """Get or create Gemini service instance."""
    global _gemini_service_instance
    if _gemini_service_instance is None:
        _gemini_service_instance = GeminiService()
    return _gemini_service_instance


@api_router.post("/chat")
async def unified_chat_endpoint(
    request: ChatRequest,
    stream: bool = Query(False, description="Enable streaming response (default: false)"),
    include_history: bool = Query(True, description="Include full conversation history in response (default: true)")
):
    """
    🚀 UNIFIED CHAT ENDPOINT - Everything in one place!
    
    Single endpoint for Flutter/mobile apps that handles:
    - ✅ Normal chat (complete response + history)
    - ✅ Streaming chat (real-time chunks + history at end)
    - ✅ Conversation history (always included in both modes)
    - ✅ Auto session creation
    - ✅ Multi-turn conversations
    
    Usage:
    - Normal: POST /api/chat
    - Streaming: POST /api/chat?stream=true
    
    Features:
    - First message: Creates new session automatically
    - Subsequent messages: Pass chat_id to continue conversation
    - History ALWAYS included in both normal and streaming modes!
    """
    
    greeting_text = (
        "Hello! Welcome back to HealthStake. I'm your personal diabetes assistant. "
        "How can I help you today?"
    )
    
    # Treat empty/short greetings as a request for the canned intro to avoid model calls
    normalized = request.message.strip().lower()
    wants_greeting = (not request.chat_id) and normalized in {"", "hi", "hello", "hey"}
    
    if stream:
        # STREAMING MODE - History always included at the end
        async def generate_stream():
            chat_id = None
            full_response = ""
            
            try:
                gemini_service = get_gemini_service()
                
                if wants_greeting:
                    # Create a fresh chat session for the new user and emit greeting
                    chat_id = gemini_service.create_chat_session()
                    chunk_data = {"type": "chunk", "text": greeting_text, "chat_id": chat_id}
                    yield f"data: {json.dumps(chunk_data)}\n\n"
                    final_data = {
                        "type": "complete",
                        "response": greeting_text,
                        "chat_id": chat_id,
                        "history": []
                    }
                    yield f"data: {json.dumps(final_data)}\n\n"
                    return
                
                # Stream the response chunks
                async for chunk_text, current_chat_id in gemini_service.send_message_stream(
                    message=request.message,
                    chat_id=request.chat_id
                ):
                    chat_id = current_chat_id
                    full_response += chunk_text
                    
                    # Send each chunk as it arrives
                    chunk_data = {
                        "type": "chunk",
                        "text": chunk_text,
                        "chat_id": chat_id
                    }
                    yield f"data: {json.dumps(chunk_data)}\n\n"
                
                # After streaming completes, ALWAYS send history
                if chat_id:
                    try:
                        history_data = gemini_service.get_chat_history(chat_id)
                        history = [
                            {"role": msg["role"], "text": msg["text"]} 
                            for msg in history_data
                        ]
                    except Exception:
                        # If history retrieval fails, return empty history
                        history = []
                    
                    # Send final message with complete response AND history
                    final_data = {
                        "type": "complete",
                        "response": full_response,
                        "chat_id": chat_id,
                        "history": history  # History always included
                    }
                    yield f"data: {json.dumps(final_data)}\n\n"
                    
            except ValueError as e:
                error_data = {
                    "type": "error",
                    "error": str(e)
                }
                yield f"data: {json.dumps(error_data)}\n\n"
            except Exception as e:
                error_data = {
                    "type": "error",
                    "error": "Failed to process chat message",
                    "message": str(e)
                }
                yield f"data: {json.dumps(error_data)}\n\n"
        
        return StreamingResponse(generate_stream(), media_type="text/event-stream")
    
    else:
        # NORMAL MODE (Complete response)
        try:
            gemini_service = get_gemini_service()
            
            # Shortcut greeting without hitting the model
            if wants_greeting:
                chat_id = gemini_service.create_chat_session()
                return UnifiedChatResponse(response=greeting_text, chat_id=chat_id, history=[])
            
            # Send message and get response
            try:
                response_text, chat_id = await gemini_service.send_message(
                    message=request.message,
                    chat_id=request.chat_id
                )
            except Exception as e:
                # Log send_message error
                import traceback
                print(f"Error in send_message: {str(e)}")
                print(traceback.format_exc())
                raise
            
            # Build response
            response_data = {
                "response": response_text,
                "chat_id": chat_id,
                "history": []  # Default to empty list
            }
            
            # Include history if requested (default: true)
            if include_history:
                try:
                    history_data = gemini_service.get_chat_history(chat_id)
                    if history_data and len(history_data) > 0:
                        try:
                            history = [
                                MessageHistory(role=str(msg.get("role", "unknown")), text=str(msg.get("text", "")))
                                for msg in history_data
                            ]
                            response_data["history"] = history
                        except Exception as e:
                            # If MessageHistory creation fails, use empty list
                            print(f"MessageHistory creation error: {str(e)}")
                            response_data["history"] = []
                    else:
                        response_data["history"] = []
                except Exception as e:
                    # If history retrieval fails, return empty history
                    # Log error but don't fail the request
                    print(f"History retrieval error: {str(e)}")
                    import traceback
                    print(traceback.format_exc())
                    response_data["history"] = []
            
            # Ensure history is always a list, never None
            if response_data.get("history") is None:
                response_data["history"] = []
            
            return UnifiedChatResponse(**response_data)
            
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            # Original technical error string
            raw_error_message = str(e)
            
            # Default values
            status_code = 500
            user_message = "We’re having trouble processing your request right now. Please try again in a moment."
            error_code = "CHAT_PROCESSING_ERROR"

            lower_msg = raw_error_message.lower()

            # Map common backend / Gemini errors to cleaner, professional messages
            if "overloaded" in lower_msg or "503" in lower_msg:
                status_code = 503
                error_code = "SERVICE_UNAVAILABLE"
                user_message = "The AI service is temporarily unavailable. Please try again shortly."
            elif "rate limit" in lower_msg or "429" in lower_msg:
                status_code = 429
                error_code = "RATE_LIMITED"
                user_message = "You’ve reached the current request limit. Please wait a bit and try again."
            elif "401" in lower_msg or "unauthenticated" in lower_msg or "invalid api key" in lower_msg:
                status_code = 401
                error_code = "AUTHENTICATION_ERROR"
                user_message = "The AI service credentials are not valid. Please contact the app administrator."
            elif "permission_denied" in lower_msg or "your api key was reported as leaked" in lower_msg:
                status_code = 403
                error_code = "PERMISSION_DENIED"
                user_message = "The AI service rejected the request due to a configuration issue. Please contact the app administrator."
            
            # Log full details for developers / server logs
            import traceback
            error_trace = traceback.format_exc()
            print(f"Error in chat endpoint: {error_trace}")

            # Return a clean, professional error payload for clients (Flutter, web, etc.)
            raise HTTPException(
                status_code=status_code,
                detail={
                    "error": user_message,
                    "code": error_code,
                    # Keep the raw technical message available under a separate field
                    # so clients can choose whether to show or hide it.
                    "technical_message": raw_error_message
                }
            )


