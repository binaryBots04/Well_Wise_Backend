from flask import Flask, request, jsonify, Blueprint
import os
from groclake.cataloglake import CatalogLake
from groclake.modellake import ModelLake  # Add this import
from flask_cors import CORS

chat_bot = Blueprint('chatbot', __name__)

# Environment variable setup
GROCLAKE_API_KEY = 'a3c65c2974270fd093ee8a9bf8ae7d0b'
GROCLAKE_ACCOUNT_ID = 'cecf88db41531add5d0cefaa83fedb38'
os.environ['GROCLAKE_API_KEY'] = GROCLAKE_API_KEY
os.environ['GROCLAKE_ACCOUNT_ID'] = GROCLAKE_ACCOUNT_ID

# Initialize both CatalogLake and ModelLake instances
catalog = CatalogLake()
model_lake = ModelLake()  # Add this line

# Chatbot configuration
CHATBOT_CONFIG = {
    "name": "Well Wise",
    "description": "I am a virtual doctor/therapist here to assist you with medical questions specially mental health",
    "instructions": "Please provide helpful and accurate medical advice based on the symptoms described.",
    "conversation_starters": [
        "Why do I feel so sad all the time?",
        "Is it normal to feel like I'm not good enough?",
        "How can I stop feeling so overwhelmed?",
        "Why do I feel tired even when I do nothing?",
        "Can you help me understand why I feel this way?",
        "What are the symptoms of a cold?",
        "Can you help me with my headache?",
        "What should I do if I have a fever?"
    ]
}

# Store conversation histories for different sessions
conversation_histories = {}

@chat_bot.route('/api/chat/config', methods=['GET'])
def get_config():
    """Get chatbot configuration"""
    return jsonify(CHATBOT_CONFIG)

@chat_bot.route('/api/chat/message', methods=['POST'])
def chat_message():
    """Process a chat message"""
    try:
        data = request.json
        user_input = data.get('message')
        
        if not user_input:
            return jsonify({"error": "Message is required"}), 400
            
        # Append user's input to conversation history
        conversation_history.append({
            "role": "user",
            "content": user_input
        })
        
        # Create the payload
        payload = {
            "messages": conversation_history,
            "token_size": 300
        }
        
        # Get response from model using model_lake instead of catalog
        try:
            response = model_lake.chat_complete(payload=payload)  # Changed this line
            bot_reply = response.get('answer', 'Sorry, I couldn\'t process that.')
            
            # Append bot's reply to conversation history
            conversation_history.append({
                "role": "assistant",
                "content": bot_reply
            })
            
            return jsonify({
                "reply": bot_reply,
                "conversation_history": conversation_history
            })
            
        except Exception as e:
            return jsonify({"error": f"Model processing error: {str(e)}"}), 500
            
    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@chat_bot.route('/api/chat/history', methods=['GET'])
def get_chat_history():
    """Get chat history"""
    return jsonify({"conversation_history": conversation_history})

@chat_bot.route('/api/chat/reset', methods=['POST'])
def reset_chat():
    """Reset chat history"""
    conversation_history.clear()
    return jsonify({"message": "Chat history reset successfully"})