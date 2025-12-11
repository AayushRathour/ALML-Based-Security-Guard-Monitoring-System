# backend/monitoring/admin.py
from django.contrib import admin
from .models import Alert, SystemSettings, DetectionSession, TrainingJob

@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ['id', 'timestamp', 'label', 'confidence', 'resolved']
    list_filter = ['resolved', 'label', 'timestamp']
    search_fields = ['label', 'notes']
    date_hierarchy = 'timestamp'

@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    list_display = ['confidence_threshold', 'detection_enabled', 'updated_at']

@admin.register(DetectionSession)
class DetectionSessionAdmin(admin.ModelAdmin):
    list_display = ['id', 'started_at', 'ended_at', 'total_detections', 'total_alerts']
    date_hierarchy = 'started_at'

@admin.register(TrainingJob)
class TrainingJobAdmin(admin.ModelAdmin):
    list_display = ['id', 'status', 'model_name', 'progress', 'created_at']
    list_filter = ['status', 'model_name']
    date_hierarchy = 'created_at'
