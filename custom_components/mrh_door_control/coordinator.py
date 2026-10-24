import requests
import aiohttp
import asyncio
import logging

import async_timeout
from datetime import timedelta

from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession

DOMAIN = "mrh_door_control"
_LOGGER = logging.getLogger(__name__)

REQUEST_TIMEOUT = 5
# Ask the device to drop the socket after each response so it never holds idle connections open
REQUEST_HEADERS = {"Connection": "close"}


def entity_uid_prefix(url: str) -> str:
    # Entity unique_ids are "<prefix>_<pin>"; the reconfigure flow rewrites this prefix when the URL changes
    return url.replace("http://", "").replace("https://","").replace(".", "_")


def describe_error(e: Exception) -> str:
    # asyncio.TimeoutError has an empty message, so always lead with the exception type
    return f"{type(e).__name__}: {e}" if str(e) else type(e).__name__


async def fetch_status(session: aiohttp.ClientSession, api_url: str) -> dict:
    try:
        # Keep the timeout tight so failures return fast
        async with async_timeout.timeout(REQUEST_TIMEOUT):
            async with session.get(api_url, headers=REQUEST_HEADERS) as response:
                if response.status == 200:
                    return await response.json(content_type=None)  # device sometimes sends text/html
                raise UpdateFailed(f"HTTP {response.status} from {api_url}")
    except (asyncio.TimeoutError, aiohttp.ClientError) as e:
        # Network/timeout -> handled as UpdateFailed so HA degrades gracefully
        raise UpdateFailed(f"Network error talking to {api_url}: {describe_error(e)}") from e


class DoorCoordinator(DataUpdateCoordinator):
    """Polls one device. Shared by every config entry that points at the same URL."""

    def __init__(self, hass, url):
        super().__init__(
            hass,
            logger=_LOGGER,  # your logger
            name=f"Door Coordinator ({url})",
            # Shared across entries, so not tied to any one entry's lifecycle; __init__.py shuts it down
            config_entry=None,
            update_method=self._async_update,
            update_interval=timedelta(seconds=1),
        )

        self.url = url
        self.session = async_get_clientsession(hass)
        # The device serves one client at a time, so polls and commands queue here instead of on its sockets
        self._request_lock = asyncio.Lock()


    async def _async_update(self):
        async with self._request_lock:
            return await fetch_status(self.session, self.url)

    async def async_send_command(self, payload: str):
        headers = {**REQUEST_HEADERS, "Content-Type": "text/plain"}
        async with self._request_lock:
            try:
                async with async_timeout.timeout(REQUEST_TIMEOUT):
                    async with self.session.post(self.url, data=payload, headers=headers) as response:
                        if response.status != 200:
                            _LOGGER.error(f"Failed to send command {payload}. Server: {self.url} Response Status: {response.status}")
            except (asyncio.TimeoutError, aiohttp.ClientError) as e:
                raise HomeAssistantError(f"Failed to send command {payload} to {self.url}: {describe_error(e)}") from e
