"""Tests for model creation and constraints across all F1 Pit Wall models."""

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone

from f1_pitwall.models import (
    APIAuditLog,
    Driver,
    LapData,
    PitStop,
    RaceControlMessage,
    Session,
    Stint,
    TelemetrySnapshot,
    ThreatEvent,
    WeatherData,
)

User = get_user_model()


def _create_session(**overrides):
    """Helper: create a Session with sensible defaults."""
    defaults = {
        'session_key': 9158,
        'meeting_key': 1219,
        'session_name': 'Race',
        'session_type': 'race',
        'circuit_name': 'Bahrain International Circuit',
        'circuit_short_name': 'Bahrain',
        'country_name': 'Bahrain',
        'country_code': 'BHR',
        'date_start': '2024-03-02T15:00:00Z',
        'year': 2024,
    }
    defaults.update(overrides)
    return Session.objects.create(**defaults)


def _create_driver(**overrides):
    """Helper: create a Driver with sensible defaults."""
    defaults = {
        'driver_number': 1,
        'full_name': 'Max VERSTAPPEN',
        'name_acronym': 'VER',
        'team_name': 'Red Bull Racing',
        'team_colour': '#3671C6',
    }
    defaults.update(overrides)
    return Driver.objects.create(**defaults)


# -- Session model -----------------------------------------------------------

class SessionCreationTest(TestCase):
    """Test Session model creation and constraints."""

    def test_create_session_with_required_fields(self):
        session = _create_session()
        self.assertEqual(session.session_key, 9158)
        self.assertEqual(session.session_name, 'Race')
        self.assertEqual(session.session_type, 'race')
        self.assertFalse(session.is_live)
        self.assertIsNotNone(session.id)

    def test_session_str_representation(self):
        session = _create_session()
        self.assertEqual(str(session), '2024 Bahrain - Race')

    def test_session_key_unique_constraint(self):
        _create_session(session_key=100)
        with self.assertRaises(IntegrityError):
            _create_session(session_key=100)

    def test_date_end_nullable(self):
        session = _create_session(date_end=None)
        self.assertIsNone(session.date_end)

    def test_ordering_by_date_desc(self):
        s1 = _create_session(session_key=100, date_start='2024-03-02T15:00:00Z')
        s2 = _create_session(session_key=101, date_start='2024-06-10T14:00:00Z')
        sessions = list(Session.objects.all())
        self.assertEqual(sessions[0].pk, s2.pk)
        self.assertEqual(sessions[1].pk, s1.pk)

    def test_auto_timestamps(self):
        session = _create_session()
        self.assertIsNotNone(session.created_at)
        self.assertIsNotNone(session.updated_at)

    def test_uuid_primary_key(self):
        session = _create_session()
        self.assertEqual(len(str(session.id)), 36)


# -- Driver model ------------------------------------------------------------

class DriverCreationTest(TestCase):
    """Test Driver model creation and constraints."""

    def test_create_driver_with_required_fields(self):
        driver = _create_driver()
        self.assertEqual(driver.driver_number, 1)
        self.assertEqual(driver.full_name, 'Max VERSTAPPEN')
        self.assertTrue(driver.is_active)

    def test_driver_str_representation(self):
        driver = _create_driver()
        self.assertEqual(str(driver), '#1 VER (Red Bull Racing)')

    def test_driver_number_unique_constraint(self):
        _create_driver(driver_number=1)
        with self.assertRaises(IntegrityError):
            _create_driver(driver_number=1)

    def test_optional_fields_default_to_empty(self):
        driver = _create_driver()
        self.assertEqual(driver.headshot_url, '')
        self.assertEqual(driver.country_code, '')

    def test_ordering_by_driver_number(self):
        d44 = _create_driver(driver_number=44, name_acronym='HAM')
        d1 = _create_driver(driver_number=1, name_acronym='VER')
        drivers = list(Driver.objects.all())
        self.assertEqual(drivers[0].pk, d1.pk)
        self.assertEqual(drivers[1].pk, d44.pk)


# -- TelemetrySnapshot model -------------------------------------------------

