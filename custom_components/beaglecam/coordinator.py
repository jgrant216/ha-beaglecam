import asyncio
import logging
from datetime import timedelta

from aiohttp.web_exceptions import HTTPError

from yarl import URL

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_HOST
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt
from .beaglecam_api import BeagleCamAPI
from .const import DOMAIN, DEFAULT_SCAN_INTERVAL

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

    async def _async_update_data(self):
        if self._beaglecam.closed:
            _LOGGER.debug("BeagleCam session is closed. Stopping updates. BeagleCam: %s, session: %s, config: %s", self._beaglecam, self._beaglecam._session, self.config_entry)
            _LOGGER.debug(self.data)
            raise UpdateFailed("BeagleCam session is closed")

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
            printer_state = {
                **{k: v for k, v in temp_status.items() if k not in ("cmd", "result")},
                **{k: v for k, v in connection.items() if k not in ("cmd", "result")},
            }
            job_state = {
                ** {k: v for k, v in print_status.items() if k not in ("cmd", "result")},
            }

            _LOGGER.debug("Combined BeagleCam data: %s", printer_state)
            _LOGGER.debug("Combined BeagleCam Job data: %s", job_state)
            return {"job": job_state, "printer": printer_state, "last_read_time": dt.utcnow()}

        except HTTPError as httperr:
            _LOGGER.exception("BeagleCam HTTP error: %s status: %s reason: %s", httperr, httperr.status, httperr.reason)
            raise UpdateFailed(f"Data fetch failed: {httperr}") from httperr
        except Exception as err:
            _LOGGER.exception("BeagleCam polling error: %s", err)
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
        configuration_url = URL.build(scheme="http", host=self.config_entry.data[CONF_HOST])

        return DeviceInfo(
            identifiers={(DOMAIN, self.config_entry.unique_id)},
            manufacturer="Mintion",
            name=self.data.get("camera", {}).get('hardware', 'BeagleCam'),
            configuration_url=str(configuration_url),
            model=self.data.get("camera", {}).get('hardware', 'BeagleCam'),
        )
