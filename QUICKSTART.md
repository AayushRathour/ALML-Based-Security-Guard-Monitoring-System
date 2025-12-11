# 🚀 Quick Start Guide

## Installation (5 Minutes)

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Setup Database
```bash
cd backend
python manage.py migrate
python manage.py createsuperuser
```
Create admin user:
- Username: `admin`
- Password: `admin123`

### Step 3: Run Server
```bash
python manage.py runserver
```

### Step 4: Access System
Open browser: **http://127.0.0.1:8000**

Login with your admin credentials.

---

## First-Time Setup

### Add Authorized Person
1. Go to **Authorized Persons** page
2. Click **"Add New Person"**
3. Enter name and upload a clear frontal face photo
4. (Optional) Leave Employee ID blank or enter unique ID
5. Click **"Add Person"**

### Start Detection
1. Go to **Live Monitor** page
2. Click **"Start Monitoring"**
3. Camera will open automatically
4. System detects faces and shows:
   - **Green boxes** = Authorized persons
   - **Red boxes** = Unauthorized persons (creates alert)

---

## Key Features

✅ Real-time face detection at 30+ FPS
✅ Automatic alert generation for unauthorized persons
✅ Multiple photos per person for better accuracy
✅ Live video stream with overlays
✅ Complete alert management
✅ User authentication system

---

## Troubleshooting

**Camera not opening?**
- Close other apps using the camera
- Check camera permissions
- Try restarting the system

**Face not detected in photo?**
- Use clear frontal face photo
- Good lighting required
- No sunglasses/masks
- Face should be large in frame

**Can't add person - UNIQUE constraint error?**
- Leave Employee ID field blank if you don't have one
- System allows multiple persons without Employee IDs

---

## Complete Documentation

For full documentation, see: **README.md**

---

**System Status**: ✅ Ready for deployment
**Version**: 1.0.0
**Last Updated**: December 11, 2025