class TelemetrySnapshotCreationTest(TestCase):
    """Test TelemetrySnapshot model creation."""

    def setUp(self):
        self.session = _create_session()
        self.driver = _create_driver()

    def test_create_telemetry_snapshot(self):
        snap = TelemetrySnapshot.objects.create(
            session=self.session,
            driver=self.driver,
            timestamp=timezone.now(),
            speed=320,
            rpm=12500,
            throttle=100,
            brake=0,
            gear=8,
            drs=10,
        )
        self.assertEqual(snap.speed, 320)
        self.assertEqual(snap.gear, 8)
        self.assertIsNotNone(snap.created_at)

    def test_str_representation(self):
        snap = TelemetrySnapshot.objects.create(
            session=self.session,
            driver=self.driver,
            timestamp=timezone.now(),
            speed=280,
            rpm=11000,
            throttle=85,
            brake=0,
            gear=7,
            drs=0,
        )
        self.assertIn('280 km/h', str(snap))

    def test_cascade_delete_on_session(self):
        TelemetrySnapshot.objects.create(
            session=self.session,
            driver=self.driver,
            timestamp=timezone.now(),
            speed=300, rpm=12000, throttle=90,
            brake=0, gear=7, drs=0,
        )
        self.session.delete()
        self.assertEqual(TelemetrySnapshot.objects.count(), 0)

    def test_cascade_delete_on_driver(self):
        TelemetrySnapshot.objects.create(
            session=self.session,
            driver=self.driver,
            timestamp=timezone.now(),
            speed=300, rpm=12000, throttle=90,
            brake=0, gear=7, drs=0,
        )
        self.driver.delete()
        self.assertEqual(TelemetrySnapshot.objects.count(), 0)


# -- LapData model -----------------------------------------------------------

class LapDataCreationTest(TestCase):
    """Test LapData model creation and unique constraint."""

    def setUp(self):
        self.session = _create_session()
        self.driver = _create_driver()

    def test_create_lap_with_all_fields(self):
        lap = LapData.objects.create(
            session=self.session,
            driver=self.driver,
            lap_number=1,
            lap_duration=90.123,
            sector_1=28.5,
            sector_2=35.8,
            sector_3=25.823,
            speed_trap=320.5,
            is_pit_out_lap=True,
        )
        self.assertEqual(lap.lap_number, 1)
        self.assertEqual(lap.lap_duration, 90.123)
        self.assertTrue(lap.is_pit_out_lap)

    def test_create_lap_with_nullable_fields(self):
        lap = LapData.objects.create(
            session=self.session,
            driver=self.driver,
            lap_number=1,
        )
        self.assertIsNone(lap.lap_duration)
        self.assertIsNone(lap.sector_1)
        self.assertIsNone(lap.speed_trap)

    def test_unique_constraint_session_driver_lap(self):
        LapData.objects.create(
            session=self.session,
            driver=self.driver,
            lap_number=1,
        )
        with self.assertRaises(IntegrityError):
            LapData.objects.create(
                session=self.session,
                driver=self.driver,
                lap_number=1,
            )

    def test_str_representation(self):
        lap = LapData.objects.create(
            session=self.session,
            driver=self.driver,
            lap_number=5,
            lap_duration=91.456,
        )
        self.assertIn('Lap 5', str(lap))
        self.assertIn('91.456s', str(lap))

    def test_str_for_incomplete_lap(self):
        lap = LapData.objects.create(
            session=self.session,
            driver=self.driver,
            lap_number=1,
        )
        self.assertIn('N/A', str(lap))

    def test_ordering_by_lap_number(self):
        LapData.objects.create(
            session=self.session, driver=self.driver, lap_number=3,
        )
        LapData.objects.create(
            session=self.session, driver=self.driver, lap_number=1,
        )
        laps = list(LapData.objects.all())
        self.assertEqual(laps[0].lap_number, 1)
        self.assertEqual(laps[1].lap_number, 3)


# -- PitStop model -----------------------------------------------------------

