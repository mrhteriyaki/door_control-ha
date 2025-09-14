from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from homeassistant.components.climate import DOMAIN as LOCK_DOMAIN

from .coordinator import DoorCoordinator

DOMAIN = "mrh_door_control"
PLATFORMS = ["lock","binary_sensor"]

async def async_setup(hass: HomeAssistant, config: dict):
    return True
    
#Config flow required.
async def async_setup_entry(hass: HomeAssistant, config: ConfigEntry):
    coordinator = DoorCoordinator(hass, config)
    hass.data.setdefault(DOMAIN, {})[config.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(config, PLATFORMS)   
    return True


async def async_unload_entry(hass: HomeAssistant, config: ConfigEntry):
    return await hass.config_entries.async_unload_platforms(config, PLATFORMS)