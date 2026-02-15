"""Tests for the OpenF1 API client with mocked HTTP responses."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

from django.test import TestCase

from f1_pitwall.exceptions import OpenF1APIError, OpenF1ConnectionError
from f1_pitwall.services.openf1_client import OpenF1Client


def _make_response(status_code=200, json_data=None):
    """Create a mock httpx.Response."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data or []
    if status_code >= 400:
        import httpx
        resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            message=f"{status_code}",
            request=MagicMock(),
            response=resp,
        )
    else:
        resp.raise_for_status.return_value = None
    return resp


class OpenF1ClientInitTest(TestCase):
    """Test client initialization."""

    @patch('f1_pitwall.services.openf1_client.aioredis')
    @patch('f1_pitwall.services.openf1_client.httpx.AsyncClient')
    def test_creates_http_and_redis_clients(self, mock_http, mock_redis):
        client = OpenF1Client()
        mock_http.assert_called_once()
        mock_redis.from_url.assert_called_once()
        self.assertIsNotNone(client)


class OpenF1ClientGetSessionsTest(TestCase):
    """Test get_sessions with mocked HTTP and Redis."""

    def setUp(self):
        self.sessions_data = [
            {
                'session_key': 9158,
                'session_name': 'Race',
                'circuit_short_name': 'Bahrain',
                'year': 2024,
            },
            {
                'session_key': 9159,
                'session_name': 'Qualifying',
                'circuit_short_name': 'Bahrain',
                'year': 2024,
            },
        ]

    @patch('f1_pitwall.services.openf1_client.aioredis')
    @patch('f1_pitwall.services.openf1_client.httpx.AsyncClient')
    async def test_get_sessions_returns_data(self, mock_http_cls, mock_redis):
        mock_http = AsyncMock()
        mock_http.get.return_value = _make_response(
            json_data=self.sessions_data,
        )
        mock_http_cls.return_value = mock_http

        mock_redis_inst = AsyncMock()
        mock_redis_inst.get.return_value = None
        mock_redis.from_url.return_value = mock_redis_inst

        client = OpenF1Client()
        result = await client.get_sessions(year=2024)

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['session_key'], 9158)
        mock_http.get.assert_called_once()

    @patch('f1_pitwall.services.openf1_client.aioredis')
    @patch('f1_pitwall.services.openf1_client.httpx.AsyncClient')
    async def test_get_sessions_with_year_filter(
        self, mock_http_cls, mock_redis,
    ):
        mock_http = AsyncMock()
        mock_http.get.return_value = _make_response(
            json_data=self.sessions_data,
        )
        mock_http_cls.return_value = mock_http

        mock_redis_inst = AsyncMock()
        mock_redis_inst.get.return_value = None
        mock_redis.from_url.return_value = mock_redis_inst

        client = OpenF1Client()
        await client.get_sessions(year=2024)

        call_args = mock_http.get.call_args
        self.assertEqual(call_args.kwargs['params']['year'], 2024)


