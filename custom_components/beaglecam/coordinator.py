import asyncio
import logging
from datetime import timedelta

from aiohttp.web_exceptions import HTTPError

from typing import cast
from yarl import URL

from homeassistant.config_entries import ConfigEntry
from const import CONF_IP, DOMAIN, DEFAULT_SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from .beaglecam_api import BeagleCamAPI

_LOGGER = logging.getLogger(__name__)


class BeagleCamDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the BeagleCam API"""

    config_entry: ConfigEntry

    def __init__(
            self,
            hass: HomeAssistant,
            beaglecam: BeagleCamAPI,
            config_entry: ConfigEntry,
            interval: int = DEFAULT_SCAN_INTERVAL,
    ) -> None:
        """Initialize."""
        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name=f"beaglecam-{config_entry.entry_id}",
            update_interval=timedelta(seconds=interval),
        )
        self._beaglecam = beaglecam
        self._printer_offline = False
        self.data = {"camera": None, "printer": None, "job": None, "last_read_time": None}

    async def async_update_data(self):
        try:
            try:
                connection = await self._beaglecam.get_connection_state()
            except Exception as err:
                _LOGGER.debug("BeagleCam is offline. Polling again in 300s.")
                await asyncio.sleep(300)  # throttle manually
                return None

            # Printer is online – proceed with normal status polling
            print_status = await self._beaglecam.get_print_status()
            temp_status = await self._beaglecam.get_temperature_status()

            # Merge API responses
            combined = {
                **{k: v for k, v in print_status.items() if k != "cmd"},
                **{k: v for k, v in temp_status.items() if k != "cmd"},
                **{k: v for k, v in connection.items() if k not in ("cmd", "result")},
            }

            _LOGGER.debug("Combined BeagleCam data: %s", combined)
            return combined
            # return {"job": job, "printer": printer, "last_read_time": dt_util.utcnow()}

        except HTTPError as httperr:
            _LOGGER.warning("BeagleCam HTTP error: %s status: %s reason: %s", httperr, httperr.status, httperr.reason)
            raise UpdateFailed(f"Data fetch failed: {httperr}") from httperr
        except Exception as err:
            _LOGGER.warning("BeagleCam polling error: %s", err)
            raise UpdateFailed(f"Data fetch failed: {err}") from err

    async def _async_setup(self) -> None:
        """Set up the coordinator.
        """
        try:
            self.data["camera"] = await self._beaglecam.get_info()
        except HTTPError as httperr:
            _LOGGER.warning("BeagleCam HTTP error: %s status: %s reason: %s", httperr, httperr.status, httperr.reason)
            raise UpdateFailed(f"Data fetch failed: {httperr}") from httperr
        except Exception as err:
            _LOGGER.warning("BeagleCam polling error: %s", err)
            raise UpdateFailed(f"Data fetch failed: {err}") from err

    @property
    def device_info(self) -> DeviceInfo:
        """Device info."""
        unique_id = cast(str, self.config_entry.unique_id)
        configuration_url = URL.build(scheme="http", host=self.config_entry.data[CONF_IP])

        return DeviceInfo(
            identifiers={(DOMAIN, unique_id)},
            manufacturer="Mintion",
            name=self.data["camera"].get('hardware', 'BeagleCam'),
            configuration_url=str(configuration_url),
        )
