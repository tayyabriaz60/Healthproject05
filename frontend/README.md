# Frontend Chatbot Tester

Simple HTML/JavaScript frontend for testing the Chatbot API.

## How to Use

1. **Start the FastAPI server:**
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

2. **Open `index.html` in your browser:**
   - Double-click `index.html` file
   - Or open it in any web browser

3. **Test the API:**
   - Enter your message
   - Click "Send" button
   - See the response!

## Features

- ✅ Normal chat mode (default)
- ✅ Streaming mode (optional)
- ✅ History included/excluded
- ✅ Chat ID management
- ✅ Beautiful UI
- ✅ Real-time responses

## Configuration

- **API URL**: Change the API endpoint if needed
- **Streaming Mode**: Enable for real-time responses
- **Include History**: Toggle history in response

## Notes

- Chat ID is automatically saved in browser localStorage
- You can manually enter chat_id to continue existing conversation
- Clear chat button resets everything