class OpenF1ClientCachingTest(TestCase):
    """Test Redis caching behavior."""

    @patch('f1_pitwall.services.openf1_client.aioredis')
    @patch('f1_pitwall.services.openf1_client.httpx.AsyncClient')
    async def test_returns_cached_data_without_http_call(
        self, mock_http_cls, mock_redis,
    ):
        cached_data = [{'session_key': 9158, 'cached': True}]

        mock_http = AsyncMock()
        mock_http_cls.return_value = mock_http

        mock_redis_inst = AsyncMock()
        mock_redis_inst.get.return_value = json.dumps(cached_data)
        mock_redis.from_url.return_value = mock_redis_inst

        client = OpenF1Client()
        result = await client.get_sessions()

        self.assertEqual(result, cached_data)
        mock_http.get.assert_not_called()

    @patch('f1_pitwall.services.openf1_client.aioredis')
    @patch('f1_pitwall.services.openf1_client.httpx.AsyncClient')
    async def test_stores_result_in_cache_after_fetch(
        self, mock_http_cls, mock_redis,
    ):
        api_data = [{'session_key': 9158}]

        mock_http = AsyncMock()
        mock_http.get.return_value = _make_response(json_data=api_data)
        mock_http_cls.return_value = mock_http

        mock_redis_inst = AsyncMock()
        mock_redis_inst.get.return_value = None
        mock_redis.from_url.return_value = mock_redis_inst

        client = OpenF1Client()
        await client.get_sessions()

        mock_redis_inst.setex.assert_called_once()
        call_args = mock_redis_inst.setex.call_args
        stored_data = json.loads(call_args[0][2])
        self.assertEqual(stored_data, api_data)

    @patch('f1_pitwall.services.openf1_client.aioredis')
    @patch('f1_pitwall.services.openf1_client.httpx.AsyncClient')
    async def test_historical_data_uses_long_ttl(
        self, mock_http_cls, mock_redis,
    ):
        mock_http = AsyncMock()
        mock_http.get.return_value = _make_response(json_data=[])
        mock_http_cls.return_value = mock_http

        mock_redis_inst = AsyncMock()
        mock_redis_inst.get.return_value = None
        mock_redis.from_url.return_value = mock_redis_inst

        client = OpenF1Client()
        await client.get_sessions()

        ttl = mock_redis_inst.setex.call_args[0][1]
        self.assertEqual(ttl, 3600)

    @patch('f1_pitwall.services.openf1_client.aioredis')
    @patch('f1_pitwall.services.openf1_client.httpx.AsyncClient')
    async def test_live_data_uses_short_ttl(
        self, mock_http_cls, mock_redis,
    ):
        mock_http = AsyncMock()
        mock_http.get.return_value = _make_response(json_data=[])
        mock_http_cls.return_value = mock_http

        mock_redis_inst = AsyncMock()
        mock_redis_inst.get.return_value = None
        mock_redis.from_url.return_value = mock_redis_inst

        client = OpenF1Client()
        await client.get_car_data(
            session_key=9158, driver_number=1,
            date_gt='2024-03-02T15:00:00',
        )

        ttl = mock_redis_inst.setex.call_args[0][1]
        self.assertEqual(ttl, 5)

    @patch('f1_pitwall.services.openf1_client.aioredis')
    @patch('f1_pitwall.services.openf1_client.httpx.AsyncClient')
    async def test_redis_failure_does_not_break_fetch(
        self, mock_http_cls, mock_redis,
    ):
        """Cache errors are silently logged — API still returns data."""
        api_data = [{'speed': 320}]

        mock_http = AsyncMock()
        mock_http.get.return_value = _make_response(json_data=api_data)
        mock_http_cls.return_value = mock_http

        mock_redis_inst = AsyncMock()
        mock_redis_inst.get.side_effect = Exception("Redis down")
        mock_redis_inst.setex.side_effect = Exception("Redis down")
        mock_redis.from_url.return_value = mock_redis_inst

        client = OpenF1Client()
        result = await client.get_positions(session_key=9158)

        self.assertEqual(result, api_data)


class OpenF1ClientRetryTest(TestCase):
    """Test retry behavior on failures."""

    @patch('f1_pitwall.services.openf1_client.asyncio.sleep', new_callable=AsyncMock)
    @patch('f1_pitwall.services.openf1_client.aioredis')
    @patch('f1_pitwall.services.openf1_client.httpx.AsyncClient')
    async def test_retries_on_server_error(
        self, mock_http_cls, mock_redis, mock_sleep,
    ):
        import httpx

        fail_resp = MagicMock()
        fail_resp.status_code = 500
        fail_resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            message="500", request=MagicMock(), response=fail_resp,
        )

        ok_resp = _make_response(json_data=[{'ok': True}])

        mock_http = AsyncMock()
        mock_http.get.side_effect = [fail_resp, ok_resp]
        mock_http_cls.return_value = mock_http

        mock_redis_inst = AsyncMock()
        mock_redis_inst.get.return_value = None
        mock_redis.from_url.return_value = mock_redis_inst

        client = OpenF1Client()
        result = await client.get_weather(session_key=9158)

        self.assertEqual(result, [{'ok': True}])
        self.assertEqual(mock_http.get.call_count, 2)
        mock_sleep.assert_called_once_with(1.0)

    @patch('f1_pitwall.services.openf1_client.asyncio.sleep', new_callable=AsyncMock)
    @patch('f1_pitwall.services.openf1_client.aioredis')
    @patch('f1_pitwall.services.openf1_client.httpx.AsyncClient')
    async def test_raises_connection_error_after_max_retries(
        self, mock_http_cls, mock_redis, mock_sleep,
    ):
        import httpx

        mock_http = AsyncMock()
        mock_http.get.side_effect = httpx.TimeoutException("timeout")
        mock_http_cls.return_value = mock_http

        mock_redis_inst = AsyncMock()
        mock_redis_inst.get.return_value = None
        mock_redis.from_url.return_value = mock_redis_inst

        client = OpenF1Client()

        with self.assertRaises(OpenF1ConnectionError):
            await client.get_drivers()

        self.assertEqual(mock_http.get.call_count, 3)

    @patch('f1_pitwall.services.openf1_client.aioredis')
    @patch('f1_pitwall.services.openf1_client.httpx.AsyncClient')
    async def test_client_error_raises_immediately(
        self, mock_http_cls, mock_redis,
    ):
        """4xx errors should not retry — raise OpenF1APIError immediately."""
        mock_http = AsyncMock()
        mock_http.get.return_value = _make_response(status_code=404)
        mock_http_cls.return_value = mock_http

        mock_redis_inst = AsyncMock()
        mock_redis_inst.get.return_value = None
        mock_redis.from_url.return_value = mock_redis_inst

        client = OpenF1Client()

        with self.assertRaises(OpenF1APIError):
            await client.get_sessions()

        self.assertEqual(mock_http.get.call_count, 1)


