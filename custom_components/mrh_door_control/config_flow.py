import voluptuous as vol
import async_timeout
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.helpers import aiohttp_client
from homeassistant.helpers import device_registry as dr, entity_registry as er

from .coordinator import REQUEST_HEADERS, REQUEST_TIMEOUT, entity_uid_prefix

DOMAIN = "mrh_door_control"

CONFIG_SCHEMA = vol.Schema({
    vol.Required("url"): str,
    vol.Required("name", default="Door Controller x"): str,
    vol.Required("door_input_pin"): int,
    vol.Required("lock_output_pin"): int,
    vol.Required("stateless_lock",default=False): bool,
})


async def _async_can_connect(hass: HomeAssistant, url: str) -> bool:
    # Test if API is reachable
    session = aiohttp_client.async_get_clientsession(hass)
    try:
        async with async_timeout.timeout(REQUEST_TIMEOUT):
            async with session.get(url, headers=REQUEST_HEADERS) as resp:
                return resp.status == 200
    except Exception:
        return False


def _async_move_registry_entries(hass: HomeAssistant, entry, old_url: str, new_url: str):
    # Entity unique_ids and the device identifier are built from the URL, so carry them over
    # to the new URL; otherwise the reload creates new entities and orphans the old ones.
    old_prefix = entity_uid_prefix(old_url) + "_"
    new_prefix = entity_uid_prefix(new_url) + "_"
    ent_reg = er.async_get(hass)
    for ent in er.async_entries_for_config_entry(ent_reg, entry.entry_id):
        if ent.unique_id.startswith(old_prefix):
            ent_reg.async_update_entity(ent.entity_id, new_unique_id=new_prefix + ent.unique_id[len(old_prefix):])

    dev_reg = dr.async_get(hass)
    device = dev_reg.async_get_device(identifiers={(DOMAIN, old_url)})
    if device is not None:
        dev_reg.async_update_device(device.id, new_identifiers={(DOMAIN, new_url)})


class MrhDoorControlConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            if not await _async_can_connect(self.hass, user_input["url"]):
                errors["base"] = "cannot_connect"
            if not errors:
                return self.async_create_entry(title=user_input["name"], data=user_input)
        return self.async_show_form(step_id="user", data_schema=CONFIG_SCHEMA, errors=errors)

    async def async_step_reconfigure(self, user_input=None):
        # Lets a device's URL be changed (e.g. new IP) while keeping its entities and history
        entry = self._get_reconfigure_entry()
        errors = {}
        if user_input is not None:
            new_url = user_input["url"]
            if not await _async_can_connect(self.hass, new_url):
                errors["base"] = "cannot_connect"
            if not errors:
                old_url = entry.data["url"]
                if new_url != old_url:
                    _async_move_registry_entries(self.hass, entry, old_url, new_url)
                return self.async_update_reload_and_abort(entry, data_updates={"url": new_url})
        schema = vol.Schema({vol.Required("url", default=entry.data["url"]): str})
        return self.async_show_form(step_id="reconfigure", data_schema=schema, errors=errors)

