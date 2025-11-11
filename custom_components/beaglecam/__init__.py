
from typing import cast

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_HOMEASSISTANT_STOP, CONF_DEVICE_ID, Platform, CONF_HOST, CONF_USERNAME, CONF_PASSWORD
from homeassistant.core import HomeAssistant, callback, Event, ServiceCall
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import device_registry
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .beaglecam_api import BeagleCamAPI
from .const import DOMAIN, DEFAULT_SCAN_INTERVAL, SERVICE_PR_CONNECT
from .coordinator import BeagleCamDataUpdateCoordinator

import logging

PLATFORMS = [Platform.SENSOR, Platform.CAMERA]

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    hass.data.setdefault(DOMAIN, {})
    session = async_get_clientsession(hass)

    api = BeagleCamAPI(
        entry.data[CONF_HOST],
        entry.data[CONF_USERNAME],
        entry.data[CONF_PASSWORD],
        session
    )

    @callback
    def _async_close_websession(event: Event | None = None) -> None:
        """Close websession."""
        session.detach()

    entry.async_on_unload(_async_close_websession)
    entry.async_on_unload(
        hass.bus.async_listen(EVENT_HOMEASSISTANT_STOP, _async_close_websession)
    )

    bc_coordinator = BeagleCamDataUpdateCoordinator(hass, api, entry, DEFAULT_SCAN_INTERVAL)

    await bc_coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": bc_coordinator,
        "api": api,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    async def async_printer_connect(call: ServiceCall) -> None:
        """Connect to a printer."""
        client = async_get_client_for_service_call(hass, call)
        await client.connect_printer()

    if not hass.services.has_service(DOMAIN, SERVICE_PR_CONNECT):
        hass.services.async_register(
            DOMAIN,
            SERVICE_PR_CONNECT,
            async_printer_connect
        )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Unload any platforms this integration sets up, e.g. sensors
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        # Clean up stored data
        hass.data[DOMAIN].pop(entry.entry_id, None)

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload a config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)


def async_get_client_for_service_call(
        hass: HomeAssistant, call: ServiceCall
) -> BeagleCamAPI:
    """Get the client related to a service call (by device ID)."""
    device_id = call.data[CONF_DEVICE_ID]
    device_reg = device_registry.async_get(hass)

    if device_entry := device_reg.async_get(device_id):
        for entry_id in device_entry.config_entries:
            if data := hass.data[DOMAIN].get(entry_id):
                return cast(BeagleCamAPI, data["api"])

    raise ServiceValidationError(
        translation_domain=DOMAIN,
        translation_key="missing_client",
        translation_placeholders={
            "device_id": device_id,
        },
    )