class OpenF1ClientEndpointsTest(TestCase):
    """Test that each public method calls the correct API endpoint."""

    def setUp(self):
        self._patches = []
        p_http = patch('f1_pitwall.services.openf1_client.httpx.AsyncClient')
        p_redis = patch('f1_pitwall.services.openf1_client.aioredis')
        self._patches.extend([p_http, p_redis])

        self.mock_http_cls = p_http.start()
        self.mock_redis = p_redis.start()

        self.mock_http = AsyncMock()
        self.mock_http.get.return_value = _make_response(json_data=[])
        self.mock_http_cls.return_value = self.mock_http

        self.mock_redis_inst = AsyncMock()
        self.mock_redis_inst.get.return_value = None
        self.mock_redis.from_url.return_value = self.mock_redis_inst

        self.client = OpenF1Client()

    def tearDown(self):
        for p in self._patches:
            p.stop()

    def _called_endpoint(self):
        return self.mock_http.get.call_args[0][0]

    def _called_params(self):
        return self.mock_http.get.call_args[1]['params']

    async def test_get_car_data_endpoint(self):
        await self.client.get_car_data(9158, 1)
        self.assertEqual(self._called_endpoint(), '/car_data')
        self.assertEqual(self._called_params()['driver_number'], 1)

    async def test_get_car_data_with_date_gt(self):
        await self.client.get_car_data(9158, 44, date_gt='2024-03-02T15:00')
        params = self._called_params()
        self.assertEqual(params['date>'], '2024-03-02T15:00')

    async def test_get_lap_data_endpoint(self):
        await self.client.get_lap_data(9158, driver_number=44)
        self.assertEqual(self._called_endpoint(), '/laps')
        self.assertEqual(self._called_params()['driver_number'], 44)

    async def test_get_positions_endpoint(self):
        await self.client.get_positions(9158)
        self.assertEqual(self._called_endpoint(), '/position')

    async def test_get_intervals_endpoint(self):
        await self.client.get_intervals(9158)
        self.assertEqual(self._called_endpoint(), '/intervals')

    async def test_get_pit_data_endpoint(self):
        await self.client.get_pit_data(9158)
        self.assertEqual(self._called_endpoint(), '/pit')

    async def test_get_stints_endpoint(self):
        await self.client.get_stints(9158, driver_number=1)
        self.assertEqual(self._called_endpoint(), '/stints')
        self.assertEqual(self._called_params()['driver_number'], 1)

    async def test_get_weather_endpoint(self):
        await self.client.get_weather(9158)
        self.assertEqual(self._called_endpoint(), '/weather')

    async def test_get_race_control_endpoint(self):
        await self.client.get_race_control(9158)
        self.assertEqual(self._called_endpoint(), '/race_control')

    async def test_get_team_radio_endpoint(self):
        await self.client.get_team_radio(9158, driver_number=44)
        self.assertEqual(self._called_endpoint(), '/team_radio')

    async def test_get_overtakes_endpoint(self):
        await self.client.get_overtakes(9158)
        self.assertEqual(self._called_endpoint(), '/overtakes')

    async def test_get_drivers_endpoint(self):
        await self.client.get_drivers(session_key=9158)
        self.assertEqual(self._called_endpoint(), '/drivers')
        self.assertEqual(self._called_params()['session_key'], 9158)


class OpenF1ClientCloseTest(TestCase):
    """Test clean shutdown."""

    @patch('f1_pitwall.services.openf1_client.aioredis')
    @patch('f1_pitwall.services.openf1_client.httpx.AsyncClient')
    async def test_close_shuts_down_both_clients(
        self, mock_http_cls, mock_redis,
    ):
        mock_http = AsyncMock()
        mock_http_cls.return_value = mock_http

        mock_redis_inst = AsyncMock()
        mock_redis.from_url.return_value = mock_redis_inst

        client = OpenF1Client()
        await client.close()

        mock_http.aclose.assert_awaited_once()
        mock_redis_inst.aclose.assert_awaited_once()
