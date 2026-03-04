"""Pure calculation logic for race strategy modeling."""

from dataclasses import dataclass, replace

from f1_pitwall.constants import (
    COMPOUND_HARD,
    COMPOUND_INTERMEDIATE,
    COMPOUND_MEDIUM,
    COMPOUND_SOFT,
    COMPOUND_WET,
    PIT_STOP_TIME_LOSS,
)


@dataclass(frozen=True)
class TireProfile:
    """Tire degradation assumptions used by the strategy model."""

    degradation_per_lap: float
    cliff_lap: int
    optimal_window_start: int
    optimal_window_end: int


@dataclass(frozen=True)
class StrategyStop:
    """Single planned stop with in-lap and next compound."""

    lap: int
    compound: str


@dataclass(frozen=True)
class StrategyOption:
    """Computed strategy option scored for decision support."""

    name: str
    total_time: float
    pit_stops: tuple[StrategyStop, ...]
    tire_risk: float
    weather_risk: float
    undercut_potential: float
    overcut_potential: float
    notes: str
    score: float = 0.0


class StrategyEngine:
    """Pure race-strategy calculator with tire degradation simulation."""

    DEGRADATION_PROFILES = {
        COMPOUND_SOFT: TireProfile(0.08, 18, 12, 18),
        COMPOUND_MEDIUM: TireProfile(0.05, 28, 20, 28),
        COMPOUND_HARD: TireProfile(0.03, 40, 30, 40),
        COMPOUND_INTERMEDIATE: TireProfile(0.06, 25, 18, 25),
        COMPOUND_WET: TireProfile(0.07, 20, 14, 20),
    }

    def __init__(self, pit_time_loss=PIT_STOP_TIME_LOSS):
        self.pit_time_loss = pit_time_loss

    def calculate_strategies(
        self,
        current_lap,
        total_laps,
        current_compound,
        tyre_age,
        base_lap_time,
        weather_forecast,
        gap_ahead,
        gap_behind,
    ):
        """Generate and rank strategy options for the current race state."""
        strategies = []
        one_stop = self._one_stop_option(
            current_lap, total_laps, current_compound, tyre_age, base_lap_time,
            weather_forecast, gap_behind,
        )
        if one_stop:
            strategies.append(one_stop)

        two_stop = self._two_stop_option(
            current_lap, total_laps, current_compound, tyre_age, base_lap_time,
            weather_forecast,
        )
        if two_stop:
            strategies.append(two_stop)

        undercut = self._undercut_option(
            current_lap, total_laps, current_compound, tyre_age, base_lap_time,
            weather_forecast, gap_ahead, gap_behind,
        )
        if undercut:
            strategies.append(undercut)

        wet_switch = self._wet_switch_option(
            current_lap, total_laps, current_compound, tyre_age, base_lap_time,
            weather_forecast,
        )
        if wet_switch:
            strategies.append(wet_switch)
        return self._score_and_sort_strategies(strategies)

    def predict_lap_time(self, compound, tyre_age, base_lap_time):
        """Predict one lap time using piecewise degradation with cliff."""
        profile = self._profile(compound)
        if tyre_age <= profile.cliff_lap:
            return base_lap_time + profile.degradation_per_lap * tyre_age
        normal = profile.degradation_per_lap * profile.cliff_lap
        cliff_laps = tyre_age - profile.cliff_lap
        cliff = profile.degradation_per_lap * 3 * cliff_laps
        return base_lap_time + normal + cliff

    def simulate_race_time(
        self,
        start_lap,
        total_laps,
        stops,
        base_lap_time,
        current_compound,
        current_tyre_age,
    ):
        """Simulate total time for a strategy from current lap onward."""
        stop_map = {stop.lap: stop for stop in stops}
        total_time = 0.0
        compound = current_compound
        tyre_age = current_tyre_age

        for lap in range(start_lap, total_laps + 1):
            stop = stop_map.get(lap)
            if stop:
                total_time += self.pit_time_loss
                compound = stop.compound
                tyre_age = 0
            total_time += self.predict_lap_time(compound, tyre_age, base_lap_time)
            tyre_age += 1
        return total_time

    def calculate_undercut_window(
        self, gap_ahead, pit_time_loss=None, projected_gain=0.0,
    ):
        """Return whether undercut is viable from gap and projected gain."""
        threshold = pit_time_loss if pit_time_loss is not None else self.pit_time_loss
        return gap_ahead <= threshold + max(0.0, projected_gain)

    def _one_stop_option(
        self,
        current_lap,
        total_laps,
        current_compound,
        tyre_age,
        base_lap_time,
        weather_forecast,
        gap_behind,
    ):
        if current_lap >= total_laps - 1:
            return None

        pit_lap = self._best_one_stop_pit_lap(
            current_lap, total_laps, current_compound, tyre_age, base_lap_time,
        )
        if pit_lap is None:
            return None

        next_compound = self._compound_for_remaining(total_laps - pit_lap)
        stops = (StrategyStop(lap=pit_lap, compound=next_compound),)
        total_time = self.simulate_race_time(
            current_lap, total_laps, stops, base_lap_time,
            current_compound, tyre_age,
        )
        window = self._detect_optimal_window(current_compound, current_lap)
        return self._build_option(
            name='one_stop',
            total_time=total_time,
            pit_stops=stops,
            weather_forecast=weather_forecast,
            current_compound=current_compound,
            start_lap=current_lap,
            current_tyre_age=tyre_age,
            undercut=False,
            overcut=gap_behind < 3.0,
            notes=(
                f"Optimal window L{window['start']}-{window['end']}; "
                f"selected pit lap {pit_lap} ({window['state']})."
            ),
        )

    def _two_stop_option(
        self,
        current_lap,
        total_laps,
        current_compound,
        tyre_age,
        base_lap_time,
        weather_forecast,
    ):
        remaining = total_laps - current_lap + 1
        if remaining <= 20:
            return None

        plan = self._best_two_stop_plan(
            current_lap, total_laps, current_compound, tyre_age, base_lap_time,
        )
        if plan is None:
            return None

        first_lap, second_lap, stops = plan
        total_time = self.simulate_race_time(
            current_lap, total_laps, stops, base_lap_time,
            current_compound, tyre_age,
        )
        stint_1 = first_lap - current_lap
        stint_2 = second_lap - first_lap
        stint_3 = total_laps - second_lap + 1
        return self._build_option(
            name='two_stop',
            total_time=total_time,
            pit_stops=stops,
            weather_forecast=weather_forecast,
            current_compound=current_compound,
            start_lap=current_lap,
            current_tyre_age=tyre_age,
            undercut=False,
            overcut=False,
            notes=(
                f"Third split stints: {stint_1}/{stint_2}/{stint_3} laps; "
                f"pits on L{first_lap} and L{second_lap}."
            ),
        )

    def _undercut_option(
        self,
        current_lap,
        total_laps,
        current_compound,
        tyre_age,
        base_lap_time,
        weather_forecast,
        gap_ahead,
        gap_behind,
    ):
        analysis = self._analyze_undercut_gap(
            current_compound, tyre_age, base_lap_time, gap_ahead, gap_behind,
        )
        if not analysis['viable']:
            return None

        compound = COMPOUND_SOFT if current_compound != COMPOUND_SOFT else COMPOUND_MEDIUM
        stops = (StrategyStop(lap=current_lap + 1, compound=compound),)
        total_time = self.simulate_race_time(
            current_lap, total_laps, stops, base_lap_time,
            current_compound, tyre_age,
        )
        return self._build_option(
            name='undercut',
            total_time=total_time,
            pit_stops=stops,
            weather_forecast=weather_forecast,
            current_compound=current_compound,
            start_lap=current_lap,
            current_tyre_age=tyre_age,
            undercut=analysis['potential'],
            overcut=False,
            notes=(
                f"Gap ahead {gap_ahead:.1f}s vs undercut window "
                f"{analysis['window']:.2f}s; projected gain "
                f"{analysis['projected_gain']:.2f}s."
            ),
        )

    def _wet_switch_option(
        self,
        current_lap,
        total_laps,
        current_compound,
        tyre_age,
        base_lap_time,
        weather_forecast,
    ):
        analysis = self._analyze_wet_switch(
            current_lap, total_laps, current_compound, weather_forecast,
        )
        if not analysis['viable']:
            return None

        stop_lap = analysis['stop_lap']
        target = analysis['target_compound']
        stops = (StrategyStop(lap=stop_lap, compound=target),)
        total_time = self.simulate_race_time(
            current_lap, total_laps, stops, base_lap_time,
            current_compound, tyre_age,
        )
        return self._build_option(
            name='wet_switch',
            total_time=total_time,
            pit_stops=stops,
            weather_forecast=weather_forecast,
            current_compound=current_compound,
            start_lap=current_lap,
            current_tyre_age=tyre_age,
            undercut=False,
            overcut=False,
            notes=(
                f"Rain {analysis['rain_probability']:.0%} in ~"
                f"{analysis['eta_laps']} laps; switch to {target} on L{stop_lap}."
            ),
        )

    def _build_option(
        self,
        name,
        total_time,
        pit_stops,
        weather_forecast,
        current_compound,
        start_lap,
        current_tyre_age,
        undercut,
        overcut,
        notes,
    ):
        tire_risk = self._strategy_tire_risk(
            start_lap, pit_stops, current_compound, current_tyre_age,
        )
        weather_risk = self._strategy_weather_risk(name, weather_forecast)
        return StrategyOption(
            name=name,
            total_time=round(total_time, 3),
            pit_stops=pit_stops,
            tire_risk=tire_risk,
            weather_risk=weather_risk,
            undercut_potential=float(undercut),
            overcut_potential=1.0 if overcut else 0.0,
            notes=notes,
        )

    def _strategy_tire_risk(
        self, start_lap, pit_stops, current_compound, current_tyre_age,
    ):
        stint_start = start_lap
        compound = current_compound
        age = current_tyre_age
        weighted_risk = 0.0
        total_laps = 0
        for stop in pit_stops:
            laps = max(0, stop.lap - stint_start)
            weighted_risk += self._stint_risk(compound, age, laps) * laps
            total_laps += laps
            stint_start = stop.lap
            compound = stop.compound
            age = 0
        if total_laps == 0:
            return 0.0
        return round(min(1.0, weighted_risk / total_laps), 3)

    def _strategy_weather_risk(self, strategy_name, weather_forecast):
        rain_probability = self._rain_probability(weather_forecast)
        if strategy_name == 'wet_switch':
            return round(max(0.0, 1.0 - rain_probability), 3)
        return round(rain_probability, 3)

    def _stint_risk(self, compound, start_age, stint_laps):
        profile = self._profile(compound)
        end_age = start_age + stint_laps
        if end_age <= profile.cliff_lap:
            return 0.0
        laps_over = end_age - profile.cliff_lap
        return min(1.0, laps_over / max(1, stint_laps))

    def _best_one_stop_pit_lap(
        self, current_lap, total_laps, current_compound, tyre_age, base_lap_time,
    ):
        candidates = self._one_stop_candidates(
            current_lap, total_laps, current_compound,
        )
        if not candidates:
            return None

        best_lap = None
        best_time = None
        for lap in candidates:
            compound = self._compound_for_remaining(total_laps - lap)
            total_time = self.simulate_race_time(
                start_lap=current_lap,
                total_laps=total_laps,
                stops=(StrategyStop(lap=lap, compound=compound),),
                base_lap_time=base_lap_time,
                current_compound=current_compound,
                current_tyre_age=tyre_age,
            )
            if best_time is None or total_time < best_time:
                best_time = total_time
                best_lap = lap
        return best_lap

    def _one_stop_candidates(self, current_lap, total_laps, compound):
        window = self._detect_optimal_window(compound, current_lap)
        latest_pit_lap = total_laps - 1
        if latest_pit_lap <= current_lap:
            return []

        if window['state'] == 'before_window':
            if window['laps_to_open'] < 2:
                return []
            start = max(current_lap + 1, window['start'])
            end = min(window['end'], latest_pit_lap)
            if start > end:
                return []
            return list(range(start, end + 1))

        if window['state'] == 'in_window':
            start = current_lap + 1
            end = min(window['end'], latest_pit_lap)
            if start > end:
                return []
            return list(range(start, end + 1))

        return [current_lap + 1] if current_lap + 1 <= latest_pit_lap else []

    def _detect_optimal_window(self, compound, current_lap):
        profile = self._profile(compound)
        start = profile.optimal_window_start
        end = profile.optimal_window_end
        if current_lap < start:
            state = 'before_window'
        elif current_lap <= end:
            state = 'in_window'
        else:
            state = 'past_window'
        return {
            'start': start,
            'end': end,
            'state': state,
            'laps_to_open': max(0, start - current_lap),
        }

    def _best_two_stop_plan(
        self, current_lap, total_laps, current_compound, tyre_age, base_lap_time,
    ):
        split_first, split_second = self._two_stop_split_laps(current_lap, total_laps)
        candidates = self._two_stop_candidates(
            split_first, split_second, current_lap, total_laps,
        )
        if not candidates:
            return None

        best = None
        best_time = None
        for first_lap, second_lap in candidates:
            stops = self._build_two_stop_stops(first_lap, second_lap, total_laps)
            total_time = self.simulate_race_time(
                start_lap=current_lap,
                total_laps=total_laps,
                stops=stops,
                base_lap_time=base_lap_time,
                current_compound=current_compound,
                current_tyre_age=tyre_age,
            )
            if best_time is None or total_time < best_time:
                best_time = total_time
                best = (first_lap, second_lap, stops)
        return best

    def _two_stop_split_laps(self, current_lap, total_laps):
        remaining = total_laps - current_lap + 1
        base = remaining // 3
        remainder = remaining % 3
        stint_1 = base + (1 if remainder > 0 else 0)
        stint_2 = base + (1 if remainder > 1 else 0)
        first_lap = current_lap + stint_1
        second_lap = first_lap + stint_2
        return first_lap, second_lap

    def _two_stop_candidates(
        self, split_first, split_second, current_lap, total_laps,
    ):
        latest_second = total_laps - 1
        if latest_second <= current_lap + 1:
            return []

        candidates = set()
        for first_offset in (-1, 0, 1):
            for second_offset in (-1, 0, 1):
                first = split_first + first_offset
                second = split_second + second_offset
                if first <= current_lap:
                    continue
                if second <= first:
                    continue
                if second > latest_second:
                    continue
                candidates.add((first, second))
        return sorted(candidates)

    def _build_two_stop_stops(self, first_lap, second_lap, total_laps):
        middle_stint = second_lap - first_lap
        final_stint = total_laps - second_lap + 1
        first_compound = COMPOUND_HARD if middle_stint >= 10 else COMPOUND_MEDIUM
        second_compound = COMPOUND_SOFT if final_stint <= 15 else COMPOUND_MEDIUM
        return (
            StrategyStop(lap=first_lap, compound=first_compound),
            StrategyStop(lap=second_lap, compound=second_compound),
        )

    def _compound_for_remaining(self, remaining_laps):
        if remaining_laps > 20:
            return COMPOUND_HARD
        if remaining_laps > 10:
            return COMPOUND_MEDIUM
        return COMPOUND_SOFT

    def _rain_probability(self, weather_forecast):
        value = float(weather_forecast.get('rain_probability') or 0.0)
        if value > 1.0:
            value /= 100.0
        return min(max(value, 0.0), 1.0)

    def _analyze_wet_switch(
        self, current_lap, total_laps, current_compound, weather_forecast,
    ):
        rain_probability = self._rain_probability(weather_forecast)
        eta_laps = self._rain_eta_laps(weather_forecast)
        remaining_laps = total_laps - current_lap
        if remaining_laps < 2:
            return {'viable': False}
        if rain_probability < 0.5:
            return {'viable': False}
        if eta_laps > remaining_laps:
            return {'viable': False}

        target_compound = self._wet_target_compound(
            weather_forecast, rain_probability,
        )
        if current_compound == target_compound:
            return {'viable': False}

        stop_lap = min(total_laps - 1, current_lap + max(1, eta_laps))
        if stop_lap <= current_lap:
            return {'viable': False}
        return {
            'viable': True,
            'rain_probability': rain_probability,
            'eta_laps': eta_laps,
            'target_compound': target_compound,
            'stop_lap': stop_lap,
        }

    def _wet_target_compound(self, weather_forecast, rain_probability):
        heavy_rain = bool(weather_forecast.get('heavy_rain'))
        rain_intensity = float(weather_forecast.get('rain_intensity') or 0.0)
        if heavy_rain or rain_intensity >= 0.7 or rain_probability >= 0.75:
            return COMPOUND_WET
        return COMPOUND_INTERMEDIATE

    def _rain_eta_laps(self, weather_forecast):
        eta_raw = weather_forecast.get('rain_eta_laps')
        if eta_raw in (None, ''):
            return 1
        try:
            return max(1, int(eta_raw))
        except (TypeError, ValueError):
            return 1

    def _analyze_undercut_gap(
        self, current_compound, tyre_age, base_lap_time, gap_ahead, gap_behind,
    ):
        pit_compound = (
            COMPOUND_SOFT if current_compound != COMPOUND_SOFT else COMPOUND_MEDIUM
        )
        rival_next = self.predict_lap_time(
            current_compound, tyre_age + 1, base_lap_time,
        )
        our_next = self.predict_lap_time(pit_compound, 0, base_lap_time)
        lap_gain = max(0.0, rival_next - our_next)
        projected_gain = round(lap_gain * 3, 3)
        window = self.pit_time_loss + projected_gain
        margin = window - gap_ahead
        rejoin_gap = gap_behind - self.pit_time_loss + projected_gain
        potential = min(
            1.0,
            max(0.0, (margin / max(self.pit_time_loss, 1.0)) + 0.5),
        )
        return {
            'viable': self.calculate_undercut_window(
                gap_ahead, projected_gain=projected_gain,
            ),
            'window': round(window, 3),
            'margin': round(margin, 3),
            'projected_gain': projected_gain,
            'rejoin_gap': round(rejoin_gap, 3),
            'potential': round(potential, 3),
        }

    def _profile(self, compound):
        profile = self.DEGRADATION_PROFILES.get(compound)
        if profile is None:
            raise ValueError(f'Unknown compound: {compound}')
        return profile

    def _score_and_sort_strategies(self, strategies):
        """Score strategies on time+risk and return best-first ordering."""
        if not strategies:
            return []

        totals = [strategy.total_time for strategy in strategies]
        min_total = min(totals)
        max_total = max(totals)
        spread = max_total - min_total

        scored = []
        for strategy in strategies:
            normalized_time = self._normalize_total_time(
                strategy.total_time, min_total, spread,
            )
            score = round(
                (0.7 * normalized_time)
                + (0.2 * strategy.tire_risk)
                + (0.1 * strategy.weather_risk),
                3,
            )
            scored.append(replace(strategy, score=score))

        return sorted(
            scored,
            key=lambda s: (
                s.score,
                s.total_time,
                s.tire_risk,
                s.weather_risk,
            ),
        )

    def _normalize_total_time(self, total_time, min_total, spread):
        if spread <= 0:
            return 0.0
        return (total_time - min_total) / spread
