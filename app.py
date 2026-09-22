import cv2
import os
import time
from flask import Flask, render_template, Response, jsonify, request
from database import (
    init_db, get_all_vehicles, add_vehicle, delete_vehicle,
    get_recent_logs, log_access, is_plate_registered
)
from anpr import ANPREngine
from generate_sample_video import create_sample_video

app = Flask(__name__)

# Global ANPR Engine & Video State
anpr_engine = ANPREngine()
current_source_type = "sample"  # Default to sample video for instant beginner test
sample_video_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sample_traffic.mp4")

# Ensure sample video exists
if not os.path.exists(sample_video_path):
    create_sample_video()

def get_video_capture():
    """Retrieve video capture object based on current source type."""
    global current_source_type, sample_video_path
    if current_source_type == "webcam":
        print("Opening webcam (Index 0)...")
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("Webcam unavailable. Falling back to sample video stream.")
            current_source_type = "sample"
            return cv2.VideoCapture(sample_video_path)
        return cap
    else:
        if not os.path.exists(sample_video_path):
            create_sample_video()
        return cv2.VideoCapture(sample_video_path)

def generate_frames():
    """MJPEG stream frame generator with looping for sample video."""
    global current_source_type
    cap = get_video_capture()

    while True:
        success, frame = cap.read()
        if not success:
            # Loop sample video when reaching end
            if current_source_type == "sample":
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue
            else:
                time.sleep(0.1)
                continue

        # Process frame with ANPR detection engine
        processed_frame = anpr_engine.process_frame(frame)

        # Encode frame to JPEG
        ret, buffer = cv2.imencode('.jpg', processed_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
        if not ret:
            continue

        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

        time.sleep(0.03)  # ~30 FPS throttle

@app.route('/')
def index():
    """Render main dashboard view."""
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    """Endpoint for live video MJPEG stream."""
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/status')
def api_status():
    """Return real-time ANPR status metrics."""
    status = anpr_engine.get_status_dict()
    status["source"] = current_source_type
    return jsonify(status)

@app.route('/api/logs')
def api_logs():
    """Return recent vehicle access logs."""
    logs = get_recent_logs(limit=25)
    return jsonify(logs)

@app.route('/api/vehicles', methods=['GET', 'POST', 'DELETE'])
def api_vehicles():
    """API for viewing, adding, and deleting registered vehicles."""
    if request.method == 'GET':
        vehicles = get_all_vehicles()
        return jsonify(vehicles)

    elif request.method == 'POST':
        data = request.get_json() or {}
        plate = data.get('plate_number', '').strip()
        owner = data.get('owner_name', 'Authorized Guest').strip()
        vtype = data.get('vehicle_type', 'Car').strip()

        if not plate:
            return jsonify({"success": False, "message": "Plate number is required"}), 400

        success, msg = add_vehicle(plate, owner, vtype)
        return jsonify({"success": success, "message": msg})

    elif request.method == 'DELETE':
        data = request.get_json() or {}
        plate = data.get('plate_number', '').strip()
        if not plate:
            return jsonify({"success": False, "message": "Plate number is required"}), 400

        delete_vehicle(plate)
        return jsonify({"success": True, "message": f"Vehicle {plate} removed successfully."})

@app.route('/api/toggle_source', methods=['POST'])
def toggle_source():
    """Toggle video feed source between Sample Video and Live Webcam."""
    global current_source_type
    data = request.get_json() or {}
    new_source = data.get('source', 'sample')

    if new_source in ['sample', 'webcam']:
        current_source_type = new_source
        return jsonify({"success": True, "source": current_source_type})
    return jsonify({"success": False, "message": "Invalid source"}), 400

@app.route('/api/manual_gate', methods=['POST'])
def manual_gate():
    """Simulate manual gate open/close override from admin dashboard."""
    data = request.get_json() or {}
    action = data.get('action', 'OPEN')

    if action == 'OPEN':
        anpr_engine.gate_status = "GATE OPEN"
        anpr_engine.vehicle_status = "MANUAL OVERRIDE"
        anpr_engine.last_detected_plate = "MANUAL_OPEN"
        log_access("MANUAL_OPEN", "GATE OPEN", "MANUAL OVERRIDE", "Admin Override")
    else:
        anpr_engine.gate_status = "GATE CLOSED"
        anpr_engine.vehicle_status = "MANUAL OVERRIDE"
        log_access("MANUAL_CLOSE", "GATE CLOSED", "MANUAL OVERRIDE", "Admin Override")

    return jsonify({"success": True, "status": anpr_engine.get_status_dict()})

if __name__ == '__main__':
    # Initialize database
    init_db()
    
    print("\n" + "="*60)
    print(" 🚗 AI NUMBER PLATE RECOGNITION & SMART GATE SYSTEM")
    print("="*60)
    print(" Server running on http://127.0.0.1:5000")
    print(" Press Ctrl+C to stop.")
    print("="*60 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