class PitStopCreationTest(TestCase):
    """Test PitStop model creation."""

    def setUp(self):
        self.session = _create_session()
        self.driver = _create_driver()

    def test_create_pit_stop(self):
        pit = PitStop.objects.create(
            session=self.session,
            driver=self.driver,
            lap_number=15,
            pit_duration=2.5,
            timestamp=timezone.now(),
        )
        self.assertEqual(pit.lap_number, 15)
        self.assertEqual(pit.pit_duration, 2.5)

    def test_str_representation(self):
        pit = PitStop.objects.create(
            session=self.session,
            driver=self.driver,
            lap_number=22,
            pit_duration=3.1,
            timestamp=timezone.now(),
        )
        self.assertIn('lap 22', str(pit))
        self.assertIn('3.1s', str(pit))

    def test_ordering_by_timestamp(self):
        now = timezone.now()
        p2 = PitStop.objects.create(
            session=self.session, driver=self.driver,
            lap_number=30, pit_duration=2.8,
            timestamp=now + timezone.timedelta(hours=1),
        )
        p1 = PitStop.objects.create(
            session=self.session, driver=self.driver,
            lap_number=15, pit_duration=2.5,
            timestamp=now,
        )
        stops = list(PitStop.objects.all())
        self.assertEqual(stops[0].pk, p1.pk)
        self.assertEqual(stops[1].pk, p2.pk)


# -- Stint model -------------------------------------------------------------

class StintCreationTest(TestCase):
    """Test Stint model creation."""

    def setUp(self):
        self.session = _create_session()
        self.driver = _create_driver()

    def test_create_stint(self):
        stint = Stint.objects.create(
            session=self.session,
            driver=self.driver,
            stint_number=1,
            compound='SOFT',
            tyre_age_at_start=0,
            lap_start=1,
            lap_end=15,
        )
        self.assertEqual(stint.stint_number, 1)
        self.assertEqual(stint.compound, 'SOFT')
        self.assertEqual(stint.lap_end, 15)

    def test_create_stint_in_progress(self):
        stint = Stint.objects.create(
            session=self.session,
            driver=self.driver,
            stint_number=2,
            compound='MEDIUM',
            lap_start=16,
        )
        self.assertIsNone(stint.lap_end)

    def test_str_representation(self):
        stint = Stint.objects.create(
            session=self.session,
            driver=self.driver,
            stint_number=1,
            compound='HARD',
            lap_start=1,
            lap_end=25,
        )
        self.assertIn('Stint 1', str(stint))
        self.assertIn('HARD', str(stint))
        self.assertIn('L1-25', str(stint))

    def test_str_for_in_progress_stint(self):
        stint = Stint.objects.create(
            session=self.session,
            driver=self.driver,
            stint_number=2,
            compound='MEDIUM',
            lap_start=26,
        )
        self.assertIn('L26-?', str(stint))

    def test_ordering_by_stint_number(self):
        Stint.objects.create(
            session=self.session, driver=self.driver,
            stint_number=2, compound='MEDIUM', lap_start=16,
        )
        Stint.objects.create(
            session=self.session, driver=self.driver,
            stint_number=1, compound='SOFT', lap_start=1, lap_end=15,
        )
        stints = list(Stint.objects.all())
        self.assertEqual(stints[0].stint_number, 1)
        self.assertEqual(stints[1].stint_number, 2)


# -- WeatherData model -------------------------------------------------------

class WeatherDataCreationTest(TestCase):
    """Test WeatherData model creation."""

    def setUp(self):
        self.session = _create_session()

    def test_create_weather_data(self):
        weather = WeatherData.objects.create(
            session=self.session,
            timestamp=timezone.now(),
            air_temperature=28.5,
            track_temperature=42.3,
            humidity=55.0,
            wind_speed=3.2,
            wind_direction=180,
            rainfall=False,
            pressure=1013.25,
        )
        self.assertEqual(weather.air_temperature, 28.5)
        self.assertFalse(weather.rainfall)

    def test_create_weather_with_rainfall(self):
        weather = WeatherData.objects.create(
            session=self.session,
            timestamp=timezone.now(),
            air_temperature=20.0,
            track_temperature=22.5,
            humidity=92.0,
            wind_speed=8.0,
            wind_direction=270,
            rainfall=True,
        )
        self.assertTrue(weather.rainfall)

    def test_pressure_nullable(self):
        weather = WeatherData.objects.create(
            session=self.session,
            timestamp=timezone.now(),
            air_temperature=25.0,
            track_temperature=35.0,
            humidity=60.0,
            wind_speed=4.0,
            wind_direction=90,
        )
        self.assertIsNone(weather.pressure)

    def test_str_representation(self):
        weather = WeatherData.objects.create(
            session=self.session,
            timestamp=timezone.now(),
            air_temperature=30.0,
            track_temperature=45.0,
            humidity=40.0,
            wind_speed=2.0,
            wind_direction=0,
            rainfall=True,
        )
        self.assertIn('30.0°C', str(weather))
        self.assertIn('RAIN', str(weather))

    def test_str_without_rain(self):
        weather = WeatherData.objects.create(
            session=self.session,
            timestamp=timezone.now(),
            air_temperature=25.0,
            track_temperature=35.0,
            humidity=50.0,
            wind_speed=3.0,
            wind_direction=90,
            rainfall=False,
        )
        self.assertNotIn('RAIN', str(weather))


