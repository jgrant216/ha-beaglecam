from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_USERNAME, CONF_PASSWORD
import voluptuous as vol
import aiohttp
import async_timeout
import logging

from .beaglecam_api import BeagleCamAPI
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

"""Config flow for BeagleCam integration."""

DATA_SCHEMA = vol.Schema({
    vol.Required(CONF_HOST): str,
    vol.Required(CONF_USERNAME): str,
    vol.Required(CONF_PASSWORD): str,
})


async def validate_input(data):
    host = data[CONF_HOST]
    username = data[CONF_USERNAME]
    password = data[CONF_PASSWORD]

    try:
        async with aiohttp.ClientSession() as session:
            async with async_timeout.timeout(5):
                api = BeagleCamAPI(host, username, password, session)
                response = await api.check_user()
                if "result" not in response:
                    raise Exception("Unexpected response format")
                if response.get("result", None) != 0:
                    raise Exception("Authentication failed")
                p2pid = (await api.get_info())["p2pid"]
    except Exception as e:
        _LOGGER.exception("Failed to connect to BeagleCam")
        raise

    return {"title": f"BeagleCam @ {host}", "p2pid": p2pid}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for BeagleCam."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            try:
                info = await validate_input(user_input)
                await self.async_set_unique_id(info["p2pid"])
                self._abort_if_unique_id_configured(updates={CONF_HOST: user_input[CONF_HOST], CONF_USERNAME: user_input[CONF_USERNAME], CONF_PASSWORD: user_input[CONF_PASSWORD]})
                return self.async_create_entry(title=info["title"], data=user_input)
            except Exception as e:
                return self.async_show_form(
                    step_id="user", data_schema=DATA_SCHEMA, errors={"base": str(e)}
                )

        return self.async_show_form(step_id="user", data_schema=DATA_SCHEMA)
