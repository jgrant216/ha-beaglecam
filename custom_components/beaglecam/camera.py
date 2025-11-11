import logging

from typing import Mapping, Any

import yarl
from homeassistant.components.camera import Camera, CameraEntityFeature
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import TemplateError
from homeassistant.helpers.template import Template
from .const import CONF_USERNAME, CONF_PASSWORD

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([BeagleCamCamera(hass, entry.data, entry.entry_id)])

class BeagleCamCamera(Camera):
    def __init__(self, hass: HomeAssistant, device_info: Mapping[str, Any], identifier: str) -> None:
        super().__init__()
        self._attr_name = "BeagleCam Camera"
        self._attr_unique_id = identifier
        self._attr_brand = "Mintion"
        self._attr_model = "BeagleCam v2"
        self._username = device_info.get(CONF_USERNAME)
        self._password = device_info.get(CONF_PASSWORD)
        self._ip_address = Template(device_info.get(CONF_HOST), hass)
        self._attr_supported_features = CameraEntityFeature.STREAM
        self.stream_options["rtsp_transport"] = "TCP"

    async def stream_source(self) -> str | None:
        """Return the source of the stream."""
        if self._ip_address is None:
            return None

        try:
            stream_addr = self._ip_address.async_render(parse_result=False)
            url = yarl.URL("rtsp://%s:554/0" % stream_addr)
            if (
                    not url.user
                    and not url.password
                    and self._username
                    and self._password
                    and url.is_absolute()
            ):
                url = url.with_user(self._username).with_password(self._password)
            return str(url)
        except TemplateError as err:
            _LOGGER.error("Error parsing template %s: %s", self._ip_address, err)
            return None

    @property
    def use_stream_for_stills(self) -> bool:
        return True

    async def async_camera_image(
            self, width: int | None = None, height: int | None = None
    ) -> bytes | None:
        """
        The BeagleCam does not support still images, so we return None.
        """
        return None