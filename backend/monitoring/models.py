# backend/monitoring/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Alert(models.Model):
    """Model for storing detection alerts"""
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    label = models.CharField(max_length=100, default='person')
    confidence = models.FloatField()
    image_path = models.CharField(max_length=500)
    resolved = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp', 'resolved']),
        ]
    
    def __str__(self):
        return f"Alert: {self.label} at {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
    
    @property
    def image_url(self):
        """Get relative URL for the alert image"""
        return f"/media/alerts/{self.image_path.split('/')[-1]}"

class SystemSettings(models.Model):
    """Model for storing system configuration"""
    confidence_threshold = models.FloatField(default=0.4)
    detection_enabled = models.BooleanField(default=False)
    alert_sound_enabled = models.BooleanField(default=True)
    email_alerts_enabled = models.BooleanField(default=False)
    sms_alerts_enabled = models.BooleanField(default=False)
    
    # Email settings
    alert_email = models.EmailField(blank=True)
    alert_phone = models.CharField(max_length=20, blank=True)
    
    # Detection parameters
    min_detection_confidence = models.FloatField(default=0.4)
    alert_cooldown_seconds = models.IntegerField(default=30)
    
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        verbose_name = "System Settings"
        verbose_name_plural = "System Settings"
    
    def __str__(self):
        return f"Settings (Updated: {self.updated_at.strftime('%Y-%m-%d %H:%M')})"
    
    @classmethod
    def get_settings(cls):
        """Get or create singleton settings instance"""
        settings, created = cls.objects.get_or_create(pk=1)
        return settings

class DetectionSession(models.Model):
    """Model for tracking detection sessions"""
    started_at = models.DateTimeField(default=timezone.now)
    ended_at = models.DateTimeField(null=True, blank=True)
    started_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    total_detections = models.IntegerField(default=0)
    total_alerts = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-started_at']
    
    def __str__(self):
        status = "Active" if self.ended_at is None else "Ended"
        return f"Session {self.id} - {status} ({self.started_at.strftime('%Y-%m-%d %H:%M')})"
    
    @property
    def duration(self):
        """Calculate session duration"""
        if self.ended_at:
            return (self.ended_at - self.started_at).total_seconds()
        return (timezone.now() - self.started_at).total_seconds()

class AuthorizedPerson(models.Model):
    """Model for storing authorized person photos for face recognition"""
    name = models.CharField(max_length=200)
    employee_id = models.CharField(max_length=50, unique=True, blank=True, null=True)
    department = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    role = models.CharField(max_length=100, blank=True)
    photo = models.ImageField(upload_to='authorized_persons/')
    face_encoding = models.TextField(blank=True)  # Store face encoding as JSON
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = "Authorized Person"
        verbose_name_plural = "Authorized Persons"
    
    def save(self, *args, **kwargs):
        # Convert empty string to None for unique constraint
        if self.employee_id == '':
            self.employee_id = None
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.name} ({self.employee_id or 'No ID'})"


class AuthorizedPersonPhoto(models.Model):
    """Model for additional photos of authorized persons"""
    person = models.ForeignKey(AuthorizedPerson, on_delete=models.CASCADE, related_name='additional_photos')
    photo = models.ImageField(upload_to='authorized_persons/additional/')
    face_encoding = models.TextField(blank=True)
    uploaded_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = "Additional Photo"
        verbose_name_plural = "Additional Photos"
    
    def __str__(self):
        return f"Photo for {self.person.name} ({self.uploaded_at.strftime('%Y-%m-%d')})"

class TrainingJob(models.Model):
    """Model for tracking model training jobs"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    created_at = models.DateTimeField(default=timezone.now)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    dataset_path = models.CharField(max_length=500)
    model_name = models.CharField(max_length=100, default='yolov8n')
    
    epochs = models.IntegerField(default=50)
    batch_size = models.IntegerField(default=8)
    image_size = models.IntegerField(default=640)
    
    progress = models.IntegerField(default=0)  # 0-100
    logs = models.TextField(blank=True)
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Training Job {self.id} - {self.status} ({self.model_name})"
