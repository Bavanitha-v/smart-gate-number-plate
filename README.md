# 🚗 AI Number Plate Recognition & Smart Gate Control System

A beginner-friendly, complete Python project for **Automatic Number Plate Recognition (ANPR)** and **Smart Gate Access Control**. 

The system captures live video streams (webcam or video file), detects vehicles using **YOLO**, extracts license plate numbers using **EasyOCR** and **OpenCV**, validates the plate against an **SQLite** database, and automatically controls gate access:
- ✅ **Registered Vehicle** &rarr; Displays **`GATE OPEN`** (Glowing Emerald Green)
- ❌ **Unregistered Vehicle** &rarr; Displays **`GATE CLOSED`** and **`UNKNOWN VEHICLE`** (Crimson Red)

---

## 🌟 Key Features

1. **Live Camera & Video Streaming**: Real-time MJPEG web video feed with security HUD overlays.
2. **AI Detection Engine**: Combines **YOLOv8** (for vehicle localization), **OpenCV** (for contrast enhancement & contour detection), and **EasyOCR** (for character recognition).
3. **SQLite Access Control**: Instant authorization lookup with automatic access logging (timestamp, plate, owner, gate action).
4. **Interactive Dashboard**: Sleek dark-mode web interface with metrics cards, manual gate controls, live logs table, and vehicle registration manager.
5. **Zero-Setup Beginner Mode**: Includes a synthetic test video generator script (`generate_sample_video.py`) so you can test license plate scanning instantly—even without a physical webcam!

---

## 📁 Project Structure

```text
ai smart gate/
├── app.py                 # Flask web server & streaming REST API endpoints
├── anpr.py                # ANPR engine (OpenCV + YOLO + EasyOCR pipeline)
├── database.py            # SQLite database initialization & CRUD helper functions
├── seed_db.py             # Script to pre-populate database with sample vehicles & logs
├── generate_sample_video.py # OpenCV script to create a test video with cars & plates
├── requirements.txt       # All required Python packages
├── README.md              # Documentation & setup guide
├── smart_gate.db          # Auto-generated SQLite database
├── sample_traffic.mp4     # Auto-generated test video stream
├── static/
│   ├── css/
│   │   └── style.css      # Dark glassmorphism dashboard styling
│   └── js/
│       └── main.js        # Dashboard real-time polling & UI interactions
└── templates/
    └── index.html         # Web dashboard HTML template
```

---

## 🚀 Quick Start Guide (Windows / VS Code)

### Step 1: Open Terminal in VS Code
Open VS Code, press `Ctrl + ~` to open the terminal, and navigate to the project directory:
```powershell
cd "c:\Users\bavan\OneDrive\Desktop\ai smart gate"
```

### Step 2: Create & Activate Virtual Environment (Recommended)
```powershell
python -m venv venv
.\venv\Scripts\activate
```

### Step 3: Install Required Dependencies
```powershell
pip install -r requirements.txt
```

### Step 4: Initialize & Seed Database
Pre-fill the SQLite database with sample registered vehicle numbers (e.g. `KA01AB1234`, `MH12DE5678`, `DL03XY9999`):
```powershell
python seed_db.py
```

### Step 5: Generate Sample Test Video (Optional but recommended!)
If you don't have a webcam connected or want to test immediately, generate the test video:
```powershell
python generate_sample_video.py
```

### Step 6: Launch the Smart Gate Web App!
```powershell
python app.py
```

Open your web browser (Chrome, Edge, or Firefox) and go to:
👉 **`http://127.0.0.1:5000`**

---

## 🖥️ Using the Dashboard

1. **Live Camera & Video Feed**:
   - By default, the app streams `sample_traffic.mp4`.
   - Click **`Live Camera`** in the top header to switch to your physical computer webcam.
2. **ANPR Recognition Metrics**:
   - Shows the last detected plate number, owner name, OCR confidence, and gate status banner.
3. **Register New Vehicles**:
   - Type a plate number (e.g., `TN07CZ4321`) and Owner Name into the **Register New Vehicle** form on the dashboard to immediately authorize access!
4. **Manual Gate Override**:
   - Use the **`OPEN GATE`** and **`CLOSE GATE`** buttons to manually control the gate.
5. **Real-time Access Logs**:
   - Every detected plate attempt is recorded with a timestamp in the SQLite database and updated on the dashboard table.

---

## 🛠️ Troubleshooting for Beginners

- **Missing C++ Build Tools for EasyOCR / PyTorch**: EasyOCR will download its pre-trained OCR weights on the first run automatically.
- **Webcam Access Error**: Ensure no other application (Zoom, Teams, Skype) is using your camera, or switch back to **`Test Video`** mode.
- **Port 5000 Already in Use**: Change `port=5000` to `port=5001` at the bottom of `app.py`.

---

## 📜 License
Educational and open-source project. Built for AI Smart Gate & Computer Vision demonstrations.
