# pyrefly: ignore [missing-import]
import cv2
# pyrefly: ignore [missing-import]
import easyocr
import re
import time
from database import is_plate_registered, log_access

class ANPREngine:
    def __init__(self):
        print("Initializing EasyOCR Engine (CPU mode)...")
        # Initialize EasyOCR reader for English characters
        self.reader = easyocr.Reader(['en'], gpu=False)
        
        # Try loading YOLOv8 model if available
        self.yolo_model = None
        try:
            from ultralytics import YOLO
            print("Loading YOLO model for vehicle/plate detection...")
            self.yolo_model = YOLO('yolov8n.pt')
            print("YOLO model loaded successfully.")
        except Exception as e:
            print(f"YOLO initialization notice: {e}. Falling back to OpenCV heuristic detector.")

        # Real-time ANPR state
        self.last_detected_plate = "Scanning..."
        self.vehicle_status = "Scanning"
        self.gate_status = "GATE CLOSED"
        self.owner_name = "-"
        self.confidence = 0.0
        self.last_log_time = 0
        self.log_cooldown = 5.0  # seconds between duplicate logs

    def clean_plate_text(self, text):
        """Extract valid alphanumeric license plate characters."""
        if not text:
            return ""
        # Remove non-alphanumeric characters and convert to uppercase
        clean = re.sub(r'[^A-Za-z0-9]', '', str(text)).upper()
        # Common OCR fixes (e.g., 'O' -> '0', 'I' -> '1' when appropriate)
        return clean

    def is_valid_plate_format(self, text):
        """Check if string matches reasonable Indian/Standard plate length (4-11 chars)."""
        return 4 <= len(text) <= 11

    def detect_plate_region_opencv(self, frame):
        """Fallback OpenCV contour detection for white rectangular license plates."""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        edged = cv2.Canny(blur, 50, 200)

        contours, _ = cv2.findContours(edged.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        contours = sorted(contours, key=cv2.contourArea, reverse=True)[:15]

        plate_box = None
        for c in contours:
            peri = cv2.arcLength(c, True)
            approx = cv2.approxPolyDP(c, 0.018 * peri, True)
            if len(approx) == 4:
                x, y, w, h = cv2.boundingRect(approx)
                aspect_ratio = w / float(h)
                if 2.0 <= aspect_ratio <= 5.5 and w > 60 and h > 20:
                    plate_box = (x, y, w, h)
                    break
        return plate_box

    def process_frame(self, frame):
        """
        Process a single video frame:
        1. Locate plate box (YOLO / OpenCV fallback)
        2. Read plate text via EasyOCR
        3. Check database registration
        4. Draw status overlays & return annotated frame
        """
        if frame is None:
            return frame

        h, w, _ = frame.shape
        plate_box = None

        # 1. Try YOLO object detection first if loaded
        if self.yolo_model is not None:
            try:
                results = self.yolo_model(frame, verbose=False, conf=0.3)
                for r in results:
                    for box in r.boxes:
                        cls_id = int(box.cls[0])
                        # Detect vehicles (car=2, motorcycle=3, bus=5, truck=7 in COCO dataset)
                        if cls_id in [2, 3, 5, 7]:
                            bx, by, bw, bh = map(int, box.xywh[0])
                            # Define expected lower region of vehicle for plate detection
                            px = max(0, bx - bw // 2)
                            py = max(0, by)
                            pw = min(w - px, bw)
                            ph = min(h - py, bh // 2)
                            if pw > 40 and ph > 20:
                                plate_box = (px, py, pw, ph)
                                # Draw subtle vehicle boundary box
                                cv2.rectangle(frame, (px, py - bh//2), (px + pw, py + ph), (255, 165, 0), 2)
                                break
            except Exception:
                pass

        # 2. Fallback to OpenCV Contour Detection if YOLO didn't lock plate
        if plate_box is None:
            plate_box = self.detect_plate_region_opencv(frame)

        # 3. Perform OCR on detected plate box area
        if plate_box is not None:
            px, py, pw, ph = plate_box
            # Extract plate crop with margin
            margin = 5
            crop_y1 = max(0, py - margin)
            crop_y2 = min(h, py + ph + margin)
            crop_x1 = max(0, px - margin)
            crop_x2 = min(w, px + pw + margin)
            plate_crop = frame[crop_y1:crop_y2, crop_x1:crop_x2]

            if plate_crop.size > 0:
                # Preprocess cropped image for higher OCR accuracy
                gray_crop = cv2.cvtColor(plate_crop, cv2.COLOR_BGR2GRAY)
                contrast_crop = cv2.threshold(gray_crop, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

                # Run EasyOCR
                try:
                    ocr_results = self.reader.readtext(contrast_crop)
                    best_text = ""
                    best_conf = 0.0

                    for bbox, text, prob in ocr_results:
                        cleaned = self.clean_plate_text(text)
                        if self.is_valid_plate_format(cleaned) and prob > best_conf:
                            best_text = cleaned
                            best_conf = prob

                    if best_text:
                        self.last_detected_plate = best_text
                        self.confidence = float(best_conf)
                        
                        # Check database for registration status
                        is_reg, owner = is_plate_registered(best_text)
                        self.owner_name = owner
                        
                        if is_reg:
                            self.gate_status = "GATE OPEN"
                            self.vehicle_status = "REGISTERED"
                        else:
                            self.gate_status = "GATE CLOSED"
                            self.vehicle_status = "UNKNOWN VEHICLE"

                        # Log access attempt (with cooldown to prevent DB flooding)
                        curr_time = time.time()
                        if curr_time - self.last_log_time > self.log_cooldown:
                            log_access(
                                plate_number=self.last_detected_plate,
                                access_status=self.gate_status,
                                vehicle_status=self.vehicle_status,
                                owner_name=self.owner_name
                            )
                            self.last_log_time = curr_time

                        # Draw highlight bounding box around detected plate
                        color = (0, 255, 0) if is_reg else (0, 0, 255)
                        cv2.rectangle(frame, (px, py), (px + pw, py + ph), color, 3)
                        cv2.putText(frame, f"{best_text}", (px, py - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
                except Exception as e:
                    pass

        # 4. Draw Security Gate Top Status Banner
        banner_bg = (20, 30, 40)
        cv2.rectangle(frame, (0, 0), (w, 75), banner_bg, -1)
        
        # Gate status color
        if self.gate_status == "GATE OPEN":
            gate_color = (0, 255, 128)  # Glowing Green
        else:
            gate_color = (60, 60, 255)   # Glowing Crimson Red

        # Gate status text
        cv2.putText(frame, f"STATUS: {self.gate_status}", (20, 48),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.1, gate_color, 3)

        # Vehicle status sub-text
        sub_text = f"PLATE: {self.last_detected_plate} | VEHICLE: {self.vehicle_status}"
        cv2.putText(frame, sub_text, (w - 560, 45),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, (220, 220, 220), 2)

        return frame

    def get_status_dict(self):
        """Return current status as JSON-serializable dictionary."""
        return {
            "detected_plate": self.last_detected_plate,
            "vehicle_status": self.vehicle_status,
            "gate_status": self.gate_status,
            "owner_name": self.owner_name,
            "confidence": round(self.confidence * 100, 1)
        }
