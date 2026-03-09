from django.contrib import admin
from django.utils.html import format_html
from .models import (
    # SHM
    Sensor, SensorReading, Event, SHMTrend,
    # NFD
    ETABSBaseline, NaturalFrequency, FFTAnalysis, FrequencyComparison,
    # Drift
    FloorLevel, DriftMeasurement, DriftSafetyThreshold, DriftAlert,
    # System
    SystemSettings, Alert
)


# ==================== SHM Admin ====================
class SensorReadingInline(admin.TabularInline):
    model = SensorReading
    extra = 0
    readonly_fields = ('timestamp', 'created_at')
    fields = ('timestamp', 'acceleration_x', 'acceleration_y', 'acceleration_z', 'magnitude')
    ordering = ['-timestamp']
    can_delete = False


@admin.register(Sensor)
class SensorAdmin(admin.ModelAdmin):
    list_display = ('name', 'sensor_type', 'location', 'is_active_badge', 'last_reading', 'installation_date')
    list_filter = ('sensor_type', 'is_active', 'created_at')
    search_fields = ('name', 'location')
    readonly_fields = ('created_at', 'updated_at', 'last_reading')
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'sensor_type', 'location', 'is_active')
        }),
        ('Installation', {
            'fields': ('installation_date', 'calibration_factor')
        }),
        ('Status', {
            'fields': ('last_reading', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    inlines = [SensorReadingInline]

    def is_active_badge(self, obj):
        color = 'green' if obj.is_active else 'red'
        status = 'Active' if obj.is_active else 'Inactive'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, status
        )
    is_active_badge.short_description = 'Status'


@admin.register(SensorReading)
class SensorReadingAdmin(admin.ModelAdmin):
    list_display = ('sensor', 'timestamp', 'acceleration_x', 'acceleration_y', 'acceleration_z', 'magnitude')
    list_filter = ('sensor', 'timestamp', 'created_at')
    search_fields = ('sensor__name',)
    readonly_fields = ('created_at', 'updated_at', 'magnitude')
    date_hierarchy = 'timestamp'
    list_per_page = 100


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('event_type_display', 'sensor', 'severity_badge', 'start_time', 'peak_acceleration')
    list_filter = ('event_type', 'severity', 'start_time')
    search_fields = ('sensor__name', 'description')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'start_time'
    fieldsets = (
        ('Event Details', {
            'fields': ('sensor', 'event_type', 'severity')
        }),
        ('Timing', {
            'fields': ('start_time', 'end_time')
        }),
        ('Measurements', {
            'fields': ('peak_acceleration', 'description')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def event_type_display(self, obj):
        colors = {
            'earthquake': '#FF6B6B',
            'blast': '#FF8C00',
            'footfall': '#4ECDC4',
            'wind': '#45B7D1',
            'traffic': '#FFA07A',
        }
        color = colors.get(obj.event_type, '#95E1D3')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color, obj.get_event_type_display()
        )
    event_type_display.short_description = 'Type'

    def severity_badge(self, obj):
        colors = {'low': '#2ECC71', 'medium': '#F39C12', 'high': '#E74C3C', 'critical': '#8B0000'}
        color = colors.get(obj.severity, '#95E1D3')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color, obj.get_severity_display()
        )
    severity_badge.short_description = 'Severity'


@admin.register(SHMTrend)
class SHMTrendAdmin(admin.ModelAdmin):
    list_display = ('sensor', 'date', 'avg_acceleration', 'max_acceleration', 'event_count')
    list_filter = ('sensor', 'date')
    search_fields = ('sensor__name',)
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'date'


# ==================== NFD Admin ====================
@admin.register(ETABSBaseline)
class ETABSBaselineAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active_badge', 'uploaded_date')
    list_filter = ('is_active', 'uploaded_date')
    search_fields = ('name', 'description')
    readonly_fields = ('uploaded_date', 'created_at', 'updated_at')

    def is_active_badge(self, obj):
        color = 'green' if obj.is_active else 'gray'
        status = 'Active' if obj.is_active else 'Inactive'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, status
        )
    is_active_badge.short_description = 'Status'


@admin.register(NaturalFrequency)
class NaturalFrequencyAdmin(admin.ModelAdmin):
    list_display = ('mode_number', 'frequency_hz', 'damping_ratio', 'frequency_source', 'baseline', 'last_measured')
    list_filter = ('frequency_source', 'baseline', 'mode_number')
    readonly_fields = ('last_measured', 'created_at', 'updated_at')
    fieldsets = (
        ('Mode Information', {
            'fields': ('baseline', 'mode_number')
        }),
        ('Frequency & Damping', {
            'fields': ('frequency_hz', 'damping_ratio', 'frequency_source')
        }),
        ('Notes & History', {
            'fields': ('notes', 'last_measured', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(FFTAnalysis)
class FFTAnalysisAdmin(admin.ModelAdmin):
    list_display = ('sensor', 'analysis_date', 'primary_frequency', 'primary_amplitude', 'frequency_range')
    list_filter = ('sensor', 'analysis_date')
    search_fields = ('sensor__name',)
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'analysis_date'

    def frequency_range(self, obj):
        return f"{obj.frequency_range_min} - {obj.frequency_range_max} Hz"
    frequency_range.short_description = 'Frequency Range'


@admin.register(FrequencyComparison)
class FrequencyComparisonAdmin(admin.ModelAdmin):
    list_display = ('baseline_frequency', 'status_badge', 'frequency_diff', 'frequency_diff_percent', 'analysis')
    list_filter = ('status', 'analysis__analysis_date')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'analysis__analysis_date'

    def status_badge(self, obj):
        colors = {'normal': '#2ECC71', 'degraded': '#F39C12', 'alert': '#E74C3C'}
        color = colors.get(obj.status, '#95E1D3')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'


# ==================== Drift Admin ====================
@admin.register(FloorLevel)
class FloorLevelAdmin(admin.ModelAdmin):
    list_display = ('floor_number', 'floor_name', 'height_above_ground')
    list_filter = ('floor_number',)
    search_fields = ('floor_name',)
    ordering = ('floor_number',)


@admin.register(DriftMeasurement)
class DriftMeasurementAdmin(admin.ModelAdmin):
    list_display = ('story_info', 'measurement_time', 'total_displacement', 'inter_story_drift_ratio_display')
    list_filter = ('measurement_time', 'lower_floor', 'upper_floor', 'event_related')
    search_fields = ('lower_floor__floor_name', 'upper_floor__floor_name')
    readonly_fields = ('total_displacement', 'inter_story_drift_ratio', 'created_at', 'updated_at')
    date_hierarchy = 'measurement_time'
    fieldsets = (
        ('Story Information', {
            'fields': ('lower_floor', 'upper_floor')
        }),
        ('Measurements', {
            'fields': ('measurement_time', 'displacement_x', 'displacement_y', 'total_displacement', 'inter_story_drift_ratio')
        }),
        ('Event Link', {
            'fields': ('event_related',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def story_info(self, obj):
        return f"{obj.lower_floor.floor_name} → {obj.upper_floor.floor_name}"
    story_info.short_description = 'Story'

    def inter_story_drift_ratio_display(self, obj):
        ratio_percent = obj.inter_story_drift_ratio * 100
        return f"{ratio_percent:.2f}%"
    inter_story_drift_ratio_display.short_description = 'Drift Ratio'


@admin.register(DriftSafetyThreshold)
class DriftSafetyThresholdAdmin(admin.ModelAdmin):
    list_display = ('story_info', 'max_drift_percent', 'building_code', 'is_active_badge')
    list_filter = ('is_active', 'building_code')
    readonly_fields = ('created_at', 'updated_at') if hasattr(DriftSafetyThreshold, 'created_at') else ()

    def story_info(self, obj):
        return f"{obj.lower_floor.floor_name} → {obj.upper_floor.floor_name}"
    story_info.short_description = 'Story'

    def max_drift_percent(self, obj):
        return f"{obj.max_inter_story_drift_ratio * 100:.2f}%"
    max_drift_percent.short_description = 'Max Drift Ratio'

    def is_active_badge(self, obj):
        color = 'green' if obj.is_active else 'red'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, 'Active' if obj.is_active else 'Inactive'
        )
    is_active_badge.short_description = 'Status'


@admin.register(DriftAlert)
class DriftAlertAdmin(admin.ModelAdmin):
    list_display = ('measurement', 'alert_status_badge', 'exceeded_by_percent', 'alert_triggered_time', 'resolved_time')
    list_filter = ('alert_status', 'alert_triggered_time')
    search_fields = ('measurement__lower_floor__floor_name', 'measurement__upper_floor__floor_name')
    readonly_fields = ('alert_triggered_time', 'created_at', 'updated_at')
    date_hierarchy = 'alert_triggered_time'

    def alert_status_badge(self, obj):
        colors = {'warning': '#F39C12', 'critical': '#E74C3C', 'cleared': '#2ECC71'}
        color = colors.get(obj.alert_status, '#95E1D3')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color, obj.get_alert_status_display()
        )
    alert_status_badge.short_description = 'Status'


# ==================== System Admin ====================
@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    list_display = ('dashboard_name_display', 'sampling_rate', 'measurement_units', 'maintenance_mode_badge')
    list_filter = ('dashboard_name', 'maintenance_mode')
    readonly_fields = ('last_calibrated', 'created_at', 'updated_at') if hasattr(SystemSettings, 'created_at') else ('last_calibrated',)

    def dashboard_name_display(self, obj):
        return obj.get_dashboard_name_display()
    dashboard_name_display.short_description = 'Dashboard'

    def maintenance_mode_badge(self, obj):
        color = 'red' if obj.maintenance_mode else 'green'
        status = 'ON' if obj.maintenance_mode else 'OFF'
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color, status
        )
    maintenance_mode_badge.short_description = 'Maintenance Mode'


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ('alert_type_display', 'is_active_badge', 'threshold_value', 'created_at')
    list_filter = ('alert_type', 'is_active')
    search_fields = ('alert_type', 'description')
    readonly_fields = ('created_at', 'updated_at')

    def alert_type_display(self, obj):
        return obj.get_alert_type_display()
    alert_type_display.short_description = 'Alert Type'

    def is_active_badge(self, obj):
        color = 'green' if obj.is_active else 'gray'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, 'Active' if obj.is_active else 'Inactive'
        )
    is_active_badge.short_description = 'Active'
