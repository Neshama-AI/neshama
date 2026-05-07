"""
Chat API - WebSocket-based chat functionality.
"""

import asyncio
import json
import random
from typing import Dict, Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException

router = APIRouter()

# Mock conversation storage
CONVERSATION_HISTORY = [
    {
        "id": "msg1",
        "role": "user",
        "content": "Hello! Can you tell me about the OCEAN personality model?",
        "timestamp": "2024-01-15T10:00:00"
    },
    {
        "id": "msg2",
        "role": "assistant",
        "content": "The OCEAN model is a widely-used framework for describing human personality. It includes Openness, Conscientiousness, Extraversion, Agreeableness, and Neuroticism. Would you like me to explain each dimension in detail?",
        "timestamp": "2024-01-15T10:00:05"
    },
    {
        "id": "msg3",
        "role": "user",
        "content": "Yes, please! Especially Openness and its importance.",
        "timestamp": "2024-01-15T10:01:00"
    },
    {
        "id": "msg4",
        "role": "assistant",
        "content": "Openness to Experience reflects how curious, creative, and open-minded someone is. High openness indicates imagination, appreciation for art, and willingness to try new things. Low openness suggests preference for routine and conventional approaches. In AI agents, openness can influence creative problem-solving and adaptation to new situations.",
        "timestamp": "2024-01-15T10:01:10"
    }
]


MOCK_RESPONSES = [
    "That's an interesting question! Let me think about this carefully.",
    "I understand what you're saying. Here's my perspective on this...",
    "Great question! This is something I find quite fascinating.",
    "I'd be happy to help you with that. Let me explain...",
    "Based on my understanding, I can share some insights with you.",
    "That's a thoughtful observation. Let me respond to that.",
    "I appreciate you sharing that with me. Here's what I think...",
    "Interesting point! This reminds me of something important.",
    "I see what you mean. Let me elaborate on this topic.",
    "Thank you for asking! Here's my detailed response..."
]


class ConnectionManager:
    """WebSocket connection manager."""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.user_sessions: Dict[str, Dict] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str):
        """Connect a new WebSocket client."""
        await websocket.accept()
        self.active_connections.append(websocket)
        self.user_sessions[session_id] = {
            "connected_at": datetime.now().isoformat(),
            "message_count": 0
        }
    
    def disconnect(self, websocket: WebSocket, session_id: str):
        """Disconnect a WebSocket client."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if session_id in self.user_sessions:
            del self.user_sessions[session_id]
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send a personal message to a client."""
        await websocket.send_text(message)
    
    async def broadcast(self, message: str):
        """Broadcast a message to all connected clients."""
        for connection in self.active_connections:
            await connection.send_text(message)


manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_chat(websocket: WebSocket, session_id: str = "default"):
    """WebSocket endpoint for chat."""
    await manager.connect(websocket, session_id)
    
    try:
        # Send welcome message
        await websocket.send_json({
            "type": "system",
            "content": "Connected to Neshama Soul Panel",
            "timestamp": datetime.now().isoformat()
        })
        
        # Send conversation history
        await websocket.send_json({
            "type": "history",
            "data": CONVERSATION_HISTORY
        })
        
        while True:
            # Receive message
            data = await websocket.receive_text()
            
            try:
                message_data = json.loads(data)
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "content": "Invalid JSON message"
                })
                continue
            
            if message_data.get("type") == "message":
                user_message = message_data.get("content", "")
                
                # Add to history
                msg_id = f"msg_{datetime.now().strftime('%H%M%S')}"
                CONVERSATION_HISTORY.append({
                    "id": msg_id,
                    "role": "user",
                    "content": user_message,
                    "timestamp": datetime.now().isoformat()
                })
                
                # Send typing indicator
                await websocket.send_json({
                    "type": "typing",
                    "content": "..."
                })
                
                # Simulate processing delay
                await asyncio.sleep(random.uniform(0.5, 1.5))
                
                # Generate response
                response_content = random.choice(MOCK_RESPONSES)
                
                # Add response to history
                response_id = f"msg_{datetime.now().strftime('%H%M%S')}"
                CONVERSATION_HISTORY.append({
                    "id": response_id,
                    "role": "assistant",
                    "content": response_content,
                    "timestamp": datetime.now().isoformat()
                })
                
                # Send response
                await websocket.send_json({
                    "type": "message",
                    "id": response_id,
                    "role": "assistant",
                    "content": response_content,
                    "timestamp": datetime.now().isoformat(),
                    "emotion": {
                        "category": random.choice(["joy", "trust", "anticipation"]),
                        "intensity": round(random.uniform(0.3, 0.7), 2)
                    }
                })
    
    except WebSocketDisconnect:
        manager.disconnect(websocket, session_id)
    except Exception as e:
        manager.disconnect(websocket, session_id)


@router.get("/history")
async def get_chat_history(limit: int = 50):
    """Get chat history."""
    return {
        "success": True,
        "data": {
            "messages": CONVERSATION_HISTORY[-limit:],
            "total": len(CONVERSATION_HISTORY)
        }
    }


@router.delete("/history")
async def clear_chat_history():
    """Clear chat history."""
    global CONVERSATION_HISTORY
    CONVERSATION_HISTORY = []
    return {
        "success": True,
        "message": "Chat history cleared"
    }
