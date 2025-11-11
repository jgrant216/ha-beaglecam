from .beaglecam_api import BeagleCamAPI
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_USERNAME, CONF_PASSWORD
import voluptuous as vol
import aiohttp
import async_timeout
import logging

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema({
    vol.Required(CONF_HOST): str,
    vol.Required(CONF_USERNAME): str,
    vol.Required(CONF_PASSWORD): str,
})


async def validate_input(data):
    ip = data[CONF_HOST]
    username = data[CONF_USERNAME]
    password = data[CONF_PASSWORD]

    try:
        async with aiohttp.ClientSession() as session:
            async with async_timeout.timeout(5):
                api = BeagleCamAPI(ip, username, password, session)
                response = await api.check_user()
                if "result" not in response:
                    raise Exception("Unexpected response format")
                if response.get("result", None) != 0:
                    raise Exception("Authentication failed")
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