# -- RaceControlMessage model ------------------------------------------------

class RaceControlMessageCreationTest(TestCase):
    """Test RaceControlMessage model creation."""

    def setUp(self):
        self.session = _create_session()

    def test_create_flag_message(self):
        msg = RaceControlMessage.objects.create(
            session=self.session,
            timestamp=timezone.now(),
            category='Flag',
            message='YELLOW FLAG in Turn 4',
            flag='YELLOW',
            sector=2,
        )
        self.assertEqual(msg.flag, 'YELLOW')
        self.assertEqual(msg.sector, 2)
        self.assertIsNone(msg.driver_number)

    def test_create_penalty_message(self):
        msg = RaceControlMessage.objects.create(
            session=self.session,
            timestamp=timezone.now(),
            category='Penalty',
            message='5 second time penalty for car 44',
            driver_number=44,
            lap_number=32,
        )
        self.assertEqual(msg.driver_number, 44)
        self.assertEqual(msg.lap_number, 32)

    def test_str_representation_with_flag(self):
        msg = RaceControlMessage.objects.create(
            session=self.session,
            timestamp=timezone.now(),
            category='Flag',
            message='RED FLAG - Session stopped',
            flag='RED',
        )
        self.assertIn('[RED]', str(msg))
        self.assertIn('RED FLAG', str(msg))

    def test_str_representation_without_flag(self):
        msg = RaceControlMessage.objects.create(
            session=self.session,
            timestamp=timezone.now(),
            category='SafetyCar',
            message='SAFETY CAR DEPLOYED',
        )
        self.assertNotIn('[', str(msg))
        self.assertIn('SAFETY CAR DEPLOYED', str(msg))

    def test_optional_fields_nullable(self):
        msg = RaceControlMessage.objects.create(
            session=self.session,
            timestamp=timezone.now(),
            category='Other',
            message='Track clear',
        )
        self.assertIsNone(msg.driver_number)
        self.assertIsNone(msg.lap_number)
        self.assertIsNone(msg.sector)
        self.assertEqual(msg.flag, '')


# -- APIAuditLog model -------------------------------------------------------

