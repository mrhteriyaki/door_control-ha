import requests
import aiohttp
import asyncio 
import logging  

from datetime import timedelta

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

DOMAIN = "mrh_door_control"
_LOGGER = logging.getLogger(__name__)

async def fetch_status(api_url: str) -> dict:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url) as response:
                if response.status == 200:
                    #(content_type=None) Forces acceptance of the text/html header as device does not always use application/json
                    return await response.json(content_type=None)
                else:
                    raise Exception(f"Error fetching status: {response.status}")
    except Exception as e:
        raise Exception(f"Failed to fetch data from server: {str(e)}")


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
        
        
    async def _async_update(self):
        # Fetch and return data from your API
        try:
            return await fetch_status(self.url)
        except requests.RequestException as ex:
            _LOGGER.error("Error updating door control state: %s", ex)
            raise