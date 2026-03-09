from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db.models import Q, Avg, Max, Min, Count
from django.utils import timezone
from datetime import timedelta
import json

from .models import (
    Sensor, SensorReading, Event, SHMTrend,
    ETABSBaseline, NaturalFrequency, FFTAnalysis, FrequencyComparison,
    FloorLevel, DriftMeasurement, DriftSafetyThreshold, DriftAlert,
    SystemSettings, Alert
)


def landing(request):
    return render(request, 'landing.html')


# ✅ Simple role routing (edit usernames to match your real admin accounts)
DASHBOARD_BY_USERNAME = {
    "admin_shm": "dashboard_shm",
    "admin_nfd": "dashboard_nfd",
    "admin_drift": "dashboard_drift",
}


def login_view(request):
    if request.user.is_authenticated:
        # If already logged in, route them
        return redirect(route_user_dashboard(request.user.username))

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "").strip()

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect(route_user_dashboard(user.username))

        messages.error(request, "Invalid username or password.")

    return render(request, "login.html")


def route_user_dashboard(username: str):
    """
    Returns the dashboard route name based on username.
    Defaults to SHM if username is not mapped (you can change this behavior).
    """
    return DASHBOARD_BY_USERNAME.get(username, "dashboard_shm")


def logout_view(request):
    logout(request)
    return redirect("login")


# ----------------------------
# SHM DASHBOARD
# ----------------------------

@login_required(login_url="login")
def dashboard_shm(request):
    """SHM dashboard with real-time vibration monitoring"""
    
    # Get all sensors
    sensors = Sensor.objects.filter(is_active=True)
    
    # Get recent readings (last hour)
    last_hour = timezone.now() - timedelta(hours=1)
    recent_readings = SensorReading.objects.filter(
        timestamp__gte=last_hour
    ).select_related('sensor')
    
    # Get recent events
    recent_events = Event.objects.all().order_by('-start_time')[:10]
    
    # Calculate statistics
    stats = {
        'total_sensors': sensors.count(),
        'active_sensors': sensors.filter(is_active=True).count(),
        'events_today': Event.objects.filter(
            start_time__date=timezone.now().date()
        ).count(),
        'high_severity_events': Event.objects.filter(
            severity__in=['high', 'critical']
        ).count(),
    }
    
    context = {
        'sensors': sensors,
        'recent_readings': recent_readings,
        'recent_events': recent_events,
        'stats': stats,
    }
    
    return render(request, 'dashboards/shm.html', context)


@login_required(login_url="login")
@require_http_methods(["GET"])
def shm_api_sensors(request):
    """API endpoint to get all sensors with status"""
    sensors = Sensor.objects.all().values('id', 'name', 'location', 'is_active', 'last_reading', 'sensor_type')
    return JsonResponse({'sensors': list(sensors)})


@login_required(login_url="login")
@require_http_methods(["GET"])
def shm_api_readings(request):
    """API endpoint to get recent sensor readings"""
    sensor_id = request.GET.get('sensor_id')
    hours = int(request.GET.get('hours', 24))
    
    start_time = timezone.now() - timedelta(hours=hours)
    readings = SensorReading.objects.filter(
        timestamp__gte=start_time
    )
    
    if sensor_id:
        readings = readings.filter(sensor_id=sensor_id)
    
    readings = readings.values('timestamp', 'sensor_id', 'acceleration_x', 'acceleration_y', 'acceleration_z', 'magnitude')
    return JsonResponse({'readings': list(readings)})