class APIAuditLogCreationTest(TestCase):
    """Test APIAuditLog model creation."""

    def test_create_audit_log_anonymous(self):
        log = APIAuditLog.objects.create(
            method='GET',
            path='/f1/api/sessions/',
            ip_address='192.168.1.1',
            user_agent='Mozilla/5.0',
            status_code=200,
            response_time_ms=45.3,
        )
        self.assertIsNone(log.user)
        self.assertFalse(log.is_suspicious)
        self.assertEqual(log.threat_indicators, [])

    def test_create_audit_log_with_user(self):
        user = User.objects.create_user(
            first_name='Test', last_name='User',
            username='audituser', email='audit@test.com',
            password='testpass123',
        )
        log = APIAuditLog.objects.create(
            user=user,
            method='POST',
            path='/f1/api/strategy/9158/calculate/',
            ip_address='10.0.0.1',
            status_code=200,
            response_time_ms=120.5,
        )
        self.assertEqual(log.user, user)

    def test_create_suspicious_log(self):
        log = APIAuditLog.objects.create(
            method='GET',
            path="/f1/api/sessions/?id=1' OR 1=1--",
            ip_address='192.168.1.100',
            user_agent='sqlmap/1.7',
            status_code=403,
            response_time_ms=5.0,
            is_suspicious=True,
            threat_indicators=['SQL_INJECTION', 'SUSPICIOUS_UA'],
        )
        self.assertTrue(log.is_suspicious)
        self.assertEqual(len(log.threat_indicators), 2)

    def test_str_representation(self):
        log = APIAuditLog.objects.create(
            method='GET',
            path='/f1/api/sessions/',
            ip_address='10.0.0.1',
            status_code=200,
            response_time_ms=30.0,
        )
        self.assertIn('GET', str(log))
        self.assertIn('/f1/api/sessions/', str(log))
        self.assertIn('200', str(log))

    def test_str_suspicious_marker(self):
        log = APIAuditLog.objects.create(
            method='GET',
            path='/f1/api/sessions/',
            ip_address='10.0.0.1',
            status_code=403,
            response_time_ms=5.0,
            is_suspicious=True,
        )
        self.assertIn('[!]', str(log))

    def test_ordering_by_timestamp_desc(self):
        log1 = APIAuditLog.objects.create(
            method='GET', path='/a', ip_address='10.0.0.1',
            status_code=200, response_time_ms=10.0,
        )
        log2 = APIAuditLog.objects.create(
            method='GET', path='/b', ip_address='10.0.0.1',
            status_code=200, response_time_ms=10.0,
        )
        logs = list(APIAuditLog.objects.all())
        self.assertEqual(logs[0].pk, log2.pk)
        self.assertEqual(logs[1].pk, log1.pk)

    def test_user_set_null_on_delete(self):
        user = User.objects.create_user(
            first_name='Del', last_name='User',
            username='deluser', email='del@test.com',
            password='testpass123',
        )
        log = APIAuditLog.objects.create(
            user=user,
            method='GET', path='/f1/api/sessions/',
            ip_address='10.0.0.1', status_code=200,
            response_time_ms=10.0,
        )
        user.delete()
        log.refresh_from_db()
        self.assertIsNone(log.user)


# -- ThreatEvent model -------------------------------------------------------

class ThreatEventCreationTest(TestCase):
    """Test ThreatEvent model creation."""

    def test_create_threat_event(self):
        threat = ThreatEvent.objects.create(
            threat_type='SQL_INJECTION',
            severity='CRITICAL',
            source_ip='192.168.1.100',
            description='Detected UNION SELECT in query params',
            raw_request={'path': '/f1/api/sessions/', 'params': 'redacted'},
        )
        self.assertEqual(threat.threat_type, 'SQL_INJECTION')
        self.assertEqual(threat.severity, 'CRITICAL')
        self.assertFalse(threat.is_resolved)
        self.assertIsNone(threat.resolved_at)

    def test_resolve_threat(self):
        threat = ThreatEvent.objects.create(
            threat_type='BRUTE_FORCE',
            severity='MEDIUM',
            source_ip='10.0.0.50',
            description='15 failed auth attempts',
            raw_request={},
        )
        now = timezone.now()
        threat.is_resolved = True
        threat.resolved_at = now
        threat.resolution_notes = 'False positive - internal testing'
        threat.save()

        threat.refresh_from_db()
        self.assertTrue(threat.is_resolved)
        self.assertEqual(
            threat.resolution_notes, 'False positive - internal testing',
        )

    def test_str_representation(self):
        threat = ThreatEvent.objects.create(
            threat_type='XSS',
            severity='HIGH',
            source_ip='172.16.0.1',
            description='Script tag detected',
            raw_request={},
        )
        self.assertIn('[HIGH]', str(threat))
        self.assertIn('XSS', str(threat))
        self.assertIn('172.16.0.1', str(threat))

    def test_str_resolved_marker(self):
        threat = ThreatEvent.objects.create(
            threat_type='RATE_LIMIT',
            severity='LOW',
            source_ip='10.0.0.1',
            description='Rate limit exceeded',
            raw_request={},
            is_resolved=True,
        )
        self.assertIn('[resolved]', str(threat))

    def test_ordering_by_timestamp_desc(self):
        t1 = ThreatEvent.objects.create(
            threat_type='XSS', severity='HIGH',
            source_ip='10.0.0.1', description='First',
            raw_request={},
        )
        t2 = ThreatEvent.objects.create(
            threat_type='XSS', severity='HIGH',
            source_ip='10.0.0.2', description='Second',
            raw_request={},
        )
        threats = list(ThreatEvent.objects.all())
        self.assertEqual(threats[0].pk, t2.pk)
        self.assertEqual(threats[1].pk, t1.pk)


