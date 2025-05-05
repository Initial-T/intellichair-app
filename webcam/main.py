import cv2
import cvzone
import math
import requests  # Import requests to send alerts
from ultralytics import YOLO
from flask import Flask, Response, jsonify
from flask_cors import CORS
import time
import threading # Add this import

app = Flask(__name__)
CORS(app)  # Allow request

# Initialize webcam
cap = cv2.VideoCapture(2) # Make sure camera index 2 is correct

# Load YOLOv8 model
model = YOLO('yolov8s.pt') # Ensure this file is in the same directory or provide the full path

# Load class names
classnames = []
try:
    with open('classes.txt', 'r') as f: # Ensure this file is in the same directory
        classnames = f.read().splitlines()
except FileNotFoundError:
    print("Error: 'classes.txt' not found. Make sure the file exists in the correct directory.")
    # Optionally exit or handle this error appropriately
    exit()


fall_detected = False  # Flag for fall detection
WEBSITE_URL = "http://localhost:5000/fall_status"  # API endpoint on the same Flask app

# Helper function to run the request in a thread
def _send_request(url, data):
    try:
        # Add a timeout to prevent indefinite blocking
        response = requests.post(url, json=data, timeout=5)
        print(f"Notification sent: {response.status_code}")
    except requests.exceptions.Timeout:
        print("Error sending notification: Request timed out.")
    except requests.exceptions.RequestException as e: # Catch specific request errors
        print(f"Error sending notification: {e}")
    except Exception as e:
        print(f"An unexpected error occurred during notification: {e}")


def send_fall_notification(status):
    """Send fall detection status to the website via API in a non-blocking way."""
    print("Fall detected:", status)
    # Create and start a new thread to send the notification
    notification_thread = threading.Thread(target=_send_request, args=(WEBSITE_URL, {"fall_detected": status}))
    notification_thread.daemon = True # Allow program to exit even if thread is running
    notification_thread.start() # Start the thread, the main code continues immediately


def generate_frames():
    global fall_detected
    frame_count = 0 # Add a frame counter
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame")
            # Attempt to reconnect or break
            time.sleep(0.5) # Wait a bit before retrying or breaking
            # Optionally try cap.open(2) again here
            break # Or break if reconnection is not desired

        # Resize frame for display and potentially reduce processing load if done before model
        display_frame = cv2.resize(frame, (980, 740))

        # --- Optimization: Resize before model inference ---
        # Smaller frame for model processing can significantly speed things up
        # model_frame = cv2.resize(frame, (640, 480)) # Example smaller size

        # Only process every Nth frame to reduce load
        if frame_count % 3 == 0:
            # results = model(model_frame) # Use resized frame if optimizing
            results = model(display_frame) # Use display frame if not optimizing resize before model

            current_frame_fall_status = False # Assume no fall in this frame initially
            person_detected_in_frame = False

            for info in results:
                parameters = info.boxes
                for box in parameters:
                    x1, y1, x2, y2 = box.xyxy[0]
                    x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                    confidence = box.conf[0]
                    class_index = int(box.cls[0])

                    # Ensure class_index is valid before accessing classnames
                    if 0 <= class_index < len(classnames):
                        class_detect = classnames[class_index]
                        conf = math.ceil(confidence * 100)

                        if class_detect == 'person' and conf > 80: # Confidence threshold
                            person_detected_in_frame = True
                            height = y2 - y1
                            width = x2 - x1

                            # Draw bounding box on the display frame
                            cvzone.cornerRect(display_frame, [x1, y1, width, height], l=30, rt=6)

                            # Fall detection logic
                            ratio = height / width if width > 0 else 0
                            threshold_ratio = 0.8  # Adjustable threshold

                            if ratio < threshold_ratio and width > 0:
                                current_frame_fall_status = True
                                # Optional: Draw indication on frame
                                cv2.putText(display_frame, "FALL DETECTED", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
                                break # Found a fall, no need to check other boxes in this frame
                if current_frame_fall_status:
                    break # Exit outer loop too if fall detected

            # Update global status only if a person was detected in the frame
            # This prevents triggering 'fall_detected = False' if no person is seen
            if person_detected_in_frame:
                if current_frame_fall_status != fall_detected:
                    fall_detected = current_frame_fall_status  # Update global variable
                    send_fall_notification(fall_detected) # Send notification (non-blocking)
            # If no person is detected for several frames, maybe reset fall_detected? (Optional logic)


        frame_count += 1 # Increment frame counter

        # Encode the display frame for live streaming
        try:
            ret_encode, buffer = cv2.imencode('.jpg', display_frame)
            if ret_encode:
                frame_bytes = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            else:
                print("Failed to encode frame")
        except Exception as e:
            print(f"Error encoding frame: {e}")
            continue # Skip this frame if encoding fails

@app.route('/video_feed')
def video_feed():
    # Ensure generate_frames() handles camera errors gracefully
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/fall_status')
def get_fall_status():
    global fall_detected
    response = jsonify({"fall_detected": fall_detected})
    # CORS headers are handled globally by CORS(app) if configured correctly,
    # but adding them here doesn't hurt if needed for specific routes.
    # response.headers.add("Access-Control-Allow-Origin", "*")
    return response

if __name__ == '__main__':
    # Use threaded=True for Flask dev server to handle multiple requests better
    # Use debug=False in production
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)

# This part might not be reached if Flask runs indefinitely,
# consider adding cleanup logic elsewhere if needed (e.g., signal handling)
print("Releasing webcam...")
cap.release()
cv2.destroyAllWindows()
print("Webcam released.")