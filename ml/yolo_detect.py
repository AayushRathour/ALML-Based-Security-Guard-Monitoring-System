# ml/yolo_detect.py - YOLO detection with face recognition
from ultralytics import YOLO
import cv2
import face_recognition
import numpy as np
import threading
import time
import os
import sys
import json
from pathlib import Path
from datetime import datetime

# Add Django settings to path
BACKEND_DIR = Path(__file__).resolve().parent.parent / 'backend'
sys.path.insert(0, str(BACKEND_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'guardsys.settings')
import django
django.setup()

from monitoring.models import Alert, AuthorizedPerson

# Global state
model = None
cap = None
running = False
latest_frame = None
frame_lock = threading.Lock()
detection_stats = {"total_detections": 0, "last_detection_time": None}
authorized_faces = {}  # {person_id: {"name": str, "encoding": np.array}}

# Paths
BASE_DIR = Path(__file__).resolve().parent
LATEST_FRAME_PATH = BASE_DIR / "latest.jpg"
ALERTS_DIR = BASE_DIR / "alerts"
MODEL_PATH = BASE_DIR / "model_weights" / "yolov8n.pt"
STOP_FILE = BASE_DIR / "STOP"

# Ensure directories exist
ALERTS_DIR.mkdir(exist_ok=True)

def load_authorized_faces():
    """Load authorized persons from database with face encodings (including additional photos)"""
    global authorized_faces
    
    try:
        from monitoring.models import AuthorizedPersonPhoto
        
        authorized_persons = AuthorizedPerson.objects.filter(is_active=True)
        print(f"Loading {authorized_persons.count()} authorized persons...")
        
        for person in authorized_persons:
            encodings_list = []
            
            # Load primary photo encoding
            if person.face_encoding:
                try:
                    encoding = np.array(json.loads(person.face_encoding))
                    encodings_list.append(encoding)
                    print(f"✓ Loaded primary photo from DB: {person.name}")
                except Exception as e:
                    print(f"⚠ Encoding parse error for {person.name}: {e}")
            elif person.photo and os.path.exists(person.photo.path):
                try:
                    image = face_recognition.load_image_file(person.photo.path)
                    encodings = face_recognition.face_encodings(image)
                    
                    if encodings:
                        encodings_list.append(encodings[0])
                        # Save encoding to database
                        person.face_encoding = json.dumps(encodings[0].tolist())
                        person.save()
                        print(f"✓ Loaded primary photo from image: {person.name}")
                except Exception as e:
                    print(f"✗ Error loading primary photo for {person.name}: {e}")
            
            # Load additional photos
            additional_photos = AuthorizedPersonPhoto.objects.filter(person=person)
            print(f"  Found {additional_photos.count()} additional photos for {person.name}")
            
            for add_photo in additional_photos:
                if add_photo.face_encoding:
                    try:
                        encoding = np.array(json.loads(add_photo.face_encoding))
                        encodings_list.append(encoding)
                    except Exception as e:
                        print(f"  ⚠ Additional photo encoding parse error: {e}")
                elif add_photo.photo and os.path.exists(add_photo.photo.path):
                    try:
                        image = face_recognition.load_image_file(add_photo.photo.path)
                        encodings = face_recognition.face_encodings(image)
                        
                        if encodings:
                            encodings_list.append(encodings[0])
                            # Save encoding to database
                            add_photo.face_encoding = json.dumps(encodings[0].tolist())
                            add_photo.save()
                    except Exception as e:
                        print(f"  ✗ Error loading additional photo: {e}")
            
            # Store all encodings for this person
            if encodings_list:
                authorized_faces[person.id] = {
                    "name": person.name,
                    "employee_id": person.employee_id,
                    "encodings": encodings_list  # Now storing multiple encodings per person
                }
                print(f"✓ Total {len(encodings_list)} photo(s) loaded for {person.name}")
            else:
                print(f"⚠ No valid face encodings for {person.name}")
        
        print(f"✓ Total authorized faces loaded: {len(authorized_faces)}")
        return True
        
    except Exception as e:
        print(f"✗ Error loading authorized faces: {e}")
        import traceback
        traceback.print_exc()
        return False

def initialize_detection(confidence_threshold=0.4):
    """Initialize YOLO model and webcam"""
    global model, cap
    
    try:
        # Load YOLO model (will auto-download if not present)
        model = YOLO(str(MODEL_PATH) if MODEL_PATH.exists() else "yolov8n.pt")
        print(f"✓ YOLO model loaded: {model.model_name}")
        
        # Initialize webcam
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            raise Exception("Cannot open webcam")
        
        # Set camera properties for better performance
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 30)
        
        print("✓ Webcam initialized")
        return True
    except Exception as e:
        print(f"✗ Initialization error: {e}")
        return False

