import logging
from datetime import datetime, timedelta

from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .beaglecam_api import PRINT_STATE, PRINT_STATE_PRINTING
from .const import DOMAIN
from .coordinator import BeagleCamDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

"""
Set up BeagleCam sensors based on a config entry.
"""

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry,
                            async_add_entities: AddConfigEntryEntitiesCallback):
    """Perform initial setup of the BeagleCam sensors based on a config entry."""
    coordinator: BeagleCamDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    device_id = entry.unique_id

    entities: list[SensorEntity] = \
        [BeagleCamTemperatureSensor(coordinator, tool, sensor_type, device_id) for tool in ("nozzle", "bed") for
         sensor_type in ("actual", "target")] + \
        [
            BeagleCamStatusSensor(coordinator, device_id),
            BeagleCamJobPercentageSensor(coordinator, device_id),
            BeagleCamFileNameSensor(coordinator, device_id),
            BeagleCamStartTimeSensor(coordinator, device_id),
            BeagleCamEstimatedFinishTimeSensor(coordinator, device_id),
            BeagleCamTotalLayerCountSensor(coordinator, device_id),
            BeagleCamCurrentLayerNumberSensor(coordinator, device_id),
        ]
    async_add_entities(entities)


def _is_printer_printing(printer: dict) -> bool:
    return (
            printer
            and printer["print_state"]
            and printer["print_state"] == PRINT_STATE_PRINTING
    )


