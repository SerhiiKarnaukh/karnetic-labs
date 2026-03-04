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

    def test_one_stop_note_includes_optimal_window_and_state(self):
        options = self.engine.calculate_strategies(**self._base_input(current_lap=10))
        one_stop = next(option for option in options if option.name == 'one_stop')
        self.assertIn('Optimal window L12-18', one_stop.notes)
        self.assertIn('(before_window)', one_stop.notes)

    def test_one_stop_from_inside_window_selects_valid_future_window_lap(self):
        options = self.engine.calculate_strategies(**self._base_input(current_lap=14))
        one_stop = next(option for option in options if option.name == 'one_stop')
        pit_lap = one_stop.pit_stops[0].lap
        self.assertGreaterEqual(pit_lap, 15)
        self.assertLessEqual(pit_lap, 18)
        self.assertIn('(in_window)', one_stop.notes)

    def test_one_stop_after_window_pits_immediately_next_lap(self):
        options = self.engine.calculate_strategies(**self._base_input(current_lap=22))
        one_stop = next(option for option in options if option.name == 'one_stop')
        self.assertEqual(one_stop.pit_stops[0].lap, 23)
        self.assertIn('(past_window)', one_stop.notes)

    def test_generates_two_stop_when_more_than_twenty_laps_remaining(self):
        options = self.engine.calculate_strategies(**self._base_input(current_lap=20))
        names = [option.name for option in options]
        self.assertIn('two_stop', names)

    def test_two_stop_has_two_valid_future_stop_laps(self):
        options = self.engine.calculate_strategies(**self._base_input(current_lap=20))
        two_stop = next(option for option in options if option.name == 'two_stop')
        first = two_stop.pit_stops[0].lap
        second = two_stop.pit_stops[1].lap
        self.assertGreater(first, 20)
        self.assertGreater(second, first)
        self.assertLessEqual(second, 56)

    def test_two_stop_note_contains_third_split_summary(self):
        options = self.engine.calculate_strategies(**self._base_input(current_lap=20))
        two_stop = next(option for option in options if option.name == 'two_stop')
        self.assertIn('Third split stints:', two_stop.notes)
        self.assertIn('pits on L', two_stop.notes)

    def test_two_stop_skipped_when_twenty_or_fewer_laps_remaining(self):
        options = self.engine.calculate_strategies(**self._base_input(current_lap=38))
        names = [option.name for option in options]
        self.assertNotIn('two_stop', names)

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

    def test_skips_one_stop_when_only_one_lap_remains(self):
        options = self.engine.calculate_strategies(
            **self._base_input(current_lap=56, total_laps=57),
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

    def test_detect_optimal_window_before(self):
        window = self.engine._detect_optimal_window(COMPOUND_SOFT, current_lap=8)
        self.assertEqual(window['state'], 'before_window')
        self.assertEqual(window['laps_to_open'], 4)

    def test_detect_optimal_window_inside(self):
        window = self.engine._detect_optimal_window(COMPOUND_SOFT, current_lap=12)
        self.assertEqual(window['state'], 'in_window')
        self.assertEqual(window['laps_to_open'], 0)

    def test_detect_optimal_window_after(self):
        window = self.engine._detect_optimal_window(COMPOUND_SOFT, current_lap=20)
        self.assertEqual(window['state'], 'past_window')

    def test_one_stop_candidates_before_window(self):
        candidates = self.engine._one_stop_candidates(
            current_lap=10,
            total_laps=57,
            compound=COMPOUND_SOFT,
        )
        self.assertEqual(candidates, [12, 13, 14, 15, 16, 17, 18])

    def test_one_stop_candidates_blocked_by_24_hour_rule(self):
        candidates = self.engine._one_stop_candidates(
            current_lap=11,
            total_laps=57,
            compound=COMPOUND_SOFT,
        )
        self.assertEqual(candidates, [])

    def test_two_stop_split_laps_even_thirds(self):
        first, second = self.engine._two_stop_split_laps(current_lap=20, total_laps=57)
        self.assertEqual(first, 33)
        self.assertEqual(second, 46)

    def test_two_stop_split_stints_differ_by_at_most_one_lap(self):
        current_lap = 21
        total_laps = 57
        first, second = self.engine._two_stop_split_laps(current_lap, total_laps)
        stints = [
            first - current_lap,
            second - first,
            total_laps - second + 1,
        ]
        self.assertLessEqual(max(stints) - min(stints), 1)

    def test_two_stop_candidates_are_unique_and_ordered(self):
        candidates = self.engine._two_stop_candidates(
            split_first=33,
            split_second=46,
            current_lap=20,
            total_laps=57,
        )
        self.assertEqual(candidates, sorted(set(candidates)))

    def test_two_stop_candidates_respect_lap_bounds(self):
        candidates = self.engine._two_stop_candidates(
            split_first=33,
            split_second=46,
            current_lap=20,
            total_laps=57,
        )
        for first, second in candidates:
            self.assertGreater(first, 20)
            self.assertGreater(second, first)
            self.assertLessEqual(second, 56)

    def test_best_two_stop_plan_returns_valid_plan(self):
        plan = self.engine._best_two_stop_plan(
            current_lap=20,
            total_laps=57,
            current_compound=COMPOUND_SOFT,
            tyre_age=8,
            base_lap_time=90.0,
        )
        self.assertIsNotNone(plan)
        first, second, stops = plan
        self.assertEqual(len(stops), 2)
        self.assertEqual(stops[0].lap, first)
        self.assertEqual(stops[1].lap, second)
