import os
import pickle
import re
import numpy as np
from flask import Blueprint, request, jsonify
from models.model_sentiment import Sentiment
from nltk.stem import PorterStemmer
from nltk.tokenize import word_tokenize
import nltk
from scipy.sparse import hstack
from sklearn.feature_extraction.text import TfidfVectorizer


nltk.download('punkt')
nltk.download('punkt_tab')


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
        "Normal" :0,
        "Depression":3.7,
        "Suicidal": 4,
        "Anxiety": 0.7,
        "Bipolar": 1,
        "Stress": 1.5,
        "Personality disorder":0.5
    }
    
    score1 = prediction_point.get(predic1,0)
    score2 = prediction_point.get(predic2,0)

    total_score = (score1+score2)/8.0

    return total_score


@sentiment_bp.route('/process_sentiment', methods=['POST'])
def process_sentiment():
    data = request.get_json()
    
    text1 = data.get('text_1')
    text2 = data.get('text_2')
    
    if not (text1 and text2):
        return jsonify({"error": "User sentiment data not found"}), 404

    predicted_status1 = predict_status(text1)
    original_status1 = label_encoder.inverse_transform([predicted_status1])[0]

    predicted_status2 = predict_status(text2)
    original_status2 = label_encoder.inverse_transform([predicted_status2])[0]

    cumalative_score = calculate_score(original_status1,original_status2)

    return jsonify({
        "message": "Sentiment data processed successfully!",
        "ml_s1": original_status1,
        "ml_s2": original_status2,
        "score" : cumalative_score
    }), 200