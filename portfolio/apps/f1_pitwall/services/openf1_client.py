"""Async HTTP client for all communication with the OpenF1 API."""

import asyncio
import hashlib
import json
import logging
import os

import httpx
import redis.asyncio as aioredis

from f1_pitwall.constants import (
    CACHE_TTL_HISTORICAL,
    CACHE_TTL_LIVE,
    OPENF1_BASE_URL,
)
from f1_pitwall.exceptions import OpenF1APIError, OpenF1ConnectionError

logger = logging.getLogger(__name__)

MAX_CONNECTIONS = 20
MAX_KEEPALIVE = 10
REQUEST_TIMEOUT = 30.0
MAX_RETRIES = 3
RETRY_BASE_DELAY = 1.0


class OpenF1Client:
    """Async HTTP client for OpenF1 API with Redis caching and retries.

    Instantiate per WebSocket connection or Celery task — not a singleton.
    """

    def __init__(self):
        self._base_url = os.environ.get('OPENF1_API_URL', OPENF1_BASE_URL)
        self._http = httpx.AsyncClient(
            base_url=self._base_url,
            timeout=httpx.Timeout(REQUEST_TIMEOUT),
            limits=httpx.Limits(
                max_connections=MAX_CONNECTIONS,
                max_keepalive_connections=MAX_KEEPALIVE,
            ),
        )
        redis_url = os.environ.get('CELERY_BROKER', 'redis://redis:6379/0')
        self._redis = aioredis.from_url(redis_url, decode_responses=True)

    # -- Public API methods --------------------------------------------------

    async def get_sessions(self, year=None):
        """Fetch session metadata. Historical TTL."""
        params = {}
        if year:
            params['year'] = year
        return await self._request('/sessions', params, live=False)

    async def get_drivers(self, session_key=None):
        """Fetch driver information. Historical TTL."""
        params = {}
        if session_key:
            params['session_key'] = session_key
        return await self._request('/drivers', params, live=False)

    async def get_car_data(self, session_key, driver_number, date_gt=None):
        """Fetch telemetry at ~3.7 Hz. Live TTL when date_gt is set."""
        params = {
            'session_key': session_key,
            'driver_number': driver_number,
        }
        if date_gt:
            params['date>'] = date_gt
        return await self._request('/car_data', params, live=bool(date_gt))

    async def get_lap_data(self, session_key, driver_number=None):
        """Fetch lap times and sectors."""
        params = {'session_key': session_key}
        if driver_number:
            params['driver_number'] = driver_number
        return await self._request('/laps', params, live=False)

    async def get_positions(self, session_key):
        """Fetch GPS positions of all cars."""
        return await self._request(
            '/position', {'session_key': session_key}, live=True,
        )

    async def get_intervals(self, session_key):
        """Fetch time gaps between cars."""
        return await self._request(
            '/intervals', {'session_key': session_key}, live=True,
        )

    async def get_pit_data(self, session_key, driver_number=None):
        """Fetch pit stop events."""
        params = {'session_key': session_key}
        if driver_number:
            params['driver_number'] = driver_number
        return await self._request('/pit', params, live=False)

    async def get_stints(self, session_key, driver_number=None):
        """Fetch tire compound data per stint."""
        params = {'session_key': session_key}
        if driver_number:
            params['driver_number'] = driver_number
        return await self._request('/stints', params, live=False)

    async def get_weather(self, session_key):
        """Fetch track weather conditions."""
        return await self._request(
            '/weather', {'session_key': session_key}, live=False,
        )

    async def get_race_control(self, session_key):
        """Fetch flags, safety car, incidents."""
        return await self._request(
            '/race_control', {'session_key': session_key}, live=False,
        )

    async def get_team_radio(self, session_key, driver_number=None):
        """Fetch team radio audio URLs."""
        params = {'session_key': session_key}
        if driver_number:
            params['driver_number'] = driver_number
        return await self._request('/team_radio', params, live=False)

    async def get_overtakes(self, session_key):
        """Fetch overtaking events."""
        return await self._request(
            '/overtakes', {'session_key': session_key}, live=False,
        )

    async def close(self):
        """Clean shutdown of HTTP and Redis connections."""
        await self._http.aclose()
        await self._redis.aclose()

    # -- Internal helpers ----------------------------------------------------

    async def _request(self, endpoint, params, live=False):
        """Build params -> check cache -> call API -> cache result -> return."""
        cache_key = self._build_cache_key(endpoint, params)
        cached = await self._get_cached(cache_key)
        if cached is not None:
            return cached

        data = await self._fetch_with_retries(endpoint, params)
        ttl = CACHE_TTL_LIVE if live else CACHE_TTL_HISTORICAL
        await self._set_cached(cache_key, data, ttl)
        return data

    async def _fetch_with_retries(self, endpoint, params):
        """HTTP GET with exponential backoff retries."""
        last_error = None

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = await self._http.get(endpoint, params=params)
                response.raise_for_status()
                data = response.json()
                self._log_success(endpoint, params, len(data))
                return data
            except httpx.TimeoutException as exc:
                last_error = exc
                self._log_retry(endpoint, attempt, exc)
            except httpx.HTTPStatusError as exc:
                last_error = exc
                self._log_retry(endpoint, attempt, exc)
                if exc.response.status_code < 500:
                    raise OpenF1APIError(
                        f"{endpoint} returned {exc.response.status_code}"
                    ) from exc
            except httpx.RequestError as exc:
                last_error = exc
                self._log_retry(endpoint, attempt, exc)

            if attempt < MAX_RETRIES:
                delay = RETRY_BASE_DELAY * (2 ** (attempt - 1))
                await asyncio.sleep(delay)

        raise OpenF1ConnectionError(
            f"Failed after {MAX_RETRIES} attempts: {endpoint}"
        ) from last_error

    def _build_cache_key(self, endpoint, params):
        """Build deterministic Redis cache key from endpoint and params."""
        sorted_params = json.dumps(params, sort_keys=True)
        param_hash = hashlib.md5(sorted_params.encode()).hexdigest()[:12]
        return f"f1:{endpoint.strip('/')}:{param_hash}"

    async def _get_cached(self, key):
        """Return cached JSON data or None."""
        try:
            raw = await self._redis.get(key)
            if raw:
                return json.loads(raw)
        except Exception:
            logger.warning("Redis cache read failed for key %s", key)
        return None

    async def _set_cached(self, key, data, ttl):
        """Store JSON data in Redis with TTL."""
        try:
            await self._redis.setex(key, ttl, json.dumps(data))
        except Exception:
            logger.warning("Redis cache write failed for key %s", key)

    def _log_success(self, endpoint, params, count):
        logger.info(
            "OpenF1 %s | params=%s | results=%d",
            endpoint, params, count,
        )

    def _log_retry(self, endpoint, attempt, error):
        logger.warning(
            "OpenF1 %s | attempt %d/%d failed: %s",
            endpoint, attempt, MAX_RETRIES, error,
        )
