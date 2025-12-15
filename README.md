# Chatbot Project

A FastAPI-based chatbot application using Google's Gemini AI.

## Project Structure

```
chatbot_project/
├── app/
│   ├── api/
│   │   ├── endpoints/
│   │   │   └── chat.py         # Chatbot endpoints (APIRouters)
│   │   └── __init__.py
│   │
│   ├── core/
│   │   ├── config.py           # Settings and Configuration variables (API keys, model name)
│   │   └── __init__.py
│   │
│   ├── services/
│   │   ├── gemini_service.py   # Business logic. Gemini SDK integration
│   │   └── __init__.py
│   │
│   ├── schemas/
│   │   ├── chat_schema.py      # Pydantic Models for request (input) and response (output) validation
│   │   └── __init__.py
│   │
│   └── main.py                 # FastAPI application entry point (run with Uvicorn)
│
├── tests/                      # Testing files
│   ├── test_api.py
│   └── test_service.py
│
├── .env                        # Environment variables (API keys, etc.)
├── requirements.txt            # Project dependencies
└── README.md                   # Project documentation
```

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Edit the `.env` file and add your Gemini API key:

```
GEMINI_API_KEY=your_actual_api_key_here
```

You can get your API key from [Google AI Studio](https://makersuite.google.com/app/apikey).

### 3. Run the Application

Start the FastAPI server using Uvicorn:

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

### 4. API Documentation

Once the server is running, you can access:
- Interactive API docs: `http://localhost:8000/docs`
- Alternative docs: `http://localhost:8000/redoc`

## API Endpoints

### POST /chat/session/create
Create a new chat session for multi-turn conversations.

**Request Body (optional):**
```json
{
  "model": "gemini-2.5-flash"
}
```

**Response:**
```json
{
  "chat_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### POST /chat/
Send a message to the chatbot. Supports multi-turn conversations with automatic history management.

**Request Body:**
```json
{
  "message": "Hello, how are you?",
  "chat_id": "550e8400-e29b-41d4-a716-446655440000"  // Optional: for continuing existing conversation
}
```

**Response:**
```json
{
  "response": "I'm doing well, thank you for asking!",
  "chat_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Multi-Turn Conversation Example:**
```bash
# First message (creates new session automatically)
POST /chat/
{
  "message": "I have 2 dogs in my house."
}
# Response includes chat_id

# Second message (continues conversation with context)
POST /chat/
{
  "message": "How many paws are in my house?",
  "chat_id": "550e8400-e29b-41d4-a716-446655440000"
}
# Model remembers you have 2 dogs and calculates 8 paws!
```

### POST /chat/stream
Streaming chat endpoint that returns responses in real-time chunks.

**Request Body:**
```json
{
  "message": "Tell me a story",
  "chat_id": "550e8400-e29b-41d4-a716-446655440000"  // Optional
}
```

**Response:** Server-Sent Events (SSE) stream with chunks

### GET /chat/{chat_id}/history
Get the full conversation history for a chat session.

**Response:**
```json
{
  "chat_id": "550e8400-e29b-41d4-a716-446655440000",
  "history": [
    {
      "role": "user",
      "text": "I have 2 dogs in my house."
    },
    {
      "role": "model",
      "text": "That's wonderful! Dogs are great companions."
    },
    {
      "role": "user",
      "text": "How many paws are in my house?"
    },
    {
      "role": "model",
      "text": "Since you have 2 dogs, and each dog has 4 paws, you have 2 × 4 = 8 paws in your house!"
    }
  ]
}
```

### DELETE /chat/{chat_id}
Delete a chat session and clear its history.

**Response:**
```json
{
  "message": "Chat session 550e8400-e29b-41d4-a716-446655440000 deleted successfully"
}
```

### GET /
Root endpoint - returns welcome message and version.

### GET /health
Health check endpoint.

## Running Tests

```bash
pytest tests/
```

## Dependencies

- **FastAPI**: Modern web framework for building APIs
- **Uvicorn**: ASGI server for running FastAPI
- **google-genai**: Latest Google Gemini AI SDK (v0.2.2+) with chat API support
- **Pydantic**: Data validation using Python type annotations
- **pytest**: Testing framework

## Features

### Multi-Turn Conversations
The chatbot uses the latest Gemini SDK which automatically manages conversation history:
- **Automatic History Management**: The SDK maintains full conversation context behind the scenes
- **No Manual History Tracking**: You don't need to manually pass previous messages
- **Session-Based**: Each chat session maintains its own independent conversation history
- **Streaming Support**: Real-time streaming responses with history preservation

### How It Works
1. Create a chat session (or let the API create one automatically)
2. Send messages with the `chat_id` to continue conversations
3. The SDK automatically includes full conversation history with each request
4. Retrieve conversation history anytime using the `/chat/{chat_id}/history` endpoint

## Notes

- Make sure to set your `GEMINI_API_KEY` in the `.env` file before running the application
- The default model is `gemini-2.5-flash`, which can be changed in the `.env` file
- The application runs in debug mode when `DEBUG=True` in `.env`
- Chat sessions are stored in memory (consider Redis or database for production)
- The SDK automatically manages the `content[]` array - you don't need to handle it manually

## Diabetes Health Assistant System Prompt

The chatbot is configured as a **compassionate and professional diabetes health assistant** with the following characteristics:

- **Purpose**: Help diabetes patients manage their condition effectively
- **Expertise Areas**:
  - Glucose monitoring and interpretation
  - Meal planning and food choices
  - Lifestyle management
  - General diabetes education

- **Guidelines**:
  - Concise responses (3-4 sentences for most responses)
  - Never recommends medication changes (always advises consulting a doctor)
  - Provides immediate safety steps for low glucose (<70 mg/dL)
  - Provides guidance for high glucose (>180 mg/dL) and when to seek medical help
  - Encouraging and supportive tone
  - Uses patient's health context for personalized advice

The system prompt is automatically applied to all new chat sessions. You can customize it by modifying `SYSTEM_PROMPT` in `app/core/config.py` or by setting it as an environment variable.

