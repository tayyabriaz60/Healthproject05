let currentChatId = null;

// Load saved chat ID from localStorage
window.addEventListener('DOMContentLoaded', () => {
    const savedChatId = localStorage.getItem('chatId');
    if (savedChatId) {
        currentChatId = savedChatId;
        document.getElementById('chatId').value = savedChatId;
    }
});

function addMessage(role, text, isError = false) {
    const messagesDiv = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role} ${isError ? 'error' : ''}`;
    
    const roleLabel = role === 'user' ? 'You' : role === 'model' ? 'AI' : 'System';
    messageDiv.innerHTML = `<strong>${roleLabel}:</strong> ${text}`;
    
    messagesDiv.appendChild(messageDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

function updateChatId(chatId) {
    if (chatId) {
        currentChatId = chatId;
        document.getElementById('chatId').value = chatId;
        localStorage.setItem('chatId', chatId);
    }
}

async function sendMessage() {
    const messageInput = document.getElementById('messageInput');
    const message = messageInput.value.trim();
    
    if (!message) {
        alert('Please enter a message!');
        return;
    }
    
    const apiUrl = document.getElementById('apiUrl').value;
    const streamMode = document.getElementById('streamMode').checked;
    const includeHistory = document.getElementById('includeHistory').checked;
    const chatIdInput = document.getElementById('chatId').value.trim();
    
    // Add user message to chat
    addMessage('user', message);
    messageInput.value = '';
    
    // Disable send button
    const sendBtn = document.getElementById('sendBtn');
    sendBtn.disabled = true;
    sendBtn.textContent = 'Sending...';
    
    try {
        const requestBody = {
            message: message,
            chat_id: chatIdInput || currentChatId || null
        };
        
        if (streamMode) {
            await handleStreaming(apiUrl, requestBody, includeHistory);
        } else {
            await handleNormal(apiUrl, requestBody, includeHistory);
        }
    } catch (error) {
        let errorMsg = error.message;
        if (errorMsg.includes('Failed to fetch') || errorMsg.includes('NetworkError')) {
            errorMsg = 'Cannot connect to server. Please check:\n1. Backend server is running\n2. API URL is correct\n3. CORS is enabled';
        }
        addMessage('system', `Error: ${errorMsg}`, true);
        console.error('Error:', error);
    } finally {
        sendBtn.disabled = false;
        sendBtn.textContent = 'Send';
    }
}

async function handleNormal(apiUrl, requestBody, includeHistory) {
    try {
        const url = new URL(apiUrl);
        url.searchParams.append('include_history', includeHistory);
        
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestBody)
        });
        
        if (!response.ok) {
            let errorMessage = 'Request failed';
            try {
                const error = await response.json();
                const detail = error.detail;
                
                if (typeof detail === 'string') {
                    errorMessage = detail;
                } else if (detail && detail.message) {
                    errorMessage = detail.message;
                } else if (detail && detail.error) {
                    errorMessage = detail.error;
                } else {
                    errorMessage = error.message || 'Request failed';
                }
                
                // Add helpful tips for common errors
                if (response.status === 503 || errorMessage.includes('overloaded')) {
                    errorMessage += '\n\n💡 Tip: Try using Streaming Mode - it might have better availability!';
                }
            } catch (e) {
                if (response.status === 503) {
                    errorMessage = 'Service temporarily unavailable. Please try again in a few moments.';
                } else {
                    errorMessage = `HTTP ${response.status}: ${response.statusText}`;
                }
            }
            throw new Error(errorMessage);
        }
        
        const data = await response.json();
        
        // Update chat ID
        if (data.chat_id) {
            updateChatId(data.chat_id);
        }
        
        // Add AI response
        addMessage('model', data.response);
        
        // Show history if included
        if (data.history && data.history.length > 0) {
            console.log('Full conversation history:', data.history);
            addMessage('system', `History loaded: ${data.history.length} messages`);
        }
    } catch (error) {
        if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
            throw new Error('Cannot connect to server. Make sure backend is running on ' + apiUrl);
        }
        throw error;
    }
}

async function handleStreaming(apiUrl, requestBody, includeHistory) {
    const url = new URL(apiUrl);
    url.searchParams.append('stream', 'true');
    url.searchParams.append('include_history', includeHistory);
    
    const response = await fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody)
    });
    
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail?.error || error.detail || 'Request failed');
    }
    
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    let fullResponse = '';
    let chatId = null;
    let messageDiv = null;
    
    while (true) {
        const { done, value } = await reader.read();
        
        if (done) break;
        
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop(); // Keep incomplete line in buffer
        
        for (const line of lines) {
            if (line.startsWith('data: ')) {
                try {
                    const data = JSON.parse(line.slice(6));
                    
                    if (data.type === 'chunk') {
                        fullResponse += data.text;
                        chatId = data.chat_id;
                        
                        // Create or update message div
                        if (!messageDiv) {
                            messageDiv = document.createElement('div');
                            messageDiv.className = 'message model streaming';
                            messageDiv.innerHTML = '<strong>AI:</strong> ';
                            document.getElementById('chatMessages').appendChild(messageDiv);
                        }
                        
                        messageDiv.innerHTML = `<strong>AI:</strong> ${fullResponse}`;
                        document.getElementById('chatMessages').scrollTop = 
                            document.getElementById('chatMessages').scrollHeight;
                    } 
                    else if (data.type === 'complete') {
                        // Remove streaming class
                        if (messageDiv) {
                            messageDiv.classList.remove('streaming');
                        }
                        
                        fullResponse = data.response;
                        chatId = data.chat_id;
                        
                        if (chatId) {
                            updateChatId(chatId);
                        }
                        
                        if (data.history && data.history.length > 0) {
                            console.log('Full conversation history:', data.history);
                            addMessage('system', `History loaded: ${data.history.length} messages`);
                        }
                    }
                    else if (data.type === 'error') {
                        throw new Error(data.error || 'Streaming error');
                    }
                } catch (e) {
                    console.error('Error parsing SSE data:', e);
                }
            }
        }
    }
}

function clearChat() {
    if (confirm('Are you sure you want to clear the chat?')) {
        document.getElementById('chatMessages').innerHTML = 
            '<div class="message system"><strong>System:</strong> Chat cleared. Send a message to begin!</div>';
        currentChatId = null;
        document.getElementById('chatId').value = '';
        localStorage.removeItem('chatId');
    }
}

// Test connection function
async function testConnection() {
    const apiUrl = document.getElementById('apiUrl').value;
    const testBtn = document.getElementById('testBtn');
    
    testBtn.disabled = true;
    testBtn.textContent = 'Testing...';
    
    try {
        // Test health endpoint first
        const baseUrl = apiUrl.replace('/api/chat', '');
        const healthUrl = baseUrl + '/health';
        
        const response = await fetch(healthUrl);
        if (response.ok) {
            addMessage('system', '✅ Connection successful! Backend server is running.', false);
        } else {
            throw new Error('Server responded but health check failed');
        }
    } catch (error) {
        addMessage('system', `❌ Connection failed: ${error.message}\n\nMake sure:\n1. Backend server is running\n2. Run: uvicorn app.main:app --host 0.0.0.0 --port 8000\n3. API URL is correct`, true);
    } finally {
        testBtn.disabled = false;
        testBtn.textContent = 'Test Connection';
    }
}

// Allow Enter key to send message
document.getElementById('messageInput').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        sendMessage();
    }
});

// Glucose Image Upload Functions
function handleGlucoseImageSelect(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    // Validate file type
    if (!file.type.startsWith('image/')) {
        alert('Please select an image file!');
        return;
    }
    
    // Show preview
    const reader = new FileReader();
    reader.onload = function(e) {
        const previewDiv = document.getElementById('glucoseImagePreview');
        const previewImg = document.getElementById('glucosePreviewImg');
        previewImg.src = e.target.result;
        previewDiv.style.display = 'flex';
        
        // Auto-upload the image
        uploadGlucoseImage(file);
    };
    reader.readAsDataURL(file);
}

function clearGlucoseImagePreview() {
    document.getElementById('glucoseImagePreview').style.display = 'none';
    document.getElementById('glucoseImageInput').value = '';
    document.getElementById('glucoseResult').classList.remove('show');
}

async function uploadGlucoseImage(file) {
    const uploadBtn = document.getElementById('uploadBtn');
    const resultDiv = document.getElementById('glucoseResult');
    
    // Disable upload button
    uploadBtn.disabled = true;
    uploadBtn.textContent = '⏳ Analyzing...';
    
    // Show loading state
    resultDiv.className = 'glucose-result loading show';
    resultDiv.innerHTML = '<p>🔄 Analyzing glucose meter image...</p>';
    
    try {
        // Get base URL from chat API URL
        const chatApiUrl = document.getElementById('apiUrl').value;
        const baseUrl = chatApiUrl.replace('/api/chat', '');
        const glucoseUrl = baseUrl + '/api/ai/analyze-glucose';
        
        // Create FormData for file upload
        const formData = new FormData();
        formData.append('image', file);
        
        // Upload image
        const response = await fetch(glucoseUrl, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to analyze image');
        }
        
        const data = await response.json();
        
        // Display results
        if (data.success) {
            resultDiv.className = 'glucose-result show';
            resultDiv.innerHTML = `
                <h4>📊 Glucose Reading</h4>
                <div class="glucose-reading">
                    <div class="value">${data.reading.value}</div>
                    <div class="unit">${data.reading.unit}</div>
                </div>
                ${data.analysis ? `
                    <div class="glucose-analysis">
                        <strong>💡 Health Analysis:</strong>
                        <p>${data.analysis}</p>
                    </div>
                ` : ''}
            `;
        } else {
            throw new Error('Analysis failed');
        }
        
    } catch (error) {
        resultDiv.className = 'glucose-result error show';
        let errorMsg = error.message;
        
        if (errorMsg.includes('Failed to fetch') || errorMsg.includes('NetworkError')) {
            errorMsg = 'Cannot connect to server. Please check:\n1. Backend server is running\n2. API URL is correct';
        }
        
        resultDiv.innerHTML = `
            <h4>❌ Error</h4>
            <p>${errorMsg}</p>
        `;
        console.error('Glucose upload error:', error);
    } finally {
        uploadBtn.disabled = false;
        uploadBtn.textContent = '📷 Upload Glucose Meter Image';
    }
}

// Food Image Upload Functions
function handleFoodImageSelect(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    // Validate file type
    if (!file.type.startsWith('image/')) {
        alert('Please select an image file!');
        return;
    }
    
    // Show preview
    const reader = new FileReader();
    reader.onload = function(e) {
        const previewDiv = document.getElementById('foodImagePreview');
        const previewImg = document.getElementById('foodPreviewImg');
        previewImg.src = e.target.result;
        previewDiv.style.display = 'flex';
        
        // Auto-upload the image
        uploadFoodImage(file);
    };
    reader.readAsDataURL(file);
}

function clearFoodImagePreview() {
    document.getElementById('foodImagePreview').style.display = 'none';
    document.getElementById('foodImageInput').value = '';
    document.getElementById('foodResult').classList.remove('show');
}

async function uploadFoodImage(file) {
    const uploadBtn = document.getElementById('foodUploadBtn');
    const resultDiv = document.getElementById('foodResult');
    const healthContext = document.getElementById('healthContextInput').value.trim();
    
    // Disable upload button
    uploadBtn.disabled = true;
    uploadBtn.textContent = '⏳ Analyzing...';
    
    // Show loading state
    resultDiv.className = 'food-result loading show';
    resultDiv.innerHTML = '<p>🔄 Analyzing food image...</p>';
    
    try {
        // Get base URL from chat API URL
        const chatApiUrl = document.getElementById('apiUrl').value;
        const baseUrl = chatApiUrl.replace('/api/chat', '');
        const foodUrl = new URL(baseUrl + '/api/ai/analyze-food');
        
        // Add health context as query parameter if provided
        if (healthContext) {
            foodUrl.searchParams.append('health_context', healthContext);
        }
        
        // Create FormData for file upload
        const formData = new FormData();
        formData.append('image', file);
        
        // Upload image
        const response = await fetch(foodUrl, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to analyze image');
        }
        
        const data = await response.json();
        
        // Display results
        if (data.success) {
            resultDiv.className = 'food-result show';
            
            // Parse recommendation to extract status (YES/CAREFUL/NO)
            const recommendation = data.recommendation || '';
            let statusClass = 'careful';
            let statusText = 'CAREFUL';
            
            if (recommendation.toUpperCase().includes('YES')) {
                statusClass = 'yes';
                statusText = 'YES';
            } else if (recommendation.toUpperCase().includes('NO')) {
                statusClass = 'no';
                statusText = 'NO';
            }
            
            resultDiv.innerHTML = `
                <h4>🍽️ Meal Analysis</h4>
                <div class="food-meal">
                    <div class="meal-name">${data.meal.meal_name || 'Unidentified Meal'}</div>
                    <div class="calories">${data.meal.calories ? data.meal.calories + ' calories' : 'Calories: Not estimated'}</div>
                </div>
                ${data.recommendation ? `
                    <div class="food-recommendation">
                        <span class="status ${statusClass}">${statusText}</span>
                        <span>${data.recommendation}</span>
                    </div>
                ` : ''}
            `;
        } else {
            throw new Error('Analysis failed');
        }
        
    } catch (error) {
        resultDiv.className = 'food-result error show';
        let errorMsg = error.message;
        
        if (errorMsg.includes('Failed to fetch') || errorMsg.includes('NetworkError')) {
            errorMsg = 'Cannot connect to server. Please check:\n1. Backend server is running\n2. API URL is correct';
        }
        
        resultDiv.innerHTML = `
            <h4>❌ Error</h4>
            <p>${errorMsg}</p>
        `;
        console.error('Food upload error:', error);
    } finally {
        uploadBtn.disabled = false;
        uploadBtn.textContent = '📷 Upload Food Image';
    }
}

// Smart Image Upload (auto-detect glucose vs food)
function handleSmartImageSelect(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    if (!file.type.startsWith('image/')) {
        alert('Please select an image file!');
        return;
    }
    
    const reader = new FileReader();
    reader.onload = function(e) {
        const previewDiv = document.getElementById('smartImagePreview');
        const previewImg = document.getElementById('smartPreviewImg');
        previewImg.src = e.target.result;
        previewDiv.style.display = 'flex';
        
        uploadSmartImage(file);
    };
    reader.readAsDataURL(file);
}

function clearSmartImagePreview() {
    document.getElementById('smartImagePreview').style.display = 'none';
    document.getElementById('smartImageInput').value = '';
    document.getElementById('smartResult').classList.remove('show');
}

async function uploadSmartImage(file) {
    const uploadBtn = document.getElementById('smartUploadBtn');
    const resultDiv = document.getElementById('smartResult');
    const healthContext = document.getElementById('smartHealthContextInput').value.trim();
    
    uploadBtn.disabled = true;
    uploadBtn.textContent = '⏳ Analyzing...';
    
    resultDiv.className = 'smart-result loading show';
    resultDiv.innerHTML = '<p>🔄 Analyzing image...</p>';
    
    try {
        const chatApiUrl = document.getElementById('apiUrl').value;
        const baseUrl = chatApiUrl.replace('/api/chat', '');
        const smartUrl = new URL(baseUrl + '/api/ai/analyze-image');
        
        if (healthContext) {
            smartUrl.searchParams.append('health_context', healthContext);
        }
        
        const formData = new FormData();
        formData.append('image', file);
        
        const response = await fetch(smartUrl, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to analyze image');
        }
        
        const data = await response.json();
        resultDiv.className = 'smart-result show';
        
        if (data.type === 'glucose') {
            resultDiv.innerHTML = `
                <h4>🩺 Detected: Glucose Meter</h4>
                <span class="smart-type glucose">GLUCOSE</span>
                <div class="smart-reading">
                    <div class="value">${data.reading.value}</div>
                    <div class="unit">${data.reading.unit}</div>
                </div>
                ${data.analysis ? `
                    <div class="smart-recommendation">
                        <strong>Health Analysis:</strong>
                        <p>${data.analysis}</p>
                    </div>
                ` : ''}
            `;
        } else if (data.type === 'food') {
            const recommendation = data.recommendation || '';
            resultDiv.innerHTML = `
                <h4>🍽️ Detected: Food</h4>
                <span class="smart-type food">FOOD</span>
                <div class="smart-meal">
                    <div class="meal-name">${data.meal.meal_name || 'Unidentified Meal'}</div>
                    <div class="calories">${data.meal.calories ? data.meal.calories + ' calories' : 'Calories: Not estimated'}</div>
                </div>
                ${recommendation ? `
                    <div class="smart-recommendation">
                        <strong>Recommendation:</strong>
                        <p>${recommendation}</p>
                    </div>
                ` : ''}
            `;
        } else {
            throw new Error('Could not detect if image is glucose meter or food. Please upload a clear image.');
        }
        
    } catch (error) {
        resultDiv.className = 'smart-result error show';
        let errorMsg = error.message;
        
        if (errorMsg.includes('Failed to fetch') || errorMsg.includes('NetworkError')) {
            errorMsg = 'Cannot connect to server. Please check:\n1. Backend server is running\n2. API URL is correct';
        }
        
        resultDiv.innerHTML = `
            <h4>❌ Error</h4>
            <p>${errorMsg}</p>
        `;
        console.error('Smart upload error:', error);
    } finally {
        uploadBtn.disabled = false;
        uploadBtn.textContent = '📷 Upload Any Image';
    }
}

