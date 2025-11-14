import logging
import yarl

from homeassistant.components.camera import Camera, CameraEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_USERNAME, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import TemplateError
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.template import Template
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import BeagleCamDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

"""Camera entity representing the BeagleCam camera and its RTSP stream."""

async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry,
                            async_add_entities: AddConfigEntryEntitiesCallback):
    """Set up the BeagleCam camera based on a config entry."""
    coordinator: BeagleCamDataUpdateCoordinator = hass.data[DOMAIN][
        config_entry.entry_id
    ]["coordinator"]
    async_add_entities([BeagleCamCamera(hass, coordinator, config_entry)])


class BeagleCamCamera(CoordinatorEntity[BeagleCamDataUpdateCoordinator], Camera):
    """Representation of a BeagleCam camera."""
    def __init__(self, hass: HomeAssistant, coordinator: BeagleCamDataUpdateCoordinator,
                 config_entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        Camera.__init__(self)
        self._attr_name = "BeagleCam Camera"
        self._attr_unique_id = config_entry.unique_id
        self._attr_brand = "Mintion"
        self._attr_model = coordinator.device_info.get("model", "BeagleCam")
        self._username = config_entry.data.get(CONF_USERNAME)
        self._password = config_entry.data.get(CONF_PASSWORD)
        self._ip_address = Template(config_entry.data.get(CONF_HOST), hass)
        self._attr_supported_features = CameraEntityFeature.STREAM
        self.stream_options["rtsp_transport"] = "tcp"

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
        """Return True, because BeagleCam does not support still images."""
        return True

    async def async_camera_image(
            self, width: int | None = None, height: int | None = None
    ) -> bytes | None:
        """
        The BeagleCam does not support still images, so we return None.
        """
        return None

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return self.coordinator.device_info
