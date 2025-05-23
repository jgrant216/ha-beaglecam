from datetime import timedelta
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN, DEFAULT_SCAN_INTERVAL
from .beaglecam_api import BeagleCamAPI

import logging
_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    api = BeagleCamAPI(
        entry.data["ip_address"],
        entry.data["username"],
        entry.data["password"],
        async_get_clientsession(hass),
    )

    async def async_update_data():
        try:
            print_status = await api.get_print_status()
            temp_status = await api.get_temperature_status()

            # Merge responses, excluding duplicate 'cmd' keys etc.
            combined = {
                **{k: v for k, v in print_status.items() if k != "cmd"},
                **{k: v for k, v in temp_status.items() if k != "cmd"},
            }

            _LOGGER.debug("Combined BeagleCam data: %s", combined)
            return combined

        except Exception as err:
            _LOGGER.error("Error fetching BeagleCam data: %s", err)
            raise UpdateFailed(f"Data fetch failed: {err}")

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="beaglecam",
        update_method=async_update_data,
        update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL)
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Unload any platforms this integration sets up, e.g. sensors
    unload_ok = await hass.config_entries.async_unload_platforms(entry, ["sensor"])

    if unload_ok:
        # Clean up stored data
        hass.data[DOMAIN].pop(entry.entry_id, None)

    return unload_ok

async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload a config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