def detect_loop(confidence_threshold=0.4):
    """Main detection loop with YOLO person detection + face recognition"""
    global running, latest_frame, detection_stats
    
    print("🔍 Detection loop started...")
    frame_count = 0
    last_alert_time = {}  # Track alerts per person to avoid spam
    
    while running:
        # Check for stop signal
        if STOP_FILE.exists():
            print("⏹ Stop signal detected")
            STOP_FILE.unlink()
            break
        
        ret, frame = cap.read()
        if not ret:
            print("⚠ Failed to read frame")
            time.sleep(0.1)
            continue
        
        frame_count += 1
        
        # Run YOLO detection to find persons
        try:
            results = model.predict(
                source=frame,
                stream=False,
                imgsz=640,
                conf=confidence_threshold,
                verbose=False,
                classes=[0]  # Only detect persons (class 0)
            )
            
            annotated = frame.copy()
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Find all face locations in current frame
            face_locations = face_recognition.face_locations(rgb_frame)
            face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
            
            # Process YOLO detections
            for r in results:
                boxes = r.boxes.xyxy.cpu().numpy()
                confs = r.boxes.conf.cpu().numpy()
                clsids = r.boxes.cls.cpu().numpy()
                
                for (x1, y1, x2, y2), conf, clsid in zip(boxes, confs, clsids):
                    class_name = model.names[int(clsid)]
                    
                    if class_name == 'person' and conf > confidence_threshold:
                        detection_stats["total_detections"] += 1
                        detection_stats["last_detection_time"] = time.time()
                        
                        # Draw person bounding box
                        cv2.rectangle(annotated, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
                        
                        # Check if this person is authorized using face recognition
                        person_authorized = False
                        person_name = "Unknown Person"
                        
                        for face_location, face_encoding in zip(face_locations, face_encodings):
                            top, right, bottom, left = face_location
                            
                            # Check if face is within person bounding box
                            if (left >= x1 and right <= x2 and top >= y1 and bottom <= y2):
                                # Compare with authorized faces (now supports multiple photos per person)
                                if authorized_faces:
                                    matches = []
                                    for person_id, person_data in authorized_faces.items():
                                        # Check against all encodings for this person
                                        for encoding in person_data["encodings"]:
                                            match = face_recognition.compare_faces(
                                                [encoding], 
                                                face_encoding,
                                                tolerance=0.6
                                            )[0]
                                            if match:
                                                matches.append((person_id, person_data))
                                                break  # Found match, no need to check other photos
                                    
                                    if matches:
                                        # Authorized person found
                                        person_authorized = True
                                        person_id, person_data = matches[0]
                                        person_name = f"{person_data['name']} ({person_data['employee_id'] or 'No ID'})"
                                        
                                        # Draw green box around face
                                        cv2.rectangle(annotated, (left, top), (right, bottom), (0, 255, 0), 2)
                                        cv2.putText(annotated, person_name, (left, top - 10),
                                                  cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                                    else:
                                        # Unauthorized person detected
                                        person_authorized = False
                                        
                                        # Draw red box around face
                                        cv2.rectangle(annotated, (left, top), (right, bottom), (0, 0, 255), 3)
                                        cv2.putText(annotated, "UNAUTHORIZED!", (left, top - 10),
                                                  cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                                        
                                        # Create alert (with cooldown)
                                        current_time = time.time()
                                        alert_key = f"unknown_{left}_{top}"
                                        
                                        if alert_key not in last_alert_time or (current_time - last_alert_time[alert_key]) > 30:
                                            save_alert_to_db(annotated, "Unauthorized Person Detected", conf)
                                            last_alert_time[alert_key] = current_time
                                            print(f"🚨 ALERT: Unauthorized person detected!")
                        
            # Add status overlay with authorized faces count
            status_text = f"Monitoring | Authorized: {len(authorized_faces)} | Detections: {detection_stats['total_detections']}"
            cv2.putText(annotated, status_text, (10, 30),
                      cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            # Thread-safe frame update
            with frame_lock:
                latest_frame = annotated.copy()
                cv2.imwrite(str(LATEST_FRAME_PATH), annotated)
            
        except Exception as e:
            print(f"⚠ Detection error: {e}")
        
        time.sleep(0.03)  # ~30 FPS
    
    print("🛑 Detection loop stopped")

def save_alert_to_db(frame, label, confidence):
    """Save alert to Django database"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        alert_path = ALERTS_DIR / f"alert_{timestamp}.jpg"
        cv2.imwrite(str(alert_path), frame)
        
        Alert.objects.create(
            label=label,
            confidence=float(confidence),
            image_path=str(alert_path),
            resolved=False
        )
        print(f"✓ Alert saved: {label}")
    except Exception as e:
        print(f"✗ Error saving alert: {e}")

def start_detection(confidence_threshold=0.4):
    """Start detection in background thread"""
    global running
    
    if running:
        return {"status": "already_running"}
    
    if not initialize_detection(confidence_threshold):
        return {"status": "error", "message": "Failed to initialize"}
    
    # Load authorized faces
    load_authorized_faces()
    
    running = True
    detection_stats["total_detections"] = 0
    detection_stats["last_detection_time"] = None
    
    thread = threading.Thread(target=detect_loop, args=(confidence_threshold,), daemon=True)
    thread.start()
    
    return {"status": "started"}

def stop_detection():
    """Stop detection gracefully"""
    global running, cap
    
    if not running:
        return {"status": "not_running"}
    
    running = False
    
    # Create stop file as signal
    STOP_FILE.touch()
    
    # Wait a bit for thread to stop
    time.sleep(0.5)
    
    # Release camera
    if cap:
        cap.release()
    
    return {"status": "stopped"}

def get_latest_frame():
    """Get latest processed frame (thread-safe)"""
    with frame_lock:
        return latest_frame.copy() if latest_frame is not None else None

def get_stats():
    """Get detection statistics"""
    return {
        "running": running,
        "total_detections": detection_stats["total_detections"],
        "last_detection_time": detection_stats["last_detection_time"]
    }

# If run directly (for testing or from subprocess)
if __name__ == "__main__":
    print("=" * 70)
    print("🚀 YOLO + Face Recognition Detection System Starting...")
    print("=" * 70)
    
    result = start_detection(confidence_threshold=0.4)
    print(f"✓ Detection initialized: {result}")
    
    if result.get('status') == 'started':
        print("\n📹 Camera active and detecting...")
        print("📊 Real-time detection running...")
        print("⏹  Create 'STOP' file or press Ctrl+C to stop\n")
        
        try:
            while running:
                time.sleep(2)
                stats = get_stats()
                if stats['total_detections'] > 0:
                    print(f"📊 Detections: {stats['total_detections']} | "
                          f"Authorized faces: {len(authorized_faces)} | "
                          f"Running: {running}")
        except KeyboardInterrupt:
            print("\n\n⏹ Stopping detection...")
            stop_detection()
            print("✓ Detection stopped cleanly")
    else:
        print("✗ Failed to start detection")
        sys.exit(1)