# -- Cross-model relationship tests -----------------------------------------

class ModelRelationshipTest(TestCase):
    """Test foreign key relationships and cascade behavior."""

    def setUp(self):
        self.session = _create_session()
        self.driver = _create_driver()

    def test_session_related_name_laps(self):
        LapData.objects.create(
            session=self.session, driver=self.driver, lap_number=1,
        )
        self.assertEqual(self.session.laps.count(), 1)

    def test_session_related_name_pit_stops(self):
        PitStop.objects.create(
            session=self.session, driver=self.driver,
            lap_number=15, pit_duration=2.5, timestamp=timezone.now(),
        )
        self.assertEqual(self.session.pit_stops.count(), 1)

    def test_session_related_name_stints(self):
        Stint.objects.create(
            session=self.session, driver=self.driver,
            stint_number=1, compound='SOFT', lap_start=1,
        )
        self.assertEqual(self.session.stints.count(), 1)

    def test_session_related_name_weather(self):
        WeatherData.objects.create(
            session=self.session, timestamp=timezone.now(),
            air_temperature=28.0, track_temperature=40.0,
            humidity=50.0, wind_speed=3.0, wind_direction=180,
        )
        self.assertEqual(self.session.weather.count(), 1)

    def test_session_related_name_rc_messages(self):
        RaceControlMessage.objects.create(
            session=self.session, timestamp=timezone.now(),
            category='Flag', message='Green',
        )
        self.assertEqual(self.session.rc_messages.count(), 1)

    def test_session_related_name_telemetry(self):
        TelemetrySnapshot.objects.create(
            session=self.session, driver=self.driver,
            timestamp=timezone.now(),
            speed=300, rpm=12000, throttle=90,
            brake=0, gear=7, drs=0,
        )
        self.assertEqual(self.session.telemetry.count(), 1)

    def test_driver_related_name_laps(self):
        LapData.objects.create(
            session=self.session, driver=self.driver, lap_number=1,
        )
        self.assertEqual(self.driver.laps.count(), 1)

    def test_driver_related_name_pit_stops(self):
        PitStop.objects.create(
            session=self.session, driver=self.driver,
            lap_number=15, pit_duration=2.5, timestamp=timezone.now(),
        )
        self.assertEqual(self.driver.pit_stops.count(), 1)

    def test_cascade_session_deletes_all_children(self):
        now = timezone.now()
        LapData.objects.create(
            session=self.session, driver=self.driver, lap_number=1,
        )
        PitStop.objects.create(
            session=self.session, driver=self.driver,
            lap_number=15, pit_duration=2.5, timestamp=now,
        )
        Stint.objects.create(
            session=self.session, driver=self.driver,
            stint_number=1, compound='SOFT', lap_start=1,
        )
        WeatherData.objects.create(
            session=self.session, timestamp=now,
            air_temperature=28.0, track_temperature=40.0,
            humidity=50.0, wind_speed=3.0, wind_direction=180,
        )
        RaceControlMessage.objects.create(
            session=self.session, timestamp=now,
            category='Flag', message='Green',
        )
        TelemetrySnapshot.objects.create(
            session=self.session, driver=self.driver,
            timestamp=now,
            speed=300, rpm=12000, throttle=90,
            brake=0, gear=7, drs=0,
        )

        self.session.delete()

        self.assertEqual(LapData.objects.count(), 0)
        self.assertEqual(PitStop.objects.count(), 0)
        self.assertEqual(Stint.objects.count(), 0)
        self.assertEqual(WeatherData.objects.count(), 0)
        self.assertEqual(RaceControlMessage.objects.count(), 0)
        self.assertEqual(TelemetrySnapshot.objects.count(), 0)