@login_required(login_url="login")
@require_http_methods(["GET"])
def shm_api_events(request):
    """API endpoint to get events with filtering"""
    page = int(request.GET.get('page', 1))
    event_type = request.GET.get('event_type')
    severity = request.GET.get('severity')
    
    events = Event.objects.all()
    
    if event_type:
        events = events.filter(event_type=event_type)
    if severity:
        events = events.filter(severity=severity)
    
    paginator = Paginator(events.order_by('-start_time'), 20)
    page_obj = paginator.get_page(page)
    
    event_list = [{
        'id': e.id,
        'event_type': e.event_type,
        'severity': e.severity,
        'start_time': e.start_time.isoformat(),
        'end_time': e.end_time.isoformat(),
        'peak_acceleration': e.peak_acceleration,
        'sensor': e.sensor.name,
    } for e in page_obj]
    
    return JsonResponse({
        'events': event_list,
        'page': page,
        'total_pages': paginator.num_pages
    })


@login_required(login_url="login")
@require_http_methods(["POST"])
def shm_api_add_event(request):
    """Create a new event"""
    try:
        data = json.loads(request.body)
        
        event = Event.objects.create(
            sensor_id=data['sensor_id'],
            event_type=data['event_type'],
            severity=data['severity'],
            start_time=timezone.now(),
            end_time=timezone.now() + timedelta(seconds=int(data.get('duration', 60))),
            peak_acceleration=float(data['peak_acceleration']),
            description=data.get('description', '')
        )
        
        return JsonResponse({'status': 'success', 'event_id': event.id})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


# ----------------------------
# NFD DASHBOARD
# ----------------------------

@login_required(login_url="login")
def dashboard_nfd(request):
    """NFD dashboard with frequency analysis"""
    
    # Get active ETABS baseline
    active_baseline = ETABSBaseline.objects.filter(is_active=True).first()
    
    # Get all natural frequencies
    frequencies = NaturalFrequency.objects.select_related('baseline').order_by('mode_number')
    
    # Get recent FFT analyses
    recent_fft = FFTAnalysis.objects.all().order_by('-analysis_date')[:10]
    
    # Get frequency comparisons with alerts
    comparisons = FrequencyComparison.objects.all().order_by('-created_at')[:5]
    
    # Calculate statistics
    stats = {
        'total_modes': frequencies.count(),
        'comparisons_normal': FrequencyComparison.objects.filter(status='normal').count(),
        'comparisons_degraded': FrequencyComparison.objects.filter(status='degraded').count(),
        'comparisons_alert': FrequencyComparison.objects.filter(status='alert').count(),
    }
    
    context = {
        'active_baseline': active_baseline,
        'frequencies': frequencies,
        'recent_fft': recent_fft,
        'comparisons': comparisons,
        'stats': stats,
    }
    
    return render(request, 'dashboards/nfd.html', context)


@login_required(login_url="login")
@require_http_methods(["GET"])
def nfd_api_frequencies(request):
    """API endpoint to get natural frequencies"""
    baseline_id = request.GET.get('baseline_id')
    
    frequencies = NaturalFrequency.objects.all()
    
    if baseline_id:
        frequencies = frequencies.filter(baseline_id=baseline_id)
    
    freq_list = [{
        'id': f.id,
        'mode': f.mode_number,
        'frequency': f.frequency_hz,
        'damping': f.damping_ratio,
        'source': f.frequency_source,
        'baseline': f.baseline.name if f.baseline else None,
    } for f in frequencies.order_by('mode_number')]
    
    return JsonResponse({'frequencies': freq_list})


@login_required(login_url="login")
@require_http_methods(["GET"])
def nfd_api_comparisons(request):
    """API endpoint to get frequency comparisons"""
    status = request.GET.get('status')
    page = int(request.GET.get('page', 1))
    
    comparisons = FrequencyComparison.objects.all()
    
    if status:
        comparisons = comparisons.filter(status=status)
    
    paginator = Paginator(comparisons.order_by('-created_at'), 20)
    page_obj = paginator.get_page(page)
    
    comp_list = [{
        'id': c.id,
        'baseline_mode': c.baseline_frequency.mode_number,
        'baseline_freq': c.baseline_frequency.frequency_hz,
        'measured_freq': c.analysis.primary_frequency,
        'diff': c.frequency_diff,
        'diff_percent': c.frequency_diff_percent,
        'status': c.status,
        'assessment': c.assessment,
    } for c in page_obj]
    
    return JsonResponse({
        'comparisons': comp_list,
        'page': page,
        'total_pages': paginator.num_pages
    })


