from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .beaglecam_api import PRINT_STATE_PRINTING
from .const import DOMAIN
from .coordinator import BeagleCamDataUpdateCoordinator


async def async_setup_entry(
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the available OctoPrint binary sensors."""
    coordinator: BeagleCamDataUpdateCoordinator = hass.data[DOMAIN][
        config_entry.entry_id
    ]["coordinator"]
    device_id = config_entry.unique_id

    entities: list[BinarySensorEntity] = [
        BeagleCamPrintingBinarySensor(coordinator, device_id),
    ]

    async_add_entities(entities)


class BeagleCamPrintingBinarySensor(CoordinatorEntity[BeagleCamDataUpdateCoordinator], BinarySensorEntity):
    def __init__(
            self,
            coordinator: BeagleCamDataUpdateCoordinator,
            device_id: str,
    ) -> None:
        """Initialize a new beaglecam printing sensor."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._attr_name = "BeagleCam Printing"
        self._attr_unique_id = f"printing-{device_id}"
        self._attr_device_info = coordinator.DeviceInfo

    @property
    def is_on(self):
        """Return true if binary sensor is on."""
        if not (printer := self.coordinator.data["printer"]):
            return None

        return self.available and bool(printer["print_state"] == PRINT_STATE_PRINTING)

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success and self.coordinator.data["printer"]["connect_state"] == 1

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return self.coordinator.device_info
