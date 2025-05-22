from homeassistant import config_entries
from homeassistant.core import callback
import voluptuous as vol
import aiohttp
import async_timeout
import logging

from .const import DOMAIN, CONF_IP, CONF_USERNAME, CONF_PASSWORD

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema({
    vol.Required(CONF_IP): str,
    vol.Required(CONF_USERNAME): str,
    vol.Required(CONF_PASSWORD): str,
})

async def validate_input(data):
    ip = data[CONF_IP]
    username = data[CONF_USERNAME]
    password = data[CONF_PASSWORD]
    url = f"http://{ip}/set3DPiCmd"

    payload = {
        "cmd": 312,
        "pro": "get_prconnectstate",
        "user": username,
        "pwd": password
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with async_timeout.timeout(5):
                async with session.post(url, json=payload) as response:
                    if response.status != 200:
                        raise Exception("Invalid response")
                    resp_json = await response.json()
                    # You may want to verify a key in the JSON, like 'result': 'ok'
                    if "result" not in resp_json:
                        raise Exception("Unexpected response format")
    except Exception as e:
        _LOGGER.exception("Failed to connect to BeagleCam")
        raise

    return {"title": f"BeagleCam @ {ip}"}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for BeagleCam."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            try:
                info = await validate_input(user_input)
                return self.async_create_entry(title=info["title"], data=user_input)
            except Exception:
                return self.async_show_form(
                    step_id="user", data_schema=DATA_SCHEMA, errors={"base": "cannot_connect"}
                )

        return self.async_show_form(step_id="user", data_schema=DATA_SCHEMA)
