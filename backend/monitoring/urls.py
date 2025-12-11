# backend/monitoring/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Authentication
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Main pages
    path('', views.home_view, name='home'),
    path('SS-admin.html', views.admin_panel_view, name='admin_panel'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('monitor/', views.live_monitor_view, name='live_monitor'),
    path('alerts/', views.alerts_log_view, name='alerts_log'),
    path('model/', views.model_management_view, name='model_management'),
    path('settings/', views.settings_view, name='settings'),
    path('help/', views.help_view, name='help'),
    
    # Streaming
    path('monitor/stream/', views.stream_view, name='stream'),
    path('stream/', views.stream_view, name='stream_alt'),
    
    # Authorized Persons Management
    path('authorized-persons/', views.authorized_persons_view, name='authorized_persons'),
    
    # API endpoints
    path('api/monitor/start/', views.start_monitor_api, name='api_start_monitor'),
    path('api/monitor/stop/', views.stop_monitor_api, name='api_stop_monitor'),
    path('api/status/', views.status_api, name='api_status'),
    path('api/alerts/', views.alerts_api, name='api_alerts'),
    path('api/alerts/<int:alert_id>/resolve/', views.resolve_alert_api, name='api_resolve_alert'),
    path('api/alerts/clear/', views.clear_alerts_api, name='api_clear_alerts'),
    path('api/snapshot/', views.snapshot_api, name='api_snapshot'),
    path('api/manual-alert/', views.manual_alert_api, name='api_manual_alert'),
    path('api/training/start/', views.start_training_api, name='api_start_training'),
]
