import cv2
import cvzone
import math
import requests  # Import requests to send alerts
from ultralytics import YOLO
from flask import Flask, Response, jsonify
from flask_cors import CORS
import time
app = Flask(__name__)
CORS(app)  # Allow request

# Initialize webcam
cap = cv2.VideoCapture(0)

# Load YOLOv8 model
model = YOLO('yolov8s.pt')

# Load class names
classnames = []
with open('classes.txt', 'r') as f:
    classnames = f.read().splitlines()

fall_detected = False  # Flag for fall detection
WEBSITE_URL = "http://localhost:5000/fall_status"  # Replace with actual website API endpoint

def send_fall_notification(status):
    """Send fall detection status to the website via API."""
    print("Fall detected:", status)
    try:
        response = requests.post(WEBSITE_URL, json={"fall_detected": status})
        print(f"Notification sent: {response.status_code}")
    except Exception as e:
        print(f"Error sending notification: {e}")

def generate_frames():
    global fall_detected
    while True:
       
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame")
            break

        frame = cv2.resize(frame, (980, 740))  # Resize frame
        results = model(frame)

        for info in results:
            parameters = info.boxes
            for box in parameters:
                x1, y1, x2, y2 = box.xyxy[0]
                x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                confidence = box.conf[0]
                class_detect = classnames[int(box.cls[0])]
                conf = math.ceil(confidence * 100)

                height = y2 - y1
                width = x2 - x1
                ratio = height / width  # Calculate ratio
                threshold_ratio = 0.8  # Adjustable threshold

                # Bounding box
                if conf > 80 and class_detect == 'person':
                    cvzone.cornerRect(frame, [x1, y1, width, height], l=30, rt=6)

                # Fall detection
                new_fall_status = ratio < threshold_ratio
                if new_fall_status != fall_detected:  # Only send update if status changes
                    fall_detected = new_fall_status  # Update global variable
                    time.sleep(1)
                    send_fall_notification(fall_detected)

        # Encode the frame for live streaming
        _, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/fall_status')
def get_fall_status():
    global fall_detected  # Return actual detection status
    response = jsonify({"fall_detected": fall_detected})
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Methods", "GET, OPTIONS")
    response.headers.add("Access-Control-Allow-Headers", "Content-Type")
    return response

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

# Release webcam when done
cap.release()
cv2.destroyAllWindows()