class BeagleCamSensorBase(CoordinatorEntity[BeagleCamDataUpdateCoordinator], SensorEntity):
    """Representation of a BeagleCam sensor."""

    def __init__(
            self,
            coordinator: BeagleCamDataUpdateCoordinator,
            sensor_type: str,
            device_id: str,
    ) -> None:
        """Initialize a new BeagleCam sensor."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._attr_name = f"BeagleCam {sensor_type}"
        self._attr_unique_id = f"{sensor_type}-{device_id}"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return self.coordinator.device_info


class BeagleCamStatusSensor(BeagleCamSensorBase):
    """Status sensor for BeagleCam printer.

    State is one of the PRINT_STATE values:
        PRINT_STATE_PRINTING: "printing",
        PRINT_STATE_IDLE: "idle",
        PRINT_STATE_PAUSED: "paused",
        PRINT_STATE_COMPLETED: "completed",
    """
    _attr_icon = "mdi:printer-3d"

    def __init__(
            self, coordinator: BeagleCamDataUpdateCoordinator, device_id: str
    ) -> None:
        """Initialize a new BeagleCam sensor."""
        super().__init__(coordinator, "Current State", device_id)

    @property
    def native_value(self):
        """Return sensor state."""
        printer = self.coordinator.data.get("printer", None)
        if not printer or not printer.get("print_state", None):
            return None

        return PRINT_STATE[printer["print_state"]]

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success and self.coordinator.data["printer"]

    @property
    def extra_state_attributes(self):
        """Return additional attributes for the sensor."""
        tlv = self.coordinator.data.get("tlv", None)
        if not tlv:
            return None

        # Only include non-None attributes in the dictionary
        return {key: value for key, value in tlv.items() if value is not None}


class BeagleCamJobPercentageSensor(BeagleCamSensorBase):
    """Job completion percentage sensor for BeagleCam printer.

    If a print is paused, the percentage will not increase until printing is resumed.
    If a print is stopped, the percentage will remain at its last value.
    This behavior comes from the BeagleCam API.
    """
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_icon = "mdi:file-percent"

    def __init__(
            self, coordinator: BeagleCamDataUpdateCoordinator, device_id: str
    ) -> None:
        """Initialize a new BeagleCam sensor."""
        super().__init__(coordinator, "Job Percentage", device_id)

    @property
    def native_value(self):
        """Return sensor state."""
        job = self.coordinator.data.get("job", None)
        if not job:
            return None

        if not (state := job.get("progress", None)):
            return 0

        return round(state, 2)


class BeagleCamEstimatedFinishTimeSensor(BeagleCamSensorBase):
    """Estimated finish time sensor for BeagleCam printer.

    This is a minute-precision timestamp calculated by adding the time left
    to the last read time. If the printer is not currently printing, the sensor
    will return None.
    """
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(
            self, coordinator: BeagleCamDataUpdateCoordinator, device_id: str
    ) -> None:
        """Initialize a new BeagleCam sensor."""
        super().__init__(coordinator, "Job Estimated Finish Time", device_id)

    @property
    def native_value(self) -> datetime | None:
        """Return sensor state."""
        job = self.coordinator.data.get("job", None)
        if not job \
                or not (time_left := job.get("time_left", None)) \
                or not _is_printer_printing(self.coordinator.data["printer"]):
            return None

        read_time = self.coordinator.data["last_read_time"]

        return (read_time + timedelta(seconds=time_left)).replace(
            second=0
        )


class BeagleCamStartTimeSensor(BeagleCamSensorBase):
    """Start time sensor for BeagleCam printer.

    This is a minute-precision timestamp calculated by subtracting the time cost
    from the last read time. If the printer is not currently printing, the sensor
    will return None."""
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(
            self, coordinator: BeagleCamDataUpdateCoordinator, device_id: str
    ) -> None:
        """Initialize a new BeagleCam sensor."""
        super().__init__(coordinator, "Job Start Time", device_id)

    @property
    def native_value(self) -> datetime | None:
        """Return sensor state."""
        job = self.coordinator.data.get("job", None)
        if not job \
                or not (time_cost := job.get("time_cost", None)) \
                or not _is_printer_printing(self.coordinator.data["printer"]):
            return None

        read_time = self.coordinator.data["last_read_time"]

        return (read_time - timedelta(seconds=time_cost)).replace(
            second=0
        )


class BeagleCamTemperatureSensor(BeagleCamSensorBase):
    """Temperature sensor for BeagleCam printer.

    This sensor can represent either the actual or target temperature for both
    the nozzle and the bed. One instance of this class is created for each combination.

    The API provides only whole number temperatures.
    """
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_suggested_display_precision = 0

    def __init__(
            self,
            coordinator: BeagleCamDataUpdateCoordinator,
            tool: str,  # e.g., "nozzle", "bed"
            temp_type: str,  # "actual" or "target"
            device_id: str,
    ) -> None:
        """Initialize a new BeagleCam sensor."""
        super().__init__(coordinator, f"{temp_type} {tool} temp", device_id)
        self._temp_type = temp_type
        self._api_tool = tool
        # Determine the key to look for based on temp_type and tool
        self.key = ("des_" if self._temp_type == "target" else "") + "tempture_" + self._api_tool[0:3]

    @property
    def native_value(self):
        printer = self.coordinator.data.get("printer", None)
        if not printer:
            return None

        return round(printer.get(self.key, None), 0) if printer.get(self.key, None) is not None else None

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success and self.coordinator.data["printer"]


class BeagleCamFileNameSensor(BeagleCamSensorBase):
    """File name sensor for BeagleCam printer.

    Similar to the job completion percentage sensor, if a print is paused or stopped,
    the file name will remain the same until a new print is started or the stop/completed
    button is pressed in the BeagleCam interface.
    """

    def __init__(
            self,
            coordinator: BeagleCamDataUpdateCoordinator,
            device_id: str,
    ) -> None:
        """Initialize a new BeagleCam sensor."""
        super().__init__(coordinator, "Current File", device_id)

    @property
    def native_value(self) -> str | None:
        """Return sensor state."""
        job = self.coordinator.data.get("job", None)

        return job.get("file_name", None)

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        if not self.coordinator.last_update_success:
            return False
        job = self.coordinator.data.get("job", None)
        return job and "file_name" in job

class BeagleCamTotalLayerCountSensor(BeagleCamSensorBase):
    """Sensor that exposes layerCount field returned by get_model_info."""
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: BeagleCamDataUpdateCoordinator,
        device_id: str,
    ) -> None:
        super().__init__(coordinator, device_id, "total_layer_count")

        # How it appears in Home Assistant
        self._attr_name = "BeagleCam Total Layers"

    @property
    def native_value(self):
        """Return sensor value."""
        job = self.coordinator.data.get("job", None)
        if not job \
                or not (layerCount := job.get("layerCount", None)) \
                or not _is_printer_printing(self.coordinator.data["printer"]):
            return None

        return int(layerCount)

    @property
    def icon(self):
        return "mdi:numeric-1-box-multiple-outline"

class BeagleCamCurrentLayerNumberSensor(BeagleCamSensorBase):
    """Sensor that exposes layerIndex field returned by get_print_status."""
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: BeagleCamDataUpdateCoordinator,
        device_id: str,
    ) -> None:
        super().__init__(coordinator, device_id, "current_layer_index")

        # How it appears in Home Assistant
        self._attr_name = "BeagleCam Current Layer Index"

    @property
    def native_value(self):
        """Return sensor value."""
        job = self.coordinator.data.get("job", None)
        if not job \
                or not (layerIndex := job.get("layerIndex", None)) \
                or not _is_printer_printing(self.coordinator.data["printer"]):
            return None

        return int(layerIndex)

    @property
    def icon(self):
        return "mdi:numeric-1-box-multiple-outline"
