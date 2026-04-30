"""Sensors for PSA Controller."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfLength, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DATA_COORDINATOR, DOMAIN
from .coordinator import PsaControllerDataUpdateCoordinator
from .entity import PsaControllerEntity, charge_control_value, vehicle_value


@dataclass(frozen=True, kw_only=True)
class PsaSensorEntityDescription(SensorEntityDescription):
    """Describe a PSA Controller sensor."""

    value_fn: Callable[[dict[str, Any]], Any]


def _total_range(data: dict[str, Any]) -> int | None:
    """Return the combined electric and fuel range if available."""
    electric = vehicle_value(data, "energy", 0, "autonomy")
    fuel = vehicle_value(data, "energy", 1, "autonomy")
    if electric is None and fuel is None:
        return None
    return int(electric or 0) + int(fuel or 0)


SENSORS: tuple[PsaSensorEntityDescription, ...] = (
    PsaSensorEntityDescription(
        key="charging_status",
        name="Charging Status",
        value_fn=lambda data: vehicle_value(data, "energy", 0, "charging", "status"),
    ),
    PsaSensorEntityDescription(
        key="battery_level",
        name="Battery Level",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: vehicle_value(data, "energy", 0, "level"),
    ),
    PsaSensorEntityDescription(
        key="mileage",
        name="Mileage",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:road-variant",
        value_fn=lambda data: vehicle_value(data, "timed_odometer", "mileage"),
    ),
    PsaSensorEntityDescription(
        key="range",
        name="Range",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:map-marker-distance",
        value_fn=lambda data: vehicle_value(data, "energy", 0, "autonomy"),
    ),
    PsaSensorEntityDescription(
        key="preconditioning_status",
        name="Preconditioning Status",
        value_fn=lambda data: vehicle_value(
            data, "preconditionning", "air_conditioning", "status"
        ),
    ),
    PsaSensorEntityDescription(
        key="charging_mode",
        name="Charging Mode",
        icon="mdi:lightning-bolt",
        value_fn=lambda data: vehicle_value(
            data, "energy", 0, "charging", "charging_mode"
        ),
    ),
    PsaSensorEntityDescription(
        key="charge_rate",
        name="Charge Rate",
        native_unit_of_measurement="mph",
        device_class=SensorDeviceClass.SPEED,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:speedometer",
        value_fn=lambda data: vehicle_value(
            data, "energy", 0, "charging", "charging_rate"
        ),
    ),
    PsaSensorEntityDescription(
        key="next_stop_time",
        name="Next Stop Time",
        value_fn=lambda data: charge_control_value(data, "_next_stop_hour"),
    ),
    PsaSensorEntityDescription(
        key="charge_threshold",
        name="Charge Threshold",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: charge_control_value(data, "percentage_threshold"),
    ),
    PsaSensorEntityDescription(
        key="fuel_level",
        name="Fuel Level",
        native_unit_of_measurement=PERCENTAGE,
        icon="mdi:gas-station",
        value_fn=lambda data: vehicle_value(data, "energy", 1, "level"),
    ),
    PsaSensorEntityDescription(
        key="fuel_range",
        name="Fuel Range",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        device_class=SensorDeviceClass.DISTANCE,
        icon="mdi:map-marker-distance",
        value_fn=lambda data: vehicle_value(data, "energy", 1, "autonomy"),
    ),
    PsaSensorEntityDescription(
        key="total_range",
        name="Total Range",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        device_class=SensorDeviceClass.DISTANCE,
        icon="mdi:calculator",
        value_fn=_total_range,
    ),
    PsaSensorEntityDescription(
        key="outside_temperature",
        name="Outside Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        value_fn=lambda data: vehicle_value(data, "environment", "air", "temp"),
    ),
    PsaSensorEntityDescription(
        key="12v_battery_status",
        name="12V Battery Status",
        native_unit_of_measurement=PERCENTAGE,
        icon="mdi:battery-check",
        value_fn=lambda data: vehicle_value(data, "battery", "voltage"),
    ),
    PsaSensorEntityDescription(
        key="ignition_status",
        name="Ignition Status",
        icon="mdi:engine",
        value_fn=lambda data: vehicle_value(data, "ignition", "type"),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up PSA Controller sensors."""
    coordinator: PsaControllerDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id][
        DATA_COORDINATOR
    ]
    async_add_entities(PsaSensor(coordinator, description) for description in SENSORS)


class PsaSensor(PsaControllerEntity, SensorEntity):
    """Representation of a PSA Controller sensor."""

    entity_description: PsaSensorEntityDescription

    def __init__(
        self,
        coordinator: PsaControllerDataUpdateCoordinator,
        description: PsaSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> Any:
        """Return the sensor state."""
        return self.entity_description.value_fn(self.coordinator.data)
