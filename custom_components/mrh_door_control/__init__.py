from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from homeassistant.components.climate import DOMAIN as LOCK_DOMAIN

from .coordinator import DoorCoordinator

DOMAIN = "mrh_door_control"
PLATFORMS = ["lock","binary_sensor"]
# hass.data[DOMAIN][COORDINATORS] maps device URL -> (coordinator, set of entry ids using it)
COORDINATORS = "coordinators"

async def async_setup(hass: HomeAssistant, config: dict):
    return True


def _device_key(url: str) -> str:
    return url.rstrip("/").lower()


#Config flow required.
async def async_setup_entry(hass: HomeAssistant, config: ConfigEntry):
    domain_data = hass.data.setdefault(DOMAIN, {})
    coordinators = domain_data.setdefault(COORDINATORS, {})
    key = _device_key(config.data["url"])
    # Entries for different doors on the same device share one coordinator, so the device gets one poll
    if key not in coordinators:
        coordinators[key] = (DoorCoordinator(hass, config.data["url"]), set())
    coordinator, entry_ids = coordinators[key]
    entry_ids.add(config.entry_id)
    domain_data[config.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(config, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, config: ConfigEntry):
    unload_ok = await hass.config_entries.async_unload_platforms(config, PLATFORMS)
    if unload_ok:
        domain_data = hass.data[DOMAIN]
        # Look up by the coordinator's URL, not config.data: a reconfigure has already changed the URL by the time it reloads
        coordinator = domain_data.pop(config.entry_id)
        coordinators = domain_data[COORDINATORS]
        key = _device_key(coordinator.url)
        coordinator, entry_ids = coordinators[key]
        entry_ids.discard(config.entry_id)
        if not entry_ids:
            del coordinators[key]
            await coordinator.async_shutdown()
    return unload_ok
