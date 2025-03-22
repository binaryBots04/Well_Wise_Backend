import os
import pickle
import re
import requests
import numpy as np
import speech_recognition as sr
from flask import Blueprint, request, jsonify
from models.model_sentiment import Sentiment
from nltk.stem import PorterStemmer
from nltk.tokenize import word_tokenize
import nltk
from scipy.sparse import hstack
from sklearn.feature_extraction.text import TfidfVectorizer
from pydub import AudioSegment

nltk.download('punkt')

sentiment_bp = Blueprint('sentiment', __name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ML_DIR = os.path.join(BASE_DIR, '../ml')
VECTOR_PATH = os.path.join(ML_DIR, 'tfidf_vectorizer.pkl')
MODEL_PATH = os.path.join(ML_DIR, 'trained_model.pkl')
LABEL_ENCODER_PATH = os.path.join(ML_DIR, 'label_encoder.pkl')

try:
    vectorizer = pickle.load(open(VECTOR_PATH, 'rb'))
    logreg = pickle.load(open(MODEL_PATH, 'rb'))
    label_encoder = pickle.load(open(LABEL_ENCODER_PATH, 'rb'))
except Exception as e:
    print(f"Error loading model files: {e}")
    raise RuntimeError("Failed to load model files.")

def preprocess_text(text):
    stemmer = PorterStemmer()
    text = str(text).lower()
    text = re.sub(r'http[s]?://\S+', '', text)
    text = re.sub(r'\[.*?\]\(.*?\)', '', text)
    text = re.sub(r'@\w+', '', text)
    text = re.sub(r'[^\w\s]', '', text)
    tokens = word_tokenize(text)
    stemmed_tokens = ' '.join(stemmer.stem(token) for token in tokens)
    return stemmed_tokens

def predict_status(text):
    preprocessed_text = preprocess_text(text)
    text_tfidf = vectorizer.transform([preprocessed_text])
    num_features = np.array([[len(text), len(re.findall(r'\.', text))]])
    combined_features = hstack([text_tfidf, num_features])
    prediction = logreg.predict(combined_features)
    return prediction[0]

def calculate_score(predic1 , predic2):
    prediction_point = {
        "Normal": 0,
        "Depression": 3.7,
        "Suicidal": 4,
        "Anxiety": 0.7,
        "Bipolar": 1,
        "Stress": 1.5,
        "Personality disorder": 0.5
    }

    score1 = prediction_point.get(predic1, 0)
    score2 = prediction_point.get(predic2, 0)

    total_score = (score1 + score2) / 8.0
    return total_score

def fetch_audio_from_pinata(ipfs_hash):
  
    ipfs_gateway = f"https://gateway.pinata.cloud/ipfs/{ipfs_hash}"
    
    response = requests.get(ipfs_gateway)
    if response.status_code == 200:
        audio_path = os.path.join(BASE_DIR, "temp_audio")
        with open(audio_path, "wb") as audio_file:
            audio_file.write(response.content)

        converted_audio_path = f"{audio_path}.wav"
        try:
            audio = AudioSegment.from_file(audio_path)  
            audio.export(converted_audio_path, format="wav") 
            os.remove(audio_path)  
            return converted_audio_path 
        except Exception as e:
            raise Exception(f"Audio conversion failed: {e}")

    else:
        raise Exception("Failed to retrieve audio from IPFS.")

def convert_audio_to_text(audio_path):
    recognizer = sr.Recognizer()
    
    with sr.AudioFile(audio_path) as source:
        audio = recognizer.record(source)
    
    try:
        text = recognizer.recognize_google(audio)
        return text
    except sr.UnknownValueError:
        return "Speech not recognized"
    except sr.RequestError:
        return "Speech recognition service unavailable"

@sentiment_bp.route('/process_sentiment', methods=['POST'])
def process_sentiment():
    data = request.get_json()
    
    text1 = data.get('text_1')
    pinata_hash = data.get('text_2_ipfs')

    if not text1:
        return jsonify({"error": "User sentiment data for text_1 not found"}), 404

    predicted_status1 = predict_status(text1)
    original_status1 = label_encoder.inverse_transform([predicted_status1])[0]

    try:
        if not pinata_hash:
            return jsonify({"error": "IPFS hash for text_2 not provided"}), 400
        
        audio_path = fetch_audio_from_pinata(pinata_hash)
        text2 = convert_audio_to_text(audio_path)
        os.remove(audio_path)
        
        predicted_status2 = predict_status(text2)
        original_status2 = label_encoder.inverse_transform([predicted_status2])[0]
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    cumulative_score = calculate_score(original_status1, original_status2)

    return jsonify({
        "message": "Sentiment data processed successfully!",
        "ml_s1": original_status1,
        "ml_s2": original_status2,
        "text_2": text2,
        "score": cumulative_score
    }), 200
