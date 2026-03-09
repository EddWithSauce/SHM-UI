from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from core.models import (
    Sensor, SensorReading, Event, SHMTrend,
    ETABSBaseline, NaturalFrequency, FFTAnalysis, FrequencyComparison,
    FloorLevel, DriftMeasurement, DriftSafetyThreshold, DriftAlert,
    SystemSettings, Alert
)


class Command(BaseCommand):
    help = 'Initialize sample data for SHM, NFD, and Drift dashboards'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting sample data initialization...'))

        # ==================== SHM Sample Data ====================
        self.stdout.write('Creating SHM data...')
        
        # Create sensors
        sensor1, _ = Sensor.objects.get_or_create(
            name='Sensor-01-Base',
            defaults={
                'sensor_type': 'raspberry_shake',
                'location': 'Ground Floor',
                'is_active': True,
                'installation_date': timezone.now() - timedelta(days=90),
                'calibration_factor': 1.0
            }
        )
        
        sensor2, _ = Sensor.objects.get_or_create(
            name='Sensor-02-Mid',
            defaults={
                'sensor_type': 'accelerometer',
                'location': 'Floor 5',
                'is_active': True,
                'installation_date': timezone.now() - timedelta(days=90),
                'calibration_factor': 1.0
            }
        )
        
        sensor3, _ = Sensor.objects.get_or_create(
            name='Sensor-03-Top',
            defaults={
                'sensor_type': 'accelerometer',
                'location': 'Floor 10',
                'is_active': True,
                'installation_date': timezone.now() - timedelta(days=60),
                'calibration_factor': 1.0
            }
        )
        
        # Create recent sensor readings
        for i in range(50):
            timestamp = timezone.now() - timedelta(minutes=i*5)
            for sensor in [sensor1, sensor2, sensor3]:
                SensorReading.objects.get_or_create(
                    sensor=sensor,
                    timestamp=timestamp,
                    defaults={
                        'acceleration_x': 0.5 + (i % 3) * 0.1,
                        'acceleration_y': 0.3 + (i % 2) * 0.05,
                        'acceleration_z': 0.2 + (i % 4) * 0.08,
                        'magnitude': 0.8 + (i % 5) * 0.1,
                    }
                )
        
        # Create events
        for i in range(5):
            Event.objects.get_or_create(
                sensor_id=sensor1.id,
                start_time=timezone.now() - timedelta(days=i),
                defaults={
                    'event_type': ['earthquake', 'blast', 'footfall'][i % 3],
                    'severity': ['low', 'medium', 'high'][i % 3],
                    'end_time': timezone.now() - timedelta(days=i, minutes=-30),
                    'peak_acceleration': 1.5 + i * 0.2,
                    'description': f'Sample event {i+1}'
                }
            )
        
        self.stdout.write(self.style.SUCCESS('✓ SHM data created'))

        # ==================== NFD Sample Data ====================
        self.stdout.write('Creating NFD data...')
        
        # Create ETABS baseline
        baseline, _ = ETABSBaseline.objects.get_or_create(
            name='Building Model v1.0',
            defaults={
                'description': 'Analytical ETABS model of the building',
                'is_active': True
            }
        )
        
        # Create natural frequencies with analytical vs experimental
        freq_pairs = [
            {'mode': 1, 'freq': 2.15, 'damping': 0.05},
            {'mode': 2, 'freq': 5.42, 'damping': 0.04},
            {'mode': 3, 'freq': 8.87, 'damping': 0.035},
        ]
        
        for pair in freq_pairs:
            # Analytical (ETABS)
            NaturalFrequency.objects.get_or_create(
                baseline=baseline,
                mode_number=pair['mode'],
                frequency_source='analytical',
                defaults={
                    'frequency_hz': pair['freq'],
                    'damping_ratio': pair['damping'],
                    'notes': 'From ETABS analytical model'
                }
            )
            
            # Experimental (FFT measured)
            NaturalFrequency.objects.get_or_create(
                baseline=baseline,
                mode_number=pair['mode'],
                frequency_source='experimental',
                defaults={
                    'frequency_hz': pair['freq'] + (pair['mode'] % 2) * 0.05,
                    'damping_ratio': pair['damping'] + 0.005,
                    'notes': 'From FFT analysis of sensor data'
                }
            )
        
        # Create FFT analyses
        for i in range(3):
            FFTAnalysis.objects.get_or_create(
                sensor=sensor1,
                analysis_date=timezone.now() - timedelta(days=i),
                defaults={
                    'frequency_range_min': 0.1,
                    'frequency_range_max': 20.0,
                    'primary_frequency': 2.18 + i * 0.05,
                    'primary_amplitude': 0.8 - i * 0.05,
                    'analysis_notes': f'FFT analysis #{i+1}'
                }
            )
        
        self.stdout.write(self.style.SUCCESS('✓ NFD data created'))

        # ==================== Drift Sample Data ====================
        self.stdout.write('Creating Drift data...')
        
        # Create floor levels
        floors = []
        for floor_num in range(-1, 11):
            floor_name = {
                -1: 'Basement',
                0: 'Ground Floor',
            }.get(floor_num, f'Floor {floor_num}')
            
            floor, _ = FloorLevel.objects.get_or_create(
                floor_number=floor_num,
                defaults={
                    'floor_name': floor_name,
                    'height_above_ground': max(0, floor_num * 4.0)
                }
            )
            floors.append(floor)
        
        # Create safety thresholds
        for i in range(len(floors) - 1):
            lower = floors[i]
            upper = floors[i + 1]
            
            DriftSafetyThreshold.objects.get_or_create(
                lower_floor=lower,
                upper_floor=upper,
                defaults={
                    'max_inter_story_drift_ratio': 0.02,  # 2% per NSCP
                    'building_code': 'NSCP 2010',
                    'is_active': True
                }
            )
        
        # Create drift measurements
        for i in range(20):
            lower = floors[i % 9]
            upper = floors[i % 9 + 1]
            
            DriftMeasurement.objects.get_or_create(
                lower_floor=lower,
                upper_floor=upper,
                measurement_time=timezone.now() - timedelta(hours=i*2),
                defaults={
                    'displacement_x': 0.5 + (i % 3) * 0.1,
                    'displacement_y': 0.3 + (i % 2) * 0.05,
                    'total_displacement': 0.8 + (i % 4) * 0.1,
                    'inter_story_drift_ratio': 0.001 + (i % 5) * 0.0005,
                }
            )
        
        self.stdout.write(self.style.SUCCESS('✓ Drift data created'))

        # ==================== System Settings ====================
        self.stdout.write('Creating system settings...')
        
        for dashboard in ['shm', 'nfd', 'drift']:
            SystemSettings.objects.get_or_create(
                dashboard_name=dashboard,
                defaults={
                    'sampling_rate': 50,
                    'measurement_units': 'metric',
                    'alert_email': f'admin_{dashboard}@building-monitoring.com',
                    'maintenance_mode': False
                }
            )
        
        self.stdout.write(self.style.SUCCESS('✓ System settings created'))

        # ==================== Alerts ====================
        self.stdout.write('Creating alerts...')
        
        alert_types = ['sensor_offline', 'high_acceleration', 'frequency_shift', 'drift_exceeded', 'system_error']
        
        for i, alert_type in enumerate(alert_types):
            Alert.objects.get_or_create(
                alert_type=alert_type,
                defaults={
                    'is_active': True,
                    'threshold_value': 1.0 + i * 0.5,
                    'description': f'Alert for {alert_type.replace("_", " ")}'
                }
            )
        
        self.stdout.write(self.style.SUCCESS('✓ Alerts created'))

        self.stdout.write(self.style.SUCCESS('\n✅ Sample data initialization complete!'))
        self.stdout.write(self.style.WARNING('\nNext steps:'))
        self.stdout.write('1. Run: python manage.py makemigrations')
        self.stdout.write('2. Run: python manage.py migrate')
        self.stdout.write('3. Create a superuser: python manage.py createsuperuser')
        self.stdout.write('4. Start server: python manage.py runserver')
        self.stdout.write('5. Visit http://localhost:8000/admin/')
