"""Tests for strategy calculation logic and edge cases."""

from django.test import SimpleTestCase

from f1_pitwall.constants import (
    COMPOUND_HARD,
    COMPOUND_MEDIUM,
    COMPOUND_SOFT,
    COMPOUND_WET,
)
from f1_pitwall.services.strategy_engine import StrategyEngine, StrategyStop


class StrategyEnginePredictLapTimeTest(SimpleTestCase):
    """Tire degradation model verification."""

    def setUp(self):
        self.engine = StrategyEngine()

    def test_predict_lap_time_before_cliff(self):
        lap = self.engine.predict_lap_time(COMPOUND_SOFT, 10, 90.0)
        self.assertAlmostEqual(lap, 90.8, places=3)

    def test_predict_lap_time_after_cliff_uses_accelerated_degradation(self):
        lap = self.engine.predict_lap_time(COMPOUND_SOFT, 20, 90.0)
        self.assertAlmostEqual(lap, 91.92, places=3)

    def test_predict_lap_time_raises_for_unknown_compound(self):
        with self.assertRaises(ValueError):
            self.engine.predict_lap_time('ULTRASOFT', 5, 90.0)


class StrategyEngineStrategyGenerationTest(SimpleTestCase):
    """Strategy generation and ranking behavior."""

    def setUp(self):
        self.engine = StrategyEngine()

    def _base_input(self, **overrides):
        data = {
            'current_lap': 12,
            'total_laps': 57,
            'current_compound': COMPOUND_SOFT,
            'tyre_age': 8,
            'base_lap_time': 90.0,
            'weather_forecast': {'rain_probability': 0.2, 'rain_eta_laps': 8},
            'gap_ahead': 24.0,
            'gap_behind': 2.0,
        }
        data.update(overrides)
        return data

    def test_generates_one_stop_option(self):
        options = self.engine.calculate_strategies(**self._base_input())
        names = [option.name for option in options]
        self.assertIn('one_stop', names)

    def test_generates_two_stop_when_more_than_twenty_laps_remaining(self):
        options = self.engine.calculate_strategies(**self._base_input(current_lap=20))
        names = [option.name for option in options]
        self.assertIn('two_stop', names)

    def test_generates_undercut_when_gap_ahead_within_pit_loss(self):
        options = self.engine.calculate_strategies(**self._base_input(gap_ahead=10.0))
        names = [option.name for option in options]
        self.assertIn('undercut', names)

    def test_generates_wet_switch_for_high_rain_probability(self):
        options = self.engine.calculate_strategies(
            **self._base_input(weather_forecast={'rain_probability': 0.8, 'rain_eta_laps': 2}),
        )
        wet = next((option for option in options if option.name == 'wet_switch'), None)
        self.assertIsNotNone(wet)
        self.assertEqual(wet.pit_stops[0].compound, COMPOUND_WET)

    def test_skips_one_stop_when_window_opens_in_less_than_two_laps(self):
        options = self.engine.calculate_strategies(
            **self._base_input(current_lap=11, current_compound=COMPOUND_SOFT),
        )
        names = [option.name for option in options]
        self.assertNotIn('one_stop', names)

    def test_calculate_undercut_window(self):
        self.assertTrue(self.engine.calculate_undercut_window(10.0))
        self.assertFalse(self.engine.calculate_undercut_window(30.0))

    def test_result_is_sorted_by_total_time(self):
        options = self.engine.calculate_strategies(**self._base_input(gap_ahead=10.0))
        total_times = [option.total_time for option in options]
        self.assertEqual(total_times, sorted(total_times))

    def test_simulate_race_time_adds_pit_time_loss(self):
        no_stop = self.engine.simulate_race_time(
            start_lap=50,
            total_laps=52,
            stops=(),
            base_lap_time=90.0,
            current_compound=COMPOUND_MEDIUM,
            current_tyre_age=3,
        )
        one_stop = self.engine.simulate_race_time(
            start_lap=50,
            total_laps=52,
            stops=(StrategyStop(lap=51, compound=COMPOUND_HARD),),
            base_lap_time=90.0,
            current_compound=COMPOUND_MEDIUM,
            current_tyre_age=3,
        )
        self.assertGreater(one_stop, no_stop)
