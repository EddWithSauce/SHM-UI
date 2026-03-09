from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing, name='landing'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Dashboards
    path('dashboard/shm/', views.dashboard_shm, name='dashboard_shm'),
    path('dashboard/nfd/', views.dashboard_nfd, name='dashboard_nfd'),
    path('dashboard/drift/', views.dashboard_drift, name='dashboard_drift'),

    # ==================== SHM API Endpoints ====================
    path('api/shm/sensors/', views.shm_api_sensors, name='shm_sensors'),
    path('api/shm/readings/', views.shm_api_readings, name='shm_readings'),
    path('api/shm/events/', views.shm_api_events, name='shm_events'),
    path('api/shm/events/add/', views.shm_api_add_event, name='shm_add_event'),

    # ==================== NFD API Endpoints ====================
    path('api/nfd/frequencies/', views.nfd_api_frequencies, name='nfd_frequencies'),
    path('api/nfd/comparisons/', views.nfd_api_comparisons, name='nfd_comparisons'),
    path('api/nfd/frequencies/add/', views.nfd_api_add_frequency, name='nfd_add_frequency'),

    # ==================== Drift API Endpoints ====================
    path('api/drift/measurements/', views.drift_api_measurements, name='drift_measurements'),
    path('api/drift/alerts/', views.drift_api_alerts, name='drift_alerts'),
    path('api/drift/measurements/add/', views.drift_api_add_measurement, name='drift_add_measurement'),
    path('api/drift/alerts/add/', views.drift_api_create_alert, name='drift_create_alert'),

    # ==================== System API Endpoints ====================
    path('api/system/settings/', views.system_api_settings, name='system_settings'),

    # ==================== Export Endpoints ====================
    path('export/', views.export_data, name='export_data'),
]
