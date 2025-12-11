# backend/monitoring/serializers.py
from rest_framework import serializers
from .models import Alert, SystemSettings, DetectionSession, TrainingJob

class AlertSerializer(serializers.ModelSerializer):
    image_url = serializers.ReadOnlyField()
    
    class Meta:
        model = Alert
        fields = ['id', 'timestamp', 'label', 'confidence', 'image_path', 
                  'image_url', 'resolved', 'notes']

class SystemSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemSettings
        fields = ['confidence_threshold', 'detection_enabled', 
                  'alert_sound_enabled', 'email_alerts_enabled', 
                  'alert_email', 'min_detection_confidence']

class DetectionSessionSerializer(serializers.ModelSerializer):
    duration = serializers.ReadOnlyField()
    
    class Meta:
        model = DetectionSession
        fields = ['id', 'started_at', 'ended_at', 'total_detections', 
                  'total_alerts', 'duration']

class TrainingJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainingJob
        fields = ['id', 'created_at', 'status', 'model_name', 'epochs', 
                  'progress', 'logs']