@login_required(login_url="login")
@require_http_methods(["POST"])
def nfd_api_add_frequency(request):
    """Add a new natural frequency"""
    try:
        data = json.loads(request.body)
        
        frequency = NaturalFrequency.objects.create(
            baseline_id=data.get('baseline_id'),
            mode_number=int(data['mode_number']),
            frequency_hz=float(data['frequency_hz']),
            frequency_source=data.get('frequency_source', 'experimental'),
            damping_ratio=float(data['damping_ratio']),
            notes=data.get('notes', '')
        )
        
        return JsonResponse({'status': 'success', 'frequency_id': frequency.id})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


# ----------------------------
# DRIFT DASHBOARD
# ----------------------------

@login_required(login_url="login")
def dashboard_drift(request):
    """Drift monitoring dashboard"""
    
    # Get all floor levels
    floors = FloorLevel.objects.all().order_by('floor_number')
    
    # Get recent drift measurements
    recent_measurements = DriftMeasurement.objects.all().order_by('-measurement_time')[:15]
    
    # Get active drift alerts (don't slice yet - we need to count first)
    active_alerts_query = DriftAlert.objects.filter(
        alert_status__in=['warning', 'critical']
    ).order_by('-alert_triggered_time')
    
    # Get safety thresholds
    thresholds = DriftSafetyThreshold.objects.filter(is_active=True)
    
    # Calculate statistics
    stats = {
        'total_floors': floors.count(),
        'total_thresholds': thresholds.count(),
        'active_warnings': active_alerts_query.filter(alert_status='warning').count(),
        'active_critical': active_alerts_query.filter(alert_status='critical').count(),
        'cleared_today': DriftAlert.objects.filter(
            alert_status='cleared',
            resolved_time__date=timezone.now().date()
        ).count(),
    }
    
    # Now slice for display
    active_alerts = active_alerts_query[:10]
    
    context = {
        'floors': floors,
        'recent_measurements': recent_measurements,
        'active_alerts': active_alerts,
        'thresholds': thresholds,
        'stats': stats,
    }
    
    return render(request, 'dashboards/drift.html', context)


@login_required(login_url="login")
@require_http_methods(["GET"])
def drift_api_measurements(request):
    """API endpoint to get drift measurements"""
    page = int(request.GET.get('page', 1))
    lower_floor = request.GET.get('lower_floor')
    upper_floor = request.GET.get('upper_floor')
    
    measurements = DriftMeasurement.objects.all()
    
    if lower_floor:
        measurements = measurements.filter(lower_floor_id=lower_floor)
    if upper_floor:
        measurements = measurements.filter(upper_floor_id=upper_floor)
    
    paginator = Paginator(measurements.order_by('-measurement_time'), 25)
    page_obj = paginator.get_page(page)
    
    meas_list = [{
        'id': m.id,
        'story': f"{m.lower_floor.floor_name} → {m.upper_floor.floor_name}",
        'measurement_time': m.measurement_time.isoformat(),
        'displacement_x': m.displacement_x,
        'displacement_y': m.displacement_y,
        'total_displacement': m.total_displacement,
        'drift_ratio': m.inter_story_drift_ratio,
        'drift_ratio_percent': m.inter_story_drift_ratio * 100,
    } for m in page_obj]
    
    return JsonResponse({
        'measurements': meas_list,
        'page': page,
        'total_pages': paginator.num_pages
    })


