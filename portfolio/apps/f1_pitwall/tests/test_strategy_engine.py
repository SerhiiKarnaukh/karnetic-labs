"""Tests for strategy calculation logic and edge cases."""

from django.test import SimpleTestCase

from f1_pitwall.constants import (
    COMPOUND_HARD,
    COMPOUND_INTERMEDIATE,
    COMPOUND_MEDIUM,
    COMPOUND_SOFT,
    COMPOUND_WET,
)
from f1_pitwall.services.strategy_engine import (
    StrategyEngine,
    StrategyOption,
    StrategyStop,
)


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

    def test_generates_undercut_when_projected_gain_extends_window(self):
        options = self.engine.calculate_strategies(**self._base_input(
            current_lap=20,
            current_compound=COMPOUND_SOFT,
            tyre_age=20,
            gap_ahead=24.0,
            gap_behind=15.0,
        ))
        undercut = next((option for option in options if option.name == 'undercut'), None)
        self.assertIsNotNone(undercut)
        self.assertIn('projected gain', undercut.notes)
        self.assertGreater(undercut.undercut_potential, 0.0)

    def test_does_not_generate_undercut_when_gap_too_large(self):
        options = self.engine.calculate_strategies(**self._base_input(
            current_lap=20,
            current_compound=COMPOUND_SOFT,
            tyre_age=20,
            gap_ahead=40.0,
            gap_behind=15.0,
        ))
        names = [option.name for option in options]
        self.assertNotIn('undercut', names)

    def test_generates_wet_switch_for_high_rain_probability(self):
        options = self.engine.calculate_strategies(
            **self._base_input(weather_forecast={'rain_probability': 0.8, 'rain_eta_laps': 2}),
        )
        wet = next((option for option in options if option.name == 'wet_switch'), None)
        self.assertIsNotNone(wet)
        self.assertEqual(wet.pit_stops[0].compound, COMPOUND_WET)

    def test_wet_switch_uses_intermediate_for_moderate_rain(self):
        options = self.engine.calculate_strategies(
            **self._base_input(weather_forecast={'rain_probability': 0.6, 'rain_eta_laps': 3}),
        )
        wet = next((option for option in options if option.name == 'wet_switch'), None)
        self.assertIsNotNone(wet)
        self.assertEqual(wet.pit_stops[0].compound, COMPOUND_INTERMEDIATE)

    def test_wet_switch_uses_wet_when_heavy_rain_flag_present(self):
        options = self.engine.calculate_strategies(
            **self._base_input(weather_forecast={
                'rain_probability': 0.6,
                'rain_eta_laps': 3,
                'heavy_rain': True,
            }),
        )
        wet = next((option for option in options if option.name == 'wet_switch'), None)
        self.assertIsNotNone(wet)
        self.assertEqual(wet.pit_stops[0].compound, COMPOUND_WET)

    def test_wet_switch_not_generated_when_rain_probability_too_low(self):
        options = self.engine.calculate_strategies(
            **self._base_input(weather_forecast={'rain_probability': 0.49, 'rain_eta_laps': 2}),
        )
        names = [option.name for option in options]
        self.assertNotIn('wet_switch', names)

    def test_wet_switch_not_generated_when_rain_eta_is_beyond_finish(self):
        options = self.engine.calculate_strategies(
            **self._base_input(
                current_lap=50,
                total_laps=57,
                weather_forecast={'rain_probability': 0.8, 'rain_eta_laps': 10},
            ),
        )
        names = [option.name for option in options]
        self.assertNotIn('wet_switch', names)

    def test_wet_switch_not_generated_when_already_on_target_compound(self):
        options = self.engine.calculate_strategies(
            **self._base_input(
                current_compound=COMPOUND_WET,
                weather_forecast={'rain_probability': 0.9, 'rain_eta_laps': 2},
            ),
        )
        names = [option.name for option in options]
        self.assertNotIn('wet_switch', names)

    def test_wet_switch_accepts_percentage_probability_input(self):
        options = self.engine.calculate_strategies(
            **self._base_input(weather_forecast={'rain_probability': 80, 'rain_eta_laps': 2}),
        )
        names = [option.name for option in options]
        self.assertIn('wet_switch', names)

    def test_wet_switch_note_contains_probability_and_eta(self):
        options = self.engine.calculate_strategies(
            **self._base_input(weather_forecast={'rain_probability': 0.8, 'rain_eta_laps': 2}),
        )
        wet = next(option for option in options if option.name == 'wet_switch')
        self.assertIn('Rain 80%', wet.notes)
        self.assertIn('in ~2 laps', wet.notes)

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
        self.assertTrue(self.engine.calculate_undercut_window(
            24.0, projected_gain=3.0,
        ))

    def test_analyze_undercut_gap_returns_viability_metrics(self):
        analysis = self.engine._analyze_undercut_gap(
            current_compound=COMPOUND_SOFT,
            tyre_age=20,
            base_lap_time=90.0,
            gap_ahead=24.0,
            gap_behind=15.0,
        )
        self.assertIn('window', analysis)
        self.assertIn('projected_gain', analysis)
        self.assertIn('potential', analysis)
        self.assertTrue(analysis['viable'])

    def test_analyze_wet_switch_viable_payload(self):
        analysis = self.engine._analyze_wet_switch(
            current_lap=20,
            total_laps=57,
            current_compound=COMPOUND_SOFT,
            weather_forecast={'rain_probability': 0.8, 'rain_eta_laps': 3},
        )
        self.assertTrue(analysis['viable'])
        self.assertEqual(analysis['target_compound'], COMPOUND_WET)
        self.assertEqual(analysis['stop_lap'], 23)

    def test_result_is_sorted_by_score(self):
        options = self.engine.calculate_strategies(**self._base_input(gap_ahead=10.0))
        scores = [option.score for option in options]
        self.assertEqual(scores, sorted(scores))

    def test_each_strategy_has_calculated_score(self):
        options = self.engine.calculate_strategies(**self._base_input(gap_ahead=10.0))
        self.assertTrue(options)
        for option in options:
            self.assertGreaterEqual(option.score, 0.0)
            self.assertLessEqual(option.score, 1.0)

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

    def test_score_and_sort_strategies_uses_time_and_risk(self):
        options = [
            StrategyOption(
                name='low_time_high_risk',
                total_time=5000.0,
                pit_stops=(),
                tire_risk=0.9,
                weather_risk=0.8,
                undercut_potential=0.0,
                overcut_potential=0.0,
                notes='',
            ),
            StrategyOption(
                name='mid_time_low_risk',
                total_time=5001.0,
                pit_stops=(),
                tire_risk=0.1,
                weather_risk=0.1,
                undercut_potential=0.0,
                overcut_potential=0.0,
                notes='',
            ),
            StrategyOption(
                name='high_time_low_risk',
                total_time=5010.0,
                pit_stops=(),
                tire_risk=0.0,
                weather_risk=0.0,
                undercut_potential=0.0,
                overcut_potential=0.0,
                notes='',
            ),
        ]
        ranked = self.engine._score_and_sort_strategies(options)
        self.assertEqual(ranked[0].name, 'mid_time_low_risk')
        self.assertEqual(ranked[1].name, 'low_time_high_risk')
        self.assertEqual(ranked[2].name, 'high_time_low_risk')

    def test_normalize_total_time_zero_when_spread_is_zero(self):
        normalized = self.engine._normalize_total_time(
            total_time=5000.0,
            min_total=5000.0,
            spread=0.0,
        )
        self.assertEqual(normalized, 0.0)
