from flask import Blueprint, request, jsonify
from models.model_user import UserData
from models.model_emotion import OpenCV
from models.model_history import History
from models.model_phq9 import PHQ9
from models.model_sentiment import Sentiment
import google.generativeai as genai
import nltk


user_bp = Blueprint('User', __name__ )

def getGeminiResponse(problem,age,name):
    inputPrompt = "My name is ${name}, i am ${age} years old, give me steps how to deal with ${problem} ? " 
    genai.configure(api_key='AIzaSyBT5ntUfk9RBtMZi34cnXqFELRpoh3_QGA')
    model = genai.GenerativeModel('gemini-1.5-flash')
    rawResponse = model.generate_content(inputPrompt)
    response = rawResponse.text.replace('\n', '').replace('*', '')
    return response 
    
    
@user_bp.route('/depression_score', methods=['POST'])
def depression_score():
    data = request.get_json()

    # Convert input scores from string to float
    try:
        history_score = float(data.get('_historyScore', 0.0))
        phq9_score = float(data.get('_phq9Score', 0.0))
        emotion_score = float(data.get('_sentimentalScore', 0.0))
        sentiment_score = float(data.get('_videoScore', 0.0))
    except ValueError:
        return jsonify({"message": "Invalid input. Scores must be floats."}), 400

    # Weights for each score component
    weights = {
        "history_wt": 0.2,
        "phq9_wt": 0.5,
        "sentiment_wt": 0.2,
        "opencv_wt": 0.1
    }

    # Calculate the weighted depression score
    depression_score = (
        (weights["history_wt"] * history_score) +
        (weights["phq9_wt"] * phq9_score) +
        (weights["opencv_wt"] * emotion_score) +
        (weights["sentiment_wt"] * sentiment_score)
    )

    print(depression_score)

    # Multiply the score by 100 and return as an integer
    depression_score = int(depression_score * 100)

    # Return the calculated depression score
    return jsonify({
        "message": "Successfully scored",
        "depression_score": depression_score
    }), 201

@user_bp.route('/results', methods=["POST"])
def result():
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "Invalid or missing JSON payload"}), 400

        required_keys = ['name', 'gender', 'depScore']
        for key in required_keys:
            if key not in data:
                return jsonify({"error": f"Missing key: {key}"}), 400

        name = data.get('name')
        gender = data.get('gender')
        score = data.get('depScore')
        severity = 0

        if score < 23:
            severity = 0
        elif score >= 23 and score < 42:
            severity = 1
        elif score >= 42 and score < 71:
            severity = 2
        else:
            severity = 3

        if severity == 0:
            disease = 'Depression Free'
        elif severity == 1:
            disease = 'mild depression'
        elif severity == 2:
            disease = 'mild to severe depression'
        else:
            disease = 'severe'

        advice = getGeminiResponse(disease, name, gender)

        response = {
            "name": name,
            "severity": disease,
            "advice": advice
        }

        return jsonify(response), 200

    except Exception as e:
        return jsonify({"error": "Internal server error"}), 500


def getGeminiResponse(problem, name, gender):
    input_prompt = f"My name is {name}, my gender is {gender}. Give me steps on how to deal with {problem} in 500 words"
    
    genai.configure(api_key='AIzaSyBT5ntUfk9RBtMZi34cnXqFELRpoh3_QGA')
    
    model = genai.GenerativeModel('gemini-1.5-flash')
    raw_response = model.generate_content(input_prompt)
    
    sentences = nltk.tokenize.sent_tokenize(raw_response.text.strip())
    
    structured_advice = [{"step": i + 1, "description": sentence} for i, sentence in enumerate(sentences)]

    return structured_advice


    







    

    