@login_required(login_url="login")
@require_http_methods(["GET"])
def drift_api_alerts(request):
    """API endpoint to get drift alerts"""
    status = request.GET.get('status')
    page = int(request.GET.get('page', 1))
    
    alerts = DriftAlert.objects.all()
    
    if status:
        alerts = alerts.filter(alert_status=status)
    
    paginator = Paginator(alerts.order_by('-alert_triggered_time'), 20)
    page_obj = paginator.get_page(page)
    
    alert_list = [{
        'id': a.id,
        'measurement': f"{a.measurement.lower_floor.floor_name} → {a.measurement.upper_floor.floor_name}",
        'status': a.alert_status,
        'exceeded_by': a.exceeded_by_percent,
        'triggered': a.alert_triggered_time.isoformat(),
        'resolved': a.resolved_time.isoformat() if a.resolved_time else None,
    } for a in page_obj]
    
    return JsonResponse({
        'alerts': alert_list,
        'page': page,
        'total_pages': paginator.num_pages
    })


@login_required(login_url="login")
@require_http_methods(["POST"])
def drift_api_add_measurement(request):
    """Record a new drift measurement"""
    try:
        data = json.loads(request.body)
        
        measurement = DriftMeasurement.objects.create(
            lower_floor_id=data['lower_floor_id'],
            upper_floor_id=data['upper_floor_id'],
            measurement_time=timezone.now(),
            displacement_x=float(data['displacement_x']),
            displacement_y=float(data['displacement_y']),
            total_displacement=float(data.get('total_displacement', 0)),
            inter_story_drift_ratio=float(data['inter_story_drift_ratio']),
            event_related_id=data.get('event_related_id')
        )
        
        return JsonResponse({'status': 'success', 'measurement_id': measurement.id})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@login_required(login_url="login")
@require_http_methods(["POST"])
def drift_api_create_alert(request):
    """Create a drift alert when threshold is exceeded"""
    try:
        data = json.loads(request.body)
        
        alert = DriftAlert.objects.create(
            measurement_id=data['measurement_id'],
            threshold_id=data['threshold_id'],
            alert_status=data.get('alert_status', 'warning'),
            exceeded_by_percent=float(data['exceeded_by_percent']),
            action_taken=data.get('action_taken', '')
        )
        
        return JsonResponse({'status': 'success', 'alert_id': alert.id})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@login_required(login_url="login")
@require_http_methods(["GET"])
def system_api_settings(request):
    """API endpoint to get system settings"""
    dashboard = request.GET.get('dashboard', 'shm')
    
    try:
        settings = SystemSettings.objects.get(dashboard_name=dashboard)
        return JsonResponse({
            'dashboard': settings.get_dashboard_name_display(),
            'sampling_rate': settings.sampling_rate,
            'units': settings.measurement_units,
            'maintenance_mode': settings.maintenance_mode,
            'alert_email': settings.alert_email,
        })
    except SystemSettings.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Settings not found'}, status=404)


@login_required(login_url="login")
@require_http_methods(["GET"])
def export_data(request):
    """Export data to CSV (example: events export)"""
    from django.http import HttpResponse
    import csv
    
    export_type = request.GET.get('type', 'events')
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="shm_{export_type}_{timezone.now().date()}.csv"'
    
    if export_type == 'events':
        writer = csv.writer(response)
        writer.writerow(['Event Type', 'Severity', 'Start Time', 'End Time', 'Peak Acceleration', 'Sensor'])
        
        for event in Event.objects.all():
            writer.writerow([
                event.event_type,
                event.severity,
                event.start_time,
                event.end_time,
                event.peak_acceleration,
                event.sensor.name
            ])
    
    elif export_type == 'drift':
        writer = csv.writer(response)
        writer.writerow(['Story', 'Measurement Time', 'Displacement X', 'Displacement Y', 'Drift Ratio %'])
        
        for meas in DriftMeasurement.objects.all():
            writer.writerow([
                f"{meas.lower_floor.floor_name} → {meas.upper_floor.floor_name}",
                meas.measurement_time,
                meas.displacement_x,
                meas.displacement_y,
                meas.inter_story_drift_ratio * 100
            ])
    
    return response
