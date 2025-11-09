
from homeassistant.components.camera import Camera, CameraEntityFeature
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from propcache.api import cached_property
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([BeagleCamCamera(coordinator)])

class BeagleCamCamera(CoordinatorEntity, Camera):
    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "BeagleCam Camera"
        self._attr_unique_id = "beaglecam_camera"
        self._attr_brand = "Mintion"

    @cached_property
    def supported_features(self) -> CameraEntityFeature:
        return CameraEntityFeature.STREAM

    @cached_property
    def stream_source(self) -> str | None:
        return self.coordinator.data.get("IPaddress", "unknown") % "rtsp://%s:554/0"

    @cached_property
    def use_stream_for_stills(self) -> bool:
        return True

    @cached_property
    def model(self) -> str | None:
        return self.coordinator.data.get("hardware", "unknown")
