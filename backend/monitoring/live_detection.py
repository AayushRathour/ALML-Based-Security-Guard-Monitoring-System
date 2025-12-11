# backend/monitoring/live_detection.py - COMPLETE WORKING DETECTION SYSTEM
import cv2
import numpy as np
import threading
import time
from pathlib import Path
from ultralytics import YOLO
import face_recognition
from datetime import datetime
from django.utils import timezone

# Global state
_camera = None
_model = None
_running = False
_thread = None
_latest_frame = None
_frame_lock = threading.Lock()
_authorized_faces = {}
_detection_count = 0
_current_detections = []  # Store current frame detections

# Paths
ML_DIR = Path(__file__).resolve().parent.parent.parent / 'ml'
MODEL_PATH = ML_DIR / 'model_weights' / 'yolov8n.pt'
ALERTS_DIR = ML_DIR / 'alerts'
ALERTS_DIR.mkdir(exist_ok=True)


def initialize_camera():
    """Initialize webcam - MUST WORK"""
    global _camera
    try:
        print("📹 Opening camera...")
        _camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)  # Use DirectShow on Windows
        _camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        _camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        _camera.set(cv2.CAP_PROP_FPS, 30)
        
        if not _camera.isOpened():
            print("✗ Camera failed to open!")
            return False
        
        # Test read
        ret, frame = _camera.read()
        if not ret or frame is None:
            print("✗ Cannot read from camera!")
            return False
        
        print(f"✓ Camera opened: {frame.shape}")
        return True
    except Exception as e:
        print(f"✗ Camera error: {e}")
        return False


def load_yolo_model():
    """Load YOLO model"""
    global _model
    try:
        print(f"📦 Loading YOLO model...")
        _model = YOLO(str(MODEL_PATH))
        print("✓ YOLO loaded")
        return True
    except Exception as e:
        print(f"✗ YOLO error: {e}")
        return False


def load_authorized_faces():
    """Load authorized persons from database"""
    global _authorized_faces
    try:
        from monitoring.models import AuthorizedPerson, AuthorizedPersonPhoto
        
        _authorized_faces.clear()
        persons = AuthorizedPerson.objects.filter(is_active=True)
        print(f"📋 Loading {persons.count()} authorized persons...")
        
        for person in persons:
            encodings = []
            
            # Primary photo
            if person.photo and hasattr(person.photo, 'path'):
                try:
                    img = face_recognition.load_image_file(person.photo.path)
                    enc_list = face_recognition.face_encodings(img)
                    if enc_list:
                        encodings.append(enc_list[0])
                        print(f"  ✓ Primary: {person.name}")
                except Exception as e:
                    print(f"  ✗ Primary error: {e}")
            
            # Additional photos
            for photo in AuthorizedPersonPhoto.objects.filter(person=person):
                if photo.photo and hasattr(photo.photo, 'path'):
                    try:
                        img = face_recognition.load_image_file(photo.photo.path)
                        enc_list = face_recognition.face_encodings(img)
                        if enc_list:
                            encodings.append(enc_list[0])
                    except:
                        pass
            
            if encodings:
                _authorized_faces[person.id] = {
                    "name": person.name,
                    "encodings": encodings
                }
                print(f"  ✓ {person.name}: {len(encodings)} photos")
        
        print(f"✓ Loaded {len(_authorized_faces)} persons")
        return True
    except Exception as e:
        print(f"✗ Face loading error: {e}")
        return False


def check_face_authorization(frame, bbox):
    """Check if person is authorized"""
    try:
        x1, y1, x2, y2 = map(int, bbox)
        face_img = frame[y1:y2, x1:x2]
        
        if face_img.size == 0:
            return None, False
        
        rgb_face = cv2.cvtColor(face_img, cv2.COLOR_BGR2RGB)
        face_encodings = face_recognition.face_encodings(rgb_face)
        
        if not face_encodings:
            return None, False
        
        face_encoding = face_encodings[0]
        
        # Compare with authorized faces
        for person_id, person_data in _authorized_faces.items():
            for known_encoding in person_data["encodings"]:
                matches = face_recognition.compare_faces([known_encoding], face_encoding, tolerance=0.6)
                if matches[0]:
                    return person_data["name"], True
        
        return None, False
    except Exception as e:
        print(f"Face check error: {e}")
        return None, False


def create_alert(frame):
    """Create alert for unauthorized detection"""
    try:
        from monitoring.models import Alert
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        snapshot_path = ALERTS_DIR / f'alert_{timestamp}.jpg'
        cv2.imwrite(str(snapshot_path), frame)
        
        Alert.objects.create(
            alert_type='unauthorized_person',
            timestamp=timezone.now(),
            snapshot_path=str(snapshot_path.relative_to(ML_DIR.parent)),
            confidence=0.85
        )
        print(f"⚠️ ALERT created: {timestamp}")
    except Exception as e:
        print(f"Alert error: {e}")


