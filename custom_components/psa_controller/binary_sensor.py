"""Binary sensors for PSA Controller."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DATA_COORDINATOR, DOMAIN
from .coordinator import PsaControllerDataUpdateCoordinator
from .entity import PsaControllerEntity, vehicle_value


@dataclass(frozen=True, kw_only=True)
class PsaBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Describe a PSA Controller binary sensor."""

    value_fn: Callable[[dict[str, Any]], bool | None]


def _engine_running(data: dict[str, Any]) -> bool | None:
    """Return whether the engine is running."""
    ignition = vehicle_value(data, "ignition", "type")
    if ignition is None:
        return None
    return ignition != "Stop"


BINARY_SENSORS: tuple[PsaBinarySensorEntityDescription, ...] = (
    PsaBinarySensorEntityDescription(
        key="plugged_in",
        name="Plugged In",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        value_fn=lambda data: vehicle_value(data, "energy", 0, "charging", "plugged"),
    ),
    PsaBinarySensorEntityDescription(
        key="position",
        translation_key="moving",
        device_class=BinarySensorDeviceClass.MOVING,
        value_fn=lambda data: vehicle_value(data, "kinetic", "moving"),
    ),
    PsaBinarySensorEntityDescription(
        key="engine_running",
        name="Engine Running",
        device_class=BinarySensorDeviceClass.POWER,
        value_fn=_engine_running,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up PSA Controller binary sensors."""
    coordinator: PsaControllerDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id][
        DATA_COORDINATOR
    ]
    async_add_entities(
        PsaBinarySensor(coordinator, description) for description in BINARY_SENSORS
    )


class PsaBinarySensor(PsaControllerEntity, BinarySensorEntity):
    """Representation of a PSA Controller binary sensor."""

    entity_description: PsaBinarySensorEntityDescription

    def __init__(
        self,
        coordinator: PsaControllerDataUpdateCoordinator,
        description: PsaBinarySensorEntityDescription,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        value = self.entity_description.value_fn(self.coordinator.data)
        if value is None:
            return None
        return bool(value)
