from flask import Flask, Response, jsonify, Blueprint, request
import cv2
import mediapipe as mp
import time
import threading
import json
from datetime import datetime
from scipy.spatial import distance

emotion_detection = Blueprint('emotion', __name__)

cap = None
processing = False
blink_counter = 0
total_blinks = 0
emotion_counts = {}
capture_interval = 1
last_capture_time = None
start_time = None  # Track start time of the session

mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)
mp_draw = mp.solutions.drawing_utils

EYE_AR_THRESH = 0.42
EYE_AR_CONSEC_FRAMES = 2

LEFT_EYE = [362, 385, 387, 263, 373, 380]
RIGHT_EYE = [33, 160, 158, 133, 153, 144]

def calculate_EAR(landmarks, eye_indices):
    left = landmarks[eye_indices[0]]
    right = landmarks[eye_indices[3]]
    
    top1 = landmarks[eye_indices[1]]
    top2 = landmarks[eye_indices[2]]
    
    bottom1 = landmarks[eye_indices[4]]
    bottom2 = landmarks[eye_indices[5]]
    
    vertical_dist1 = distance.euclidean([top1.x, top1.y], [bottom1.x, bottom1.y])
    vertical_dist2 = distance.euclidean([top2.x, top2.y], [bottom2.x, bottom2.y])
    horizontal_dist = distance.euclidean([left.x, left.y], [right.x, right.y])
    
    ear = (vertical_dist1 + vertical_dist2) / (2 * horizontal_dist)
    return ear

def process_frame():
    global cap, processing, blink_counter, total_blinks, last_capture_time, emotion_counts, start_time
    while processing:
        success, frame = cap.read()
        if not success:
            break
        
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(rgb_frame)
        
        if results.multi_face_landmarks:
            for face_landmarks in results.multi_face_landmarks:
                left_ear = calculate_EAR(face_landmarks.landmark, LEFT_EYE)
                right_ear = calculate_EAR(face_landmarks.landmark, RIGHT_EYE)
                
                ear = (left_ear + right_ear) / 2.0
                
                mp_draw.draw_landmarks(
                    frame,
                    face_landmarks,
                    mp_face_mesh.FACEMESH_CONTOURS,
                    landmark_drawing_spec=None,
                    connection_drawing_spec=mp_draw.DrawingSpec(color=(0, 255, 0), thickness=1, circle_radius=1)
                )
                
                if ear < EYE_AR_THRESH:
                    blink_counter += 1
                else:
                    if blink_counter >= EYE_AR_CONSEC_FRAMES:
                        total_blinks += 1
                    blink_counter = 0
                
                cv2.putText(frame, f"EAR: {ear:.2f}", (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        cv2.putText(frame, f"Blinks: {total_blinks}", (10, 70),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        frame = cv2.resize(frame, (640, 360))
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@emotion_detection.route('/start_session', methods=['GET'])
def start_session():
    global cap, processing, blink_counter, total_blinks, last_capture_time, emotion_counts, start_time
    if processing:  # Prevent starting a session if one is already running
        return jsonify({"status": "error", "message": "Session already running"}), 400
    
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        return jsonify({"status": "error", "message": "Failed to open camera"}), 500
    
    processing = True
    blink_counter = 0
    total_blinks = 0
    score = 0
    last_capture_time = time.time()
    emotion_counts = {}
    start_time = time.time()  # Store the start time of the session
    threading.Thread(target=process_frame).start()
    return jsonify({"status": "session started"})

@emotion_detection.route('/stop_session', methods=['GET'])
def stop_session():
    global cap, processing, start_time
    if not processing:
        return jsonify({"status": "error", "message": "No active session"}), 400
    
    processing = False
    if cap and cap.isOpened():
        cap.release()
    
    # Calculate elapsed time in seconds
    elapsed_time = time.time() - start_time
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"detected_emotion_counts_{timestamp}.json"
    
    # Save emotion counts to JSON file
    with open(output_file, 'w') as json_file:
        json.dump(emotion_counts, json_file)

    bpm = (total_blinks*60)/round(elapsed_time)

    if(bpm <= 8):
        score = 3
    elif(bpm > 8 and bpm <= 12 ):
        score = 2
    elif(bpm >12 and bpm<=20):
        score = 0
    else:
        score=1

    score = score/3.0

    return jsonify({
        "status": "session stopped",
        "total_blinks": total_blinks,
        "elapsed_time": round(elapsed_time, 2),
        "blinks"  : bpm,
        "cv_score" : score
    })

@emotion_detection.route('/video_feed')
def video_feed():
    if not processing:
        return jsonify({"status": "error", "message": "No active session"}), 400
    return Response(process_frame(), mimetype='multipart/x-mixed-replace; boundary=frame')