def detection_loop():
    """Main detection loop - runs in background thread"""
    global _running, _latest_frame, _detection_count, _current_detections
    
    print("\n" + "="*60)
    print("🎯 DETECTION LOOP STARTING")
    print("="*60)
    
    # Initialize everything
    if not load_yolo_model():
        _running = False
        return
    
    if not load_authorized_faces():
        _running = False
        return
    
    if not initialize_camera():
        _running = False
        return
    
    print("\n🟢 DETECTION ACTIVE - Camera feed is NOW LIVE and updating\n")
    
    _detection_count = 0
    frame_count = 0
    last_alert_time = 0
    fps_start_time = time.time()
    fps_frame_count = 0
    current_fps = 0
    
    while _running:
        try:
            ret, frame = _camera.read()
            if not ret or frame is None:
                print("✗ Frame read failed")
                time.sleep(0.1)
                continue
            
            frame_count += 1
            fps_frame_count += 1
            annotated = frame.copy()
            
            # Calculate FPS
            if time.time() - fps_start_time >= 1.0:
                current_fps = fps_frame_count
                fps_frame_count = 0
                fps_start_time = time.time()
            
            # Detect faces in the frame first
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            face_locations = face_recognition.face_locations(rgb_frame)
            face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
            
            _current_detections.clear()
            
            # Check each detected face
            for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
                name = None
                is_authorized = False
                
                # Compare with authorized faces
                for person_id, person_data in _authorized_faces.items():
                    for known_encoding in person_data["encodings"]:
                        matches = face_recognition.compare_faces([known_encoding], face_encoding, tolerance=0.5)
                        if matches[0]:
                            name = person_data["name"]
                            is_authorized = True
                            break
                    if is_authorized:
                        break
                
                if not is_authorized:
                    name = "UNAUTHORIZED"
                
                _detection_count += 1
                
                # Draw face bounding box
                color = (0, 255, 0) if is_authorized else (0, 0, 255)
                cv2.rectangle(annotated, (left, top), (right, bottom), color, 3)
                
                # Draw name label with background
                label = name
                label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_DUPLEX, 0.8, 2)[0]
                label_y = top - 10 if top - 10 > 10 else top + label_size[1] + 10
                
                # Background rectangle for text
                cv2.rectangle(annotated, 
                             (left, label_y - label_size[1] - 10), 
                             (left + label_size[0] + 10, label_y + 5), 
                             color, -1)
                
                # White text
                cv2.putText(annotated, label, (left + 5, label_y), 
                           cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 2)
                
                # Store detection
                _current_detections.append({
                    'name': name,
                    'authorized': is_authorized,
                    'bbox': (left, top, right, bottom)
                })
                
                # Create alert if unauthorized
                if not is_authorized and (time.time() - last_alert_time) > 5:
                    create_alert(annotated)
                    last_alert_time = time.time()
            
            # Add clean status overlay at bottom
            overlay_height = 80
            overlay = annotated.copy()
            cv2.rectangle(overlay, (0, annotated.shape[0] - overlay_height), 
                         (annotated.shape[1], annotated.shape[0]), 
                         (0, 0, 0), -1)
            cv2.addWeighted(overlay, 0.7, annotated, 0.3, 0, annotated)
            
            # Status text
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            y_pos = annotated.shape[0] - 50
            cv2.putText(annotated, f"🕐 {timestamp}", (10, y_pos), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            cv2.putText(annotated, f"FPS: {current_fps}", (10, y_pos + 25), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            
            cv2.putText(annotated, f"Faces: {len(face_locations)}", (150, y_pos + 25), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
            
            cv2.putText(annotated, f"Total: {_detection_count}", (280, y_pos + 25), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)
            
            # Show authorized persons list on the right
            if _current_detections:
                info_x = annotated.shape[1] - 250
                info_y = 30
                for detection in _current_detections[:5]:  # Max 5
                    status = "✓ AUTHORIZED" if detection['authorized'] else "✗ UNAUTHORIZED"
                    color = (0, 255, 0) if detection['authorized'] else (0, 0, 255)
                    
                    cv2.putText(annotated, f"{detection['name']}", 
                               (info_x, info_y), cv2.FONT_HERSHEY_SIMPLEX, 
                               0.5, color, 2)
                    cv2.putText(annotated, status, 
                               (info_x, info_y + 20), cv2.FONT_HERSHEY_SIMPLEX, 
                               0.4, color, 1)
                    info_y += 50
            
            # Update latest frame for streaming
            with _frame_lock:
                _latest_frame = annotated.copy()
            
            # Print status every 5 seconds
            if frame_count % 150 == 0:
                print(f"📊 Frame {frame_count} | FPS: {current_fps} | Faces: {len(face_locations)} | Total: {_detection_count}")
            
            time.sleep(0.001)  # Minimal delay for max FPS
            
        except Exception as e:
            print(f"Loop error: {e}")
            import traceback
            traceback.print_exc()
            time.sleep(0.1)
    
    # Cleanup
    print("\n🛑 Stopping detection...")
    if _camera:
        _camera.release()
    print("✓ Detection stopped\n")


def start_detection():
    """Start detection thread"""
    global _running, _thread, _detection_count
    
    if _running:
        print("⚠️ Detection already running")
        return False
    
    print("🚀 Starting detection...")
    _running = True
    _detection_count = 0
    _thread = threading.Thread(target=detection_loop, daemon=True)
    _thread.start()
    
    # Wait for initialization
    time.sleep(2)
    
    return _running


def stop_detection():
    """Stop detection thread"""
    global _running, _camera, _thread
    
    print("🛑 Stopping detection...")
    _running = False
    
    if _thread:
        _thread.join(timeout=3)
    
    if _camera:
        _camera.release()
        _camera = None
    
    print("✓ Stopped")


def get_frame_bytes():
    """Get current frame as JPEG bytes for MJPEG streaming"""
    global _latest_frame
    
    with _frame_lock:
        if _latest_frame is None:
            # Return black frame with "Initializing..." text
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(frame, "Initializing camera...", (150, 240), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            ret, buffer = cv2.imencode('.jpg', frame)
            return buffer.tobytes()
        
        ret, buffer = cv2.imencode('.jpg', _latest_frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        if not ret:
            return None
        return buffer.tobytes()


def generate_frames():
    """Generator function for MJPEG streaming"""
    while True:
        frame_bytes = get_frame_bytes()
        if frame_bytes:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        time.sleep(0.033)  # ~30 FPS


def is_running():
    """Check if detection is running"""
    return _running


def get_detection_count():
    """Get total detection count"""
    return _detection_count
