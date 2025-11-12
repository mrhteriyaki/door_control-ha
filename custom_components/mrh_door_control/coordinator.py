import requests
import aiohttp
import asyncio 
import logging  

import async_timeout
from datetime import timedelta

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession

DOMAIN = "mrh_door_control"
_LOGGER = logging.getLogger(__name__)

async def fetch_status(session: aiohttp.ClientSession, api_url: str) -> dict:
    try:
        # Keep the timeout tight so failures return fast
        async with async_timeout.timeout(5):
            async with session.get(api_url) as response:
                if response.status == 200:
                    return await response.json(content_type=None)  # device sometimes sends text/html
                raise UpdateFailed(f"HTTP {response.status} from {api_url}")
    except (asyncio.TimeoutError, aiohttp.ClientError) as e:
        # Network/timeout -> handled as UpdateFailed so HA degrades gracefully
        raise UpdateFailed(f"Network error talking to {api_url}: {e}") from e


class DoorCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, config_entry):
        super().__init__(
            hass,
            logger=_LOGGER,  # your logger
            name="Door Coordinator",
            update_method=self._async_update,
            update_interval=timedelta(seconds=1),
        )

        self.entry = config_entry
        self.url = config_entry.data["url"]
        self.session = async_get_clientsession(hass)
        
        
    async def _async_update(self):
        return await fetch_status(self.session, self.url)