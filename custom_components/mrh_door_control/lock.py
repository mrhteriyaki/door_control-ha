import logging
import requests
import voluptuous as vol
import aiohttp
import asyncio

from .coordinator import DoorCoordinator
from datetime import timedelta
from homeassistant import config_entries
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from homeassistant.components.lock.const import LockState
from homeassistant.components.lock import (
    LockEntity,
    LockEntityFeature,
    PLATFORM_SCHEMA,
    ATTR_CODE,
    SERVICE_OPEN,
)

DOMAIN = "mrh_door_control"
_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    name = config_entry.data["name"]
    url = config_entry.data["url"]
    lock_pin = config_entry.data["lock_output_pin"]
    if "stateless_lock" in config_entry.data:
        stateless_lock = config_entry.data["stateless_lock"]
    else:
        stateless_lock = False
    async_add_entities([MrhDoorControlLock(coordinator,name,url,lock_pin,stateless_lock)])



class MrhDoorControlLock(CoordinatorEntity,LockEntity):
    
    def __init__(self, coordinator, name, url, lock_pin,stateless_lock):
        super().__init__(coordinator)
        self._name = name
        self._url = url
        self._uid = url.replace("http://", "").replace("https://","").replace(".", "_") + "_" + str(lock_pin)
        self._lock_state = None
        self._lock_pin = lock_pin
        self._stateless_lock = stateless_lock
    
    @property
    def name(self):
        return self._name

    @property
    def is_locked(self):
        if self._stateless_lock == True:
            return None
        elif self.coordinator.data == None:
            return None
        elif self.coordinator.data.get(("D" + str(self._lock_pin))) == 0:
            return True
        elif self.coordinator.data.get(("D" + str(self._lock_pin))) == 1:
            return False
        return None
       
    @property
    def device_info(self):
        return {
        "identifiers": {(DOMAIN, self._url)},
        "name": self._name + " - Lock",
        }  
               
    @property
    def unique_id(self):
        return self._uid 
    
    @property
    def supported_features(self):
        if self._stateless_lock == True:
            return LockEntityFeature.OPEN
        else:
            return 0 #Normal lock/unlock feature.

    async def send_control_command(self, payload):
        headers = {'Content-Type': 'text/plain'}
        async with aiohttp.ClientSession() as session:
            async with session.post(self._url, data=payload, headers=headers) as response:
                if response.status != 200:
                    _LOGGER.error(f"Failed to send command {payload}. Server: {self._url} Response Status: {response.status}")


    async def async_unlock(self, **kwargs):
        self._lock_state = False
        await self.send_control_command("D" + str(self._lock_pin) + ":1")
        await self.coordinator.async_request_refresh()

    async def async_lock(self, **kwargs):
        self._lock_state = True
        await self.send_control_command("D" + str(self._lock_pin) + ":0")
        await self.coordinator.async_request_refresh()

             
    async def async_open(self, **kwargs):
        await self.send_control_command("T" + str(self._lock_pin) + ":500")
        await self.coordinator.async_request_refresh()