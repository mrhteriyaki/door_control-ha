import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.helpers import aiohttp_client

DOMAIN = "mrh_door_control"

CONFIG_SCHEMA = vol.Schema({
    vol.Required("url"): str,
    vol.Required("name", default="Door Controller x"): str,
    vol.Required("door_input_pin"): int,
    vol.Required("lock_output_pin"): int,
    vol.Required("stateless_lock",default=False): bool,
})


class MrhDoorControlConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            # Test if API is reachable
            session = aiohttp_client.async_get_clientsession(self.hass)
            try:
                async with session.get(user_input["url"]) as resp:
                    if resp.status != 200:
                        errors["base"] = "cannot_connect"
            except Exception:
                errors["base"] = "cannot_connect"
            if not errors:
                return self.async_create_entry(title=user_input["name"], data=user_input)
        return self.async_show_form(step_id="user", data_schema=CONFIG_SCHEMA, errors=errors)
    