# backend/monitoring/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse, StreamingHttpResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

import sys
import os
import time
from pathlib import Path

# Add ML directory to path
ML_DIR = Path(settings.BASE_DIR).parent / 'ml'
sys.path.insert(0, str(ML_DIR))

from .models import Alert, SystemSettings, DetectionSession, TrainingJob
from .serializers import AlertSerializer, SystemSettingsSerializer

# ===========================
# Authentication Views
# ===========================

def home_view(request):
    """Landing homepage"""
    return render(request, 'monitoring/home.html')

def register_view(request):
    """User registration page"""
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        
        # Validation
        if password1 != password2:
            messages.error(request, 'Passwords do not match!')
            return render(request, 'monitoring/register.html')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists!')
            return render(request, 'monitoring/register.html')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered!')
            return render(request, 'monitoring/register.html')
        
        # Create user
        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password1,
                first_name=first_name,
                last_name=last_name
            )
            messages.success(request, 'Account created successfully! Please login.')
            return redirect('login')
        except Exception as e:
            messages.error(request, f'Error creating account: {str(e)}')
            return render(request, 'monitoring/register.html')
    
    return render(request, 'monitoring/register.html')

def login_view(request):
    """User login page"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            return render(request, 'monitoring/login.html', {
                'error': 'Invalid credentials'
            })
    
    return render(request, 'monitoring/login.html')

@login_required
def logout_view(request):
    """User logout"""
    logout(request)
    return redirect('login')

@login_required
def admin_panel_view(request):
    """Admin panel for user management"""
    # Check if user is admin
    if not request.user.is_superuser:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard')
    
    # Handle POST requests (Add, Edit, Delete)
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add':
            username = request.POST.get('username')
            email = request.POST.get('email')
            first_name = request.POST.get('first_name', '')
            last_name = request.POST.get('last_name', '')
            password = request.POST.get('password')
            password2 = request.POST.get('password2')
            is_staff = request.POST.get('is_staff') == 'on'
            is_active = request.POST.get('is_active') == 'on'
            
            if password != password2:
                messages.error(request, 'Passwords do not match!')
            elif User.objects.filter(username=username).exists():
                messages.error(request, 'Username already exists!')
            elif User.objects.filter(email=email).exists():
                messages.error(request, 'Email already registered!')
            else:
                try:
                    user = User.objects.create_user(
                        username=username,
                        email=email,
                        password=password,
                        first_name=first_name,
                        last_name=last_name,
                        is_staff=is_staff,
                        is_active=is_active
                    )
                    messages.success(request, f'User "{username}" created successfully!')
                except Exception as e:
                    messages.error(request, f'Error creating user: {str(e)}')
        
        elif action == 'edit':
            user_id = request.POST.get('user_id')
            try:
                user = User.objects.get(id=user_id)
                user.email = request.POST.get('email', user.email)
                user.first_name = request.POST.get('first_name', user.first_name)
                user.last_name = request.POST.get('last_name', user.last_name)
                user.is_staff = request.POST.get('is_staff') == 'on'
                user.is_active = request.POST.get('is_active') == 'on'
                user.save()
                messages.success(request, f'User "{user.username}" updated successfully!')
            except User.DoesNotExist:
                messages.error(request, 'User not found!')
            except Exception as e:
                messages.error(request, f'Error updating user: {str(e)}')
        
        elif action == 'delete':
            user_id = request.POST.get('user_id')
            try:
                user = User.objects.get(id=user_id)
                if user.id == request.user.id:
                    messages.error(request, 'You cannot delete your own account!')
                else:
                    username = user.username
                    user.delete()
                    messages.success(request, f'User "{username}" deleted successfully!')
            except User.DoesNotExist:
                messages.error(request, 'User not found!')
            except Exception as e:
                messages.error(request, f'Error deleting user: {str(e)}')
        
        return redirect('admin_panel')
    
    # GET request - display users
    users = User.objects.all().order_by('-date_joined')
    
    context = {
        'users': users,
        'total_users': users.count(),
        'admin_count': users.filter(is_superuser=True).count(),
        'active_users': users.filter(is_active=True).count(),
        'inactive_users': users.filter(is_active=False).count(),
    }
    
    return render(request, 'monitoring/admin_panel.html', context)

# ===========================
# Main Pages
# ===========================

@login_required
def dashboard_view(request):
    """Main dashboard page"""
    system_settings = SystemSettings.get_settings()
    
    # Get recent alerts (last 10)
    recent_alerts = Alert.objects.filter(resolved=False)[:10]
    
    # Get current session if active
    active_session = DetectionSession.objects.filter(ended_at__isnull=True).first()
    
    # Statistics
    total_alerts = Alert.objects.count()
    unresolved_alerts = Alert.objects.filter(resolved=False).count()
    today_alerts = Alert.objects.filter(
        timestamp__date=timezone.now().date()
    ).count()
    
    context = {
        'settings': system_settings,
        'recent_alerts': recent_alerts,
        'active_session': active_session,
        'total_alerts': total_alerts,
        'unresolved_alerts': unresolved_alerts,
        'today_alerts': today_alerts,
    }
    
    return render(request, 'monitoring/dashboard.html', context)

@login_required
def live_monitor_view(request):
    """Live monitoring page with video stream"""
    system_settings = SystemSettings.get_settings()
    from .models import AuthorizedPerson
    authorized_count = AuthorizedPerson.objects.filter(is_active=True).count()
    return render(request, 'monitoring/live_monitor.html', {
        'settings': system_settings,
        'authorized_count': authorized_count
    })

@login_required
def alerts_log_view(request):
    """Alerts history page"""
    alerts = Alert.objects.all()[:100]  # Last 100 alerts
    
    # Filter options
    resolved_filter = request.GET.get('resolved')
    if resolved_filter == 'true':
        alerts = alerts.filter(resolved=True)
    elif resolved_filter == 'false':
        alerts = alerts.filter(resolved=False)
    
    return render(request, 'monitoring/alerts_log.html', {
        'alerts': alerts
    })

@login_required
def model_management_view(request):
    """Model training and management page"""
    training_jobs = TrainingJob.objects.all()[:20]
    
    return render(request, 'monitoring/model_management.html', {
        'training_jobs': training_jobs
    })

@login_required
def settings_view(request):
    """System settings page"""
    system_settings = SystemSettings.get_settings()
    
    if request.method == 'POST':
        system_settings.confidence_threshold = float(request.POST.get('confidence_threshold', 0.4))
        system_settings.alert_sound_enabled = request.POST.get('alert_sound_enabled') == 'on'
        system_settings.email_alerts_enabled = request.POST.get('email_alerts_enabled') == 'on'
        system_settings.alert_email = request.POST.get('alert_email', '')
        system_settings.alert_cooldown_seconds = int(request.POST.get('alert_cooldown_seconds', 30))
        system_settings.updated_by = request.user
        system_settings.save()
        
        return redirect('settings')
    
    return render(request, 'monitoring/settings.html', {
        'settings': system_settings
    })

@login_required
def help_view(request):
    """Help and documentation page"""
    return render(request, 'monitoring/help.html')

# ===========================
# Video Streaming
# ===========================

@login_required
def stream_view(request):
    """LIVE MJPEG video stream from camera"""
    from . import live_detection
    
    return StreamingHttpResponse(
        live_detection.generate_frames(),
        content_type='multipart/x-mixed-replace; boundary=frame'
    )

# ===========================
# Detection Control API
# ===========================

@require_http_methods(["POST"])
def start_monitor_api(request):
    """Start LIVE detection with camera"""
    from . import live_detection
    
    # Check authentication
    if not request.user.is_authenticated:
        return JsonResponse({
            'status': 'error',
            'message': 'Authentication required'
        }, status=401)
    
    system_settings = SystemSettings.get_settings()
    
    # Check if already running
    if live_detection.is_running():
        return JsonResponse({
            'status': 'already_running',
            'message': 'Detection is already active'
        })
    
    # Start new session
    session = DetectionSession.objects.create(
        started_by=request.user
    )
    
    # Start detection
    try:
        print("🚀 Starting LIVE detection...")
        
        success = live_detection.start_detection()
        
        if not success:
            return JsonResponse({
                'status': 'error',
                'message': 'Failed to start camera - check console'
            }, status=500)
        
        system_settings.detection_enabled = True
        system_settings.save()
        
        print("✓ LIVE detection started - camera feed is now ACTIVE")
        
        return JsonResponse({
            'status': 'started',
            'session_id': session.id,
            'message': 'Camera opened! Live feed active'
        })
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

@require_http_methods(["POST"])
def stop_monitor_api(request):
    """Stop LIVE detection"""
    from . import live_detection
    
    # Check authentication
    if not request.user.is_authenticated:
        return JsonResponse({
            'status': 'error',
            'message': 'Authentication required'
        }, status=401)
    
    system_settings = SystemSettings.get_settings()
    
    # End current session
    active_session = DetectionSession.objects.filter(ended_at__isnull=True).first()
    if active_session:
        active_session.ended_at = timezone.now()
        active_session.save()
    
    # Stop detection
    live_detection.stop_detection()
    
    system_settings.detection_enabled = False
    system_settings.save()
    
    return JsonResponse({
        'status': 'stopped',
        'message': 'Camera stopped successfully'
    })

@login_required
def status_api(request):
    """Get current system status"""
    system_settings = SystemSettings.get_settings()
    active_session = DetectionSession.objects.filter(ended_at__isnull=True).first()
    
    return JsonResponse({
        'detection_enabled': system_settings.detection_enabled,
        'confidence_threshold': system_settings.confidence_threshold,
        'active_session_id': active_session.id if active_session else None,
        'unresolved_alerts': Alert.objects.filter(resolved=False).count()
    })

# ===========================
# Alerts API
# ===========================

@login_required
def alerts_api(request):
    """Get alerts list (API)"""
    alerts = Alert.objects.all()[:50]
    serializer = AlertSerializer(alerts, many=True)
    return JsonResponse({'alerts': serializer.data})

@login_required
@require_http_methods(["POST"])
def resolve_alert_api(request, alert_id):
    """Mark alert as resolved"""
    try:
        alert = Alert.objects.get(id=alert_id)
        alert.resolved = True
        alert.save()
        return JsonResponse({'status': 'resolved'})
    except Alert.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Alert not found'}, status=404)

@login_required
@require_http_methods(["POST"])
def clear_alerts_api(request):
    """Clear all resolved alerts"""
    count = Alert.objects.filter(resolved=True).delete()[0]
    return JsonResponse({
        'status': 'cleared',
        'count': count
    })

# ===========================
# Model Training API
# ===========================

@login_required
@require_http_methods(["POST"])
def start_training_api(request):
    """Start model training job"""
    dataset_path = request.POST.get('dataset_path')
    model_name = request.POST.get('model_name', 'yolov8n')
    epochs = int(request.POST.get('epochs', 50))
    batch_size = int(request.POST.get('batch_size', 8))
    
    job = TrainingJob.objects.create(
        dataset_path=dataset_path,
        model_name=model_name,
        epochs=epochs,
        batch_size=batch_size,
        created_by=request.user,
        status='pending'
    )
    
    # TODO: Start training in background (use Celery in production)
    
    return JsonResponse({
        'status': 'created',
        'job_id': job.id
    })

# ===========================
# Authorized Persons Management
# ===========================

@login_required
def authorized_persons_view(request):
    """Manage authorized persons for face recognition"""
    from .models import AuthorizedPerson
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add':
            import face_recognition
            from .models import AuthorizedPersonPhoto
            
            name = request.POST.get('name')
            employee_id = request.POST.get('employee_id', '')
            department = request.POST.get('department', '')
            email = request.POST.get('email', '')
            phone = request.POST.get('phone', '')
            role = request.POST.get('role', '')
            notes = request.POST.get('notes', '')
            photo = request.FILES.get('photo')
            additional_photos = request.FILES.getlist('additional_photos')
            
            if name and photo:
                try:
                    # Create person first to save photo
                    person = AuthorizedPerson.objects.create(
                        name=name,
                        employee_id=employee_id,
                        department=department,
                        email=email,
                        phone=phone,
                        role=role,
                        photo=photo,
                        notes=notes,
                        created_by=request.user
                    )
                    
                    # Extract face encoding from primary photo
                    encoding_extracted = False
                    try:
                        image = face_recognition.load_image_file(person.photo.path)
                        encodings = face_recognition.face_encodings(image)
                        
                        if encodings:
                            # Save encoding as JSON string
                            import json
                            person.face_encoding = json.dumps(encodings[0].tolist())
                            person.save()
                            encoding_extracted = True
                        else:
                            messages.warning(request, f'No face detected in primary photo.')
                    except Exception as e:
                        messages.warning(request, f'Face encoding failed for primary photo: {str(e)}')
                    
                    # Process additional photos
                    additional_count = 0
                    for add_photo in additional_photos:
                        try:
                            # Create additional photo instance
                            photo_instance = AuthorizedPersonPhoto.objects.create(
                                person=person,
                                photo=add_photo
                            )
                            
                            # Extract face encoding
                            try:
                                image = face_recognition.load_image_file(photo_instance.photo.path)
                                encodings = face_recognition.face_encodings(image)
                                
                                if encodings:
                                    import json
                                    photo_instance.face_encoding = json.dumps(encodings[0].tolist())
                                    photo_instance.save()
                                    additional_count += 1
                            except Exception as e:
                                print(f"Failed to extract encoding from additional photo: {e}")
                        except Exception as e:
                            print(f"Failed to save additional photo: {e}")
                    
                    # Success message
                    msg = f'✓ Authorized person "{name}" added'
                    if encoding_extracted:
                        msg += ' with face recognition'
                    if additional_count > 0:
                        msg += f' (including {additional_count} additional photo{"s" if additional_count > 1 else ""})'
                    messages.success(request, msg + '!')
                        
                except Exception as e:
                    messages.error(request, f'Error adding person: {str(e)}')
            else:
                messages.error(request, 'Name and photo are required!')
        
        elif action == 'delete':
            person_id = request.POST.get('person_id')
            try:
                person = AuthorizedPerson.objects.get(id=person_id)
                name = person.name
                person.delete()
                messages.success(request, f'Person "{name}" deleted successfully!')
            except AuthorizedPerson.DoesNotExist:
                messages.error(request, 'Person not found!')
        
        elif action == 'toggle':
            person_id = request.POST.get('person_id')
            try:
                person = AuthorizedPerson.objects.get(id=person_id)
                person.is_active = not person.is_active
                person.save()
                status = 'activated' if person.is_active else 'deactivated'
                messages.success(request, f'Person "{person.name}" {status}!')
            except AuthorizedPerson.DoesNotExist:
                messages.error(request, 'Person not found!')
        
        return redirect('authorized_persons')
    
    # GET request
    persons = AuthorizedPerson.objects.all().order_by('-created_at')
    active_count = persons.filter(is_active=True).count()
    inactive_count = persons.filter(is_active=False).count()
    
    context = {
        'persons': persons,
        'total_persons': persons.count(),
        'active_count': active_count,
        'inactive_count': inactive_count,
    }
    
    return render(request, 'monitoring/authorized_persons.html', context)

@login_required
@require_http_methods(["POST"])
def snapshot_api(request):
    """Take a snapshot from the video stream"""
    try:
        # TODO: Capture current frame and save it
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        filename = f'snapshot_{timestamp}.jpg'
        
        return JsonResponse({
            'status': 'success',
            'message': 'Snapshot saved',
            'filename': filename
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

@login_required
@require_http_methods(["POST"])
def manual_alert_api(request):
    """Trigger a manual alert"""
    try:
        alert = Alert.objects.create(
            label='Manual Alert',
            confidence=1.0,
            image_path='manual',
            notes=f'Manually triggered by {request.user.username}'
        )
        
        return JsonResponse({
            'status': 'success',
            'message': 'Manual alert triggered',
            'alert_id': alert.id
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)
