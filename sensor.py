from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([BeagleCamStatusSensor(coordinator)])

class BeagleCamStatusSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "BeagleCam Print Status"
        self._attr_unique_id = "beaglecam_print_status"

    @property
    def state(self):
        # Choose a representative value (e.g., progress or status)
        return self.coordinator.data.get("progress", "unknown")

    @property
    def extra_state_attributes(self):
        # Return the full response as attributes
        return self.coordinator.data
