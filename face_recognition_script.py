
"""
import os
import cv2
import face_recognition
import numpy as np
import requests

API_URL = "http://127.0.0.1:5000/attendance"  # Flask backend URL
KNOWN_FACES_DIR = "known_faces"               # Folder with known faces

# -----------------------
# 1) Load known faces
# -----------------------
known_faces = []
known_names = []

for filename in os.listdir(KNOWN_FACES_DIR):
    if filename.lower().endswith((".jpg", ".jpeg", ".png")):
        img_path = os.path.join(KNOWN_FACES_DIR, filename)
        image = face_recognition.load_image_file(img_path)
        encodings = face_recognition.face_encodings(image)
        if encodings:
            known_faces.append(encodings[0])
            # Use the filename (without extension) as the person's name
            known_names.append(os.path.splitext(filename)[0])

print(f"✅ Loaded {len(known_faces)} known faces.")

# -----------------------
# 2) Open Webcam
# -----------------------
video_capture = cv2.VideoCapture(0)
if not video_capture.isOpened():
    print("Error: Could not open webcam.")
    exit()

# Set to track which names (including "Unknown") have been recorded in this session
recorded_names_this_session = set()

while True:
    ret, frame = video_capture.read()
    if not ret or frame is None:
        print("Error: Could not read frame from webcam.")
        break

    # Convert from BGR (OpenCV) to RGB (face_recognition)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # -----------------------
    # 3) Detect & Encode Faces
    # -----------------------
    face_locations = face_recognition.face_locations(rgb_frame)
    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

    # Create a list to store detection results for this frame
    detections = []  # Each element will be a dict: { "name": <str>, "location": (top, right, bottom, left) }

    for face_encoding, (top, right, bottom, left) in zip(face_encodings, face_locations):
        # Default name is "Unknown"
        name = "Unknown"
        matches = face_recognition.compare_faces(known_faces, face_encoding, tolerance=0.5)
        face_distances = face_recognition.face_distance(known_faces, face_encoding)
        if True in matches:
            best_match_index = np.argmin(face_distances)
            name = known_names[best_match_index]
        detections.append({"name": name, "location": (top, right, bottom, left)})

    # -----------------------
    # 4) Record Attendance (After Recognition)
    # -----------------------
    for detection in detections:
        name = detection["name"]
        if name not in recorded_names_this_session:
            recorded_names_this_session.add(name)
            if name == "Unknown":
                # Print a message for unknown faces without sending a POST request
                print("Sorry, attendance not recorded as student not registered yet")
            else:
                payload = {"name": name}
                try:
                    response = requests.post(API_URL, json=payload)
                    if response.status_code in (200, 201):
                        try:
                            data = response.json()
                            print(data.get("message", "No message in response"))
                            if "timestamp" in data:
                                print("Recorded at:", data["timestamp"])
                        except ValueError:
                            print("Server returned non-JSON:", response.text)
                    else:
                        print(f"Server returned status code {response.status_code}")
                        print("Response text:", response.text)
                except Exception as e:
                    print("Error sending request:", e)

    # -----------------------
    # 5) Draw Rectangles & Labels
    # -----------------------
    for detection in detections:
        name = detection["name"]
        top, right, bottom, left = detection["location"]
        # Green for recognized, red for unknown
        color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)
        cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
        cv2.putText(frame, name, (left, top - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

    # Show the camera feed
    cv2.imshow("Face Recognition Attendance", frame)

    # Press 'q' to quit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

video_capture.release()
cv2.destroyAllWindows()
"""

import os
import cv2
import face_recognition
import numpy as np
import requests
import hashlib
import time  # to get a numeric timestamp

API_URL = "http://127.0.0.1:5000/attendance"  # Flask backend URL
KNOWN_FACES_DIR = "known_faces"               # Folder with known faces

SECRET_KEY = "YourSecretKeyHere"  # Keep this private, e.g., in an .env file

def compute_attendance_hash(name: str, timestamp: int, secret_key: str) -> str:
    """
    Combine the name, timestamp, and a secret key, then compute a SHA-256 hash.
    """
    data_str = f"{name}|{timestamp}|{secret_key}"
    return hashlib.sha256(data_str.encode("utf-8")).hexdigest()

# -----------------------
# 1) Load known faces
# -----------------------
known_faces = []
known_names = []

for filename in os.listdir(KNOWN_FACES_DIR):
    if filename.lower().endswith((".jpg", ".jpeg", ".png")):
        img_path = os.path.join(KNOWN_FACES_DIR, filename)
        image = face_recognition.load_image_file(img_path)
        encodings = face_recognition.face_encodings(image)
        if encodings:
            known_faces.append(encodings[0])
            known_names.append(os.path.splitext(filename)[0])

print(f"✅ Loaded {len(known_faces)} known faces.")

# -----------------------
# 2) Open Webcam
# -----------------------
video_capture = cv2.VideoCapture(0)
if not video_capture.isOpened():
    print("Error: Could not open webcam.")
    exit()

# Keep track of which names have been recorded this session
recorded_names_this_session = set()

while True:
    ret, frame = video_capture.read()
    if not ret or frame is None:
        print("Error: Could not read frame from webcam.")
        break

    # Convert from BGR to RGB
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Detect & encode faces
    face_locations = face_recognition.face_locations(rgb_frame)
    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

    detections = []  # e.g. [ {"name": "Alice", "location": (top, right, bottom, left)}, ... ]

    for face_encoding, (top, right, bottom, left) in zip(face_encodings, face_locations):
        name = "Unknown"
        matches = face_recognition.compare_faces(known_faces, face_encoding, tolerance=0.5)
        face_distances = face_recognition.face_distance(known_faces, face_encoding)
        if True in matches:
            best_match_index = np.argmin(face_distances)
            name = known_names[best_match_index]
        detections.append({"name": name, "location": (top, right, bottom, left)})

    # Record attendance after recognition
    for detection in detections:
        name = detection["name"]
        if name not in recorded_names_this_session:
            recorded_names_this_session.add(name)
            if name == "Unknown":
                print("Sorry, attendance not recorded as student not registered yet")
            else:
                # Compute a numeric timestamp
                record_time = int(time.time())

                # Compute the hash
                record_hash = compute_attendance_hash(name, record_time, SECRET_KEY)

                # Send to Flask
                payload = {
                    "name": name,
                    "timestamp": record_time,   # we send an int
                    "hash": record_hash
                }
                try:
                    response = requests.post(API_URL, json=payload)
                    if response.status_code in (200, 201):
                        try:
                            data = response.json()
                            print(data.get("message", "No message in response"))
                            if "timestamp" in data:
                                print("Recorded at:", data["timestamp"])
                        except ValueError:
                            print("Server returned non-JSON:", response.text)
                    else:
                        print(f"Server returned status code {response.status_code}")
                        print("Response text:", response.text)
                except Exception as e:
                    print("Error sending request:", e)

    # Draw rectangles
    for detection in detections:
        name = detection["name"]
        top, right, bottom, left = detection["location"]
        color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)
        cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
        cv2.putText(frame, name, (left, top - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

    cv2.imshow("Face Recognition Attendance", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

video_capture.release()
cv2.destroyAllWindows()
