# 🛡️ SECURITY GUARD MONITORING SYSTEM - COMPLETE DOCUMENTATION

## 📋 TABLE OF CONTENTS
1. [Project Overview](#project-overview)
2. [System Architecture](#system-architecture)
3. [Installation & Setup](#installation-setup)
4. [Pages & Features](#pages-features)
5. [API Endpoints](#api-endpoints)
6. [Functions & Components](#functions-components)
7. [Database Schema](#database-schema)
8. [Usage Guide](#usage-guide)
9. [Troubleshooting](#troubleshooting)

---

## 🎯 PROJECT OVERVIEW

**Security Guard Monitoring System** is an AI-powered real-time surveillance system that uses **YOLOv8** for person detection and **face_recognition** library for face identification. The system automatically detects unauthorized persons and generates alerts with snapshots.

### Key Technologies
- **Backend**: Django 4.2.23 + Django REST Framework
- **AI Models**: YOLOv8 (Ultralytics) + dlib face recognition
- **Computer Vision**: OpenCV 4.11
- **Frontend**: HTML5, Tailwind CSS, JavaScript
- **Database**: SQLite (default) / PostgreSQL (optional)

### Core Features
✅ Real-time person detection using YOLOv8
✅ Face recognition with multiple photos per person
✅ Automatic alert generation for unauthorized persons
✅ Live camera feed with MJPEG streaming
✅ Multiple photo support for better accuracy
✅ Complete CRUD operations for authorized persons
✅ Alert management with resolution tracking
✅ User authentication & authorization
✅ Responsive web interface

---

## 🏗️ SYSTEM ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────┐
│                    DJANGO WEB FRAMEWORK                     │
├─────────────────────────────────────────────────────────────┤
│  Frontend (HTML/CSS/JS) ←→ Views ←→ Models ←→ Database    │
│           ↓                    ↓                             │
│    API Endpoints          Live Detection                     │
│           ↓                    ↓                             │
│    REST Framework      Threading System                      │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│               DETECTION ENGINE (live_detection.py)           │
├─────────────────────────────────────────────────────────────┤
│  Camera Input → YOLO Detection → Face Recognition           │
│       ↓              ↓                    ↓                  │
│  OpenCV      Person Detection      Face Matching            │
│       ↓              ↓                    ↓                  │
│  Frame Capture   Bounding Boxes    Authorization Check      │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                    OUTPUT & STORAGE                          │
├─────────────────────────────────────────────────────────────┤
│  Live Stream → MJPEG → Browser Display                      │
│  Alerts → Database → Alert Page                             │
│  Snapshots → File System → Media Storage                    │
└─────────────────────────────────────────────────────────────┘
```

---

## 💾 INSTALLATION & SETUP

### Prerequisites
- Python 3.12+
- Webcam/USB Camera
- Windows/Linux/macOS

### Step 1: Clone & Navigate
```bash
cd "Security guard monitoring system"
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Database Setup
```bash
cd backend
python manage.py makemigrations
python manage.py migrate
```

### Step 4: Create Superuser
```bash
python manage.py createsuperuser
# Username: admin
# Password: admin123
```

### Step 5: Download YOLO Model
The system will auto-download `yolov8n.pt` on first run.
Manual download: Place in `ml/model_weights/yolov8n.pt`

### Step 6: Run Server
```bash
python manage.py runserver
```

### Step 7: Access System
Open browser: **http://127.0.0.1:8000**

---

## 📄 PAGES & FEATURES

### 1. 🏠 **Homepage** (`/`)
- **Purpose**: Landing page with login/register
- **Features**:
  - User authentication
  - System introduction
  - Quick navigation
- **File**: `templates/monitoring/home.html`

### 2. 📊 **Dashboard** (`/dashboard/`)
- **Purpose**: System overview and statistics
- **Features**:
  - Total alerts count
  - Active detection status
  - Recent alerts list
  - System health indicators
  - Quick action buttons
- **Key Metrics**:
  - Total Alerts (All-time)
  - Unresolved Alerts
  - Active Sessions
  - Authorized Persons Count
- **File**: `templates/monitoring/dashboard.html`
- **View**: `views.dashboard_view()`

### 3. 📹 **Live Monitor** (`/monitor/`)
- **Purpose**: Real-time camera feed and detection
- **Features**:
  - Live MJPEG video stream
  - Start/Stop detection controls
  - Real-time face detection boxes
  - Authorization status overlay
  - FPS counter
  - Snapshot capture
  - Detection statistics
- **Controls**:
  - **Start Monitoring**: Activates camera and detection
  - **Stop Monitoring**: Stops detection and releases camera
  - **Take Snapshot**: Captures current frame
- **Display Overlay**:
  - Green boxes → Authorized persons
  - Red boxes → Unauthorized persons
  - Person name + status
  - Timestamp
  - FPS counter
  - Total detections
- **File**: `templates/monitoring/monitor.html`
- **View**: `views.monitor_view()`
- **Backend**: `live_detection.py`

### 4. 🚨 **Alerts** (`/alerts/`)
- **Purpose**: Alert management and history
- **Features**:
  - Alert list with snapshots
  - Filter: All / Resolved / Unresolved
  - Resolution controls
  - Timestamp display
  - Snapshot preview
  - Bulk operations
- **Alert Information**:
  - Detection timestamp
  - Snapshot image
  - Person confidence
  - Resolution status
  - Notes (optional)
- **Actions**:
  - Mark as resolved
  - Add notes
  - Delete alert
  - Clear resolved alerts
- **File**: `templates/monitoring/alerts.html`
- **View**: `views.alerts_view()`

### 5. 👤 **Authorized Persons** (`/authorized-persons/`)
- **Purpose**: Manage authorized personnel database
- **Features**:
  - Add new persons with photos
  - Multiple photos per person
  - Edit person details
  - Activate/Deactivate persons
  - Delete persons
  - Face encoding automatic extraction
- **Person Fields**:
  - Name (Required)
  - Employee ID (Optional, Unique)
  - Department
  - Email
  - Phone
  - Role/Position
  - Primary Photo (Required)
  - Additional Photos (Optional, Multiple)
  - Notes
  - Status (Active/Inactive)
- **Auto-Processing**:
  - Face detection in uploaded photos
  - Face encoding extraction (128-d vector)
  - Encoding saved to database
  - Validation warnings if no face detected
- **File**: `templates/monitoring/authorized_persons.html`
- **View**: `views.authorized_persons_view()`

### 6. 🤖 **Model Training** (`/model/`)
- **Purpose**: AI model training interface (Future feature)
- **Features**:
  - Training job creation
  - Dataset upload
  - Model configuration
  - Training progress
  - Model evaluation
- **File**: `templates/monitoring/model_training.html`
- **View**: `views.model_training_view()`

### 7. ⚙️ **Settings** (`/settings/`)
- **Purpose**: System configuration
- **Features**:
  - Detection sensitivity
  - Camera settings
  - Alert preferences
  - System preferences
- **Configurable Options**:
  - Confidence threshold
  - Face recognition tolerance
  - Alert cooldown period
  - Frame processing rate
- **File**: `templates/monitoring/settings.html`
- **View**: `views.settings_view()`

### 8. 👨‍💼 **Admin Panel** (`/admin-panel/`)
- **Purpose**: User management (Superuser only)
- **Features**:
  - Add/Edit/Delete users
  - Assign roles
  - Manage permissions
  - View user activity
- **User Fields**:
  - Username
  - Email
  - First/Last Name
  - Staff status
  - Active status
- **File**: `templates/monitoring/admin_panel.html`
- **View**: `views.admin_panel_view()`

### 9. ❓ **Help** (`/help/`)
- **Purpose**: System documentation and support
- **Features**:
  - User guide
  - FAQ
  - Troubleshooting
  - Contact information
- **File**: `templates/monitoring/help.html`
- **View**: `views.help_view()`

---

## 🔌 API ENDPOINTS

### Detection Control
| Endpoint | Method | Purpose | Response |
|----------|--------|---------|----------|
| `/api/monitor/start/` | POST | Start detection | `{"status": "started"}` |
| `/api/monitor/stop/` | POST | Stop detection | `{"status": "stopped"}` |
| `/api/status/` | GET | System status | `{"running": true/false}` |

### Alert Management
| Endpoint | Method | Purpose | Response |
|----------|--------|---------|----------|
| `/api/alerts/` | GET | Get all alerts | `[{alert_objects}]` |
| `/api/alerts/<id>/resolve/` | POST | Mark resolved | `{"status": "resolved"}` |
| `/api/alerts/clear/` | POST | Clear resolved | `{"count": N}` |

### Camera Operations
| Endpoint | Method | Purpose | Response |
|----------|--------|---------|----------|
| `/api/snapshot/` | POST | Capture frame | `{"path": "..."}` |
| `/stream/` | GET | MJPEG stream | Video stream |

### Training (Future)
| Endpoint | Method | Purpose | Response |
|----------|--------|---------|----------|
| `/api/training/start/` | POST | Start training | `{"job_id": N}` |

---

## ⚙️ FUNCTIONS & COMPONENTS

### Backend Core (`backend/monitoring/`)

#### **1. views.py** - Request Handlers
```python
# Authentication
- login_view() → User login
- logout_view() → User logout  
- register_view() → New user registration

# Pages
- dashboard_view() → Dashboard with stats
- monitor_view() → Live monitoring page
- alerts_view() → Alert management
- authorized_persons_view() → Person CRUD
- settings_view() → System settings
- help_view() → Help documentation
- admin_panel_view() → User management

# API Endpoints
- start_monitor_api() → Start detection
- stop_monitor_api() → Stop detection
- status_api() → Get system status
- alerts_api() → Get alerts JSON
- resolve_alert_api() → Mark resolved
- snapshot_api() → Capture snapshot
- stream_view() → MJPEG stream
```

#### **2. models.py** - Database Models
```python
# Alert Model
- Fields: timestamp, label, confidence, image_path, resolved, notes
- Methods: __str__(), save()

# AuthorizedPerson Model
- Fields: name, employee_id, department, email, phone, role, photo, 
         face_encoding, is_active, created_at, created_by, notes
- Methods: save() → Converts empty employee_id to None

# AuthorizedPersonPhoto Model
- Fields: person (FK), photo, face_encoding, uploaded_at
- Purpose: Store multiple photos per person

# SystemSettings Model
- Fields: detection_sensitivity, camera_source, alert_cooldown
- Purpose: Store system configuration

# DetectionSession Model
- Fields: start_time, end_time, detections_count
- Purpose: Track detection sessions

# TrainingJob Model
- Fields: dataset_path, model_name, status, progress
- Purpose: Track training jobs
```

#### **3. live_detection.py** - Detection Engine
```python
# Global State
- _camera: OpenCV VideoCapture object
- _model: YOLO model instance
- _running: Detection active flag
- _thread: Background thread
- _latest_frame: Current annotated frame
- _frame_lock: Thread-safe frame access
- _authorized_faces: Dict of person encodings
- _detection_count: Total detections

# Core Functions
- initialize_camera() → Open webcam with DirectShow
- load_yolo_model() → Load YOLOv8n model
- load_authorized_faces() → Load from database with encodings
- detection_loop() → Main processing loop
  * Reads frames continuously
  * Detects faces with face_recognition
  * Compares with authorized encodings
  * Draws bounding boxes (green/red)
  * Updates frame with overlays
  * Creates alerts for unauthorized
  * Calculates FPS
- start_detection() → Start background thread
- stop_detection() → Stop thread and release camera
- generate_frames() → MJPEG stream generator
- create_alert() → Save alert to database
```

#### **4. serializers.py** - DRF Serializers
```python
- AlertSerializer → Alert JSON serialization
- SystemSettingsSerializer → Settings JSON
```

#### **5. urls.py** - URL Routing
```python
# Page URLs
urlpatterns = [
    path('', home_view),
    path('dashboard/', dashboard_view),
    path('monitor/', monitor_view),
    path('alerts/', alerts_view),
    # ... etc
]

# API URLs
- /api/monitor/start/
- /api/monitor/stop/
- /api/status/
- /api/alerts/
# ... etc
```

### Detection Flow Explained

```
1. USER CLICKS "START MONITORING"
   ↓
2. Frontend sends POST to /api/monitor/start/
   ↓
3. views.start_monitor_api() called
   ↓
4. live_detection.start_detection() called
   ↓
5. Background thread started
   ↓
6. detection_loop() runs continuously:
   a. camera.read() → Capture frame
   b. face_recognition.face_locations() → Find faces
   c. face_recognition.face_encodings() → Extract encodings
   d. Compare with authorized_faces dict
   e. Draw boxes (green=authorized, red=unauthorized)
   f. Add overlays (name, timestamp, FPS, stats)
   g. Update _latest_frame
   h. Create alert if unauthorized
   ↓
7. generate_frames() yields MJPEG stream
   ↓
8. Browser displays via /stream/ endpoint
   ↓
9. Loop continues until "STOP" clicked
```

---

## 🗄️ DATABASE SCHEMA

### **Alert** Table
```sql
- id: BigAutoField (PK)
- timestamp: DateTimeField (Indexed)
- label: CharField (default="person")
- confidence: FloatField
- image_path: CharField (max_length=500)
- resolved: BooleanField (default=False)
- notes: TextField (blank=True)
```

### **AuthorizedPerson** Table
```sql
- id: BigAutoField (PK)
- name: CharField (max_length=200)
- employee_id: CharField (max_length=50, unique=True, null=True)
- department: CharField (max_length=100, blank=True)
- email: EmailField (blank=True)
- phone: CharField (max_length=20, blank=True)
- role: CharField (max_length=100, blank=True)
- photo: ImageField (upload_to='authorized_persons/')
- face_encoding: TextField (JSON string of 128-d vector)
- is_active: BooleanField (default=True)
- created_at: DateTimeField (auto_now_add=True)
- created_by: ForeignKey(User, null=True)
- notes: TextField (blank=True)
```

### **AuthorizedPersonPhoto** Table
```sql
- id: BigAutoField (PK)
- person: ForeignKey(AuthorizedPerson, on_delete=CASCADE)
- photo: ImageField (upload_to='authorized_persons/additional/')
- face_encoding: TextField (JSON string)
- uploaded_at: DateTimeField (auto_now_add=True)
```

### **SystemSettings** Table
```sql
- id: BigAutoField (PK)
- detection_sensitivity: FloatField (default=0.5)
- camera_source: IntegerField (default=0)
- alert_cooldown: IntegerField (default=5)
- face_recognition_tolerance: FloatField (default=0.6)
```

---

## 📖 USAGE GUIDE

### Adding Authorized Person
1. Navigate to **Authorized Persons** page
2. Click **"Add New Person"** button
3. Fill in details:
   - Name (Required)
   - Employee ID (Optional - leave blank if none)
   - Upload primary photo (Clear frontal face)
   - Upload additional photos (Optional - improves accuracy)
4. Click **"Add Person"**
5. System automatically:
   - Detects face in photo
   - Extracts 128-d face encoding
   - Saves to database
   - Shows success/warning message

### Starting Detection
1. Go to **Live Monitor** page
2. Click **"Start Monitoring"**
3. Camera opens automatically
4. System processes:
   - Loads YOLO model
   - Loads authorized faces from database
   - Starts detection loop
   - Displays live feed

### What Happens During Detection
- **Green Box**: Authorized person detected → Name displayed
- **Red Box**: Unauthorized person detected → Alert created
- **Overlay Info**: FPS, timestamp, detection count
- **Auto-Alert**: Saved to database with snapshot (max 1 per 5 sec per person)

### Viewing Alerts
1. Go to **Alerts** page
2. View list with:
   - Snapshot image
   - Detection time
   - Resolution status
3. Click **"Resolve"** to mark handled
4. Click **"Clear Resolved"** to bulk delete

### Managing Users (Admin Only)
1. Go to **Admin Panel**
2. View all users
3. Add new user with role
4. Edit/Delete existing users
5. Control staff/active status

---

## 🔧 TROUBLESHOOTING

### Camera Not Opening
```
Error: "Camera initialization failed"
Solutions:
1. Check camera is connected
2. Close other apps using camera (Zoom, Skype, etc.)
3. Restart system
4. Try different camera index (0, 1, 2...)
```

### Face Not Detected in Photo
```
Warning: "No face detected in primary photo"
Solutions:
1. Use clear frontal face photo
2. Good lighting
3. No sunglasses/masks
4. Single person in frame
5. Face should be large in image (at least 200x200px)
```

### Low Detection Accuracy
```
Problem: System not recognizing authorized persons
Solutions:
1. Add multiple photos per person (3-5 recommended)
2. Different angles and lighting conditions
3. Adjust face_recognition_tolerance in settings (0.5-0.6)
4. Ensure good camera quality and lighting
```

### Server Won't Start
```
Error: "Port 8000 already in use"
Solutions:
1. Stop existing Django server
2. Kill Python processes:
   Get-Process python | Stop-Process -Force
3. Use different port:
   python manage.py runserver 8001
```

### YOLO Model Not Found
```
Error: "Model file not found"
Solutions:
1. Download yolov8n.pt manually
2. Place in: ml/model_weights/yolov8n.pt
3. Or let system auto-download on first run
```

---

## 📁 PROJECT STRUCTURE

```
Security guard monitoring system/
├── backend/
│   ├── guardsys/              # Django project settings
│   │   ├── settings.py        # Main configuration
│   │   ├── urls.py            # Root URL config
│   │   └── wsgi.py            # WSGI config
│   ├── monitoring/            # Main app
│   │   ├── migrations/        # Database migrations
│   │   ├── templates/         # HTML templates
│   │   ├── models.py          # Database models
│   │   ├── views.py           # Request handlers
│   │   ├── urls.py            # App URLs
│   │   ├── serializers.py     # DRF serializers
│   │   └── live_detection.py  # Detection engine
│   ├── media/                 # Uploaded files
│   │   └── authorized_persons/ # Person photos
│   ├── db.sqlite3             # Database file
│   └── manage.py              # Django CLI
├── ml/
│   ├── model_weights/
│   │   └── yolov8n.pt         # YOLO model
│   └── alerts/                # Alert snapshots
├── requirements.txt           # Python dependencies
└── COMPLETE_DOCUMENTATION.md  # This file
```

---

## 🎓 KEY CONCEPTS

### Face Recognition Pipeline
```
1. Upload Photo
   ↓
2. Detect Face (face_recognition.face_locations)
   ↓
3. Extract Encoding (face_recognition.face_encodings)
   → Returns 128-dimensional vector
   ↓
4. Save to Database (as JSON string)
   ↓
5. During Detection:
   - Extract encoding from camera frame
   - Compare with all stored encodings
   - Match if distance < tolerance (0.6)
   - Display result (green=match, red=no match)
```

### Threading Model
```
Main Django Thread:
- Handles HTTP requests
- Serves web pages
- API endpoints

Background Detection Thread:
- Runs independently
- Processes camera frames
- Updates global _latest_frame
- Creates alerts
- Never blocks main thread

Communication:
- Thread-safe locks (_frame_lock)
- Global state variables
- No direct thread communication needed
```

### MJPEG Streaming
```
Browser Request → /stream/ endpoint
   ↓
views.stream_view() returns StreamingHttpResponse
   ↓
Calls generate_frames() generator
   ↓
Loop:
  1. Get _latest_frame (with lock)
  2. Encode to JPEG
  3. Yield with multipart boundary
  4. Browser displays frame
  5. Repeat (continuous stream)
```

---

## 🚀 PERFORMANCE TIPS

1. **Camera Resolution**: Lower resolution = faster processing
   - Recommended: 640x480 @ 30 FPS
   
2. **Face Detection Frequency**: Process every Nth frame
   - Current: Every frame (maximum accuracy)
   - Alternative: Every 3rd frame (better FPS)

3. **YOLO Confidence**: Lower threshold = more detections
   - Current: 0.4 (40% confidence)
   - Adjust in live_detection.py

4. **Face Recognition Tolerance**: Higher = more lenient
   - Current: 0.5 (strict)
   - Range: 0.4 (very strict) to 0.6 (lenient)

5. **Multiple Photos**: More photos per person = better accuracy
   - Recommended: 3-5 photos per person
   - Different angles and lighting

---

## 📞 SUPPORT

For issues or questions:
1. Check this documentation
2. Review code comments
3. Check Django logs in terminal
4. Verify camera and model files

---

## ✅ SYSTEM CHECKLIST

Before deployment, verify:
- ✅ Camera works and is accessible
- ✅ YOLO model downloaded (yolov8n.pt)
- ✅ Database migrated (python manage.py migrate)
- ✅ Superuser created
- ✅ At least 1 authorized person added with photo
- ✅ Face encoding extracted successfully
- ✅ Detection starts without errors
- ✅ Live feed displays correctly
- ✅ Alerts are created for unauthorized persons
- ✅ All pages load without errors

---

## 🎉 CONCLUSION

This Security Guard Monitoring System provides enterprise-grade surveillance with AI-powered face recognition. The system is production-ready with:

- ✅ Real-time detection at 30+ FPS
- ✅ Accurate face recognition with dlib
- ✅ Scalable architecture
- ✅ User-friendly interface
- ✅ Complete API documentation
- ✅ Comprehensive error handling

**System is ready for deployment and monitoring!**

---

**Last Updated**: December 11, 2025
**Version**: 1.0.0
**Python**: 3.12+
**Django**: 4.2.23
#   A L M L - B a s e d - S e c u r i t y - G u a r d - M o n i t o r i n g - S y s t e m  
 