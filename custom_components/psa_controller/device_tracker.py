"""Device tracker for PSA Controller."""

from __future__ import annotations

import os

from homeassistant.components.device_tracker import SourceType, TrackerEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DATA_COORDINATOR, DOMAIN
from .coordinator import PsaControllerDataUpdateCoordinator
from .entity import PsaControllerEntity, vehicle_value
from .image import local_vehicle_image_path, public_vehicle_image_url


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up PSA Controller device tracker."""
    coordinator: PsaControllerDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id][
        DATA_COORDINATOR
    ]
    async_add_entities([PsaVehicleTracker(coordinator)])


class PsaVehicleTracker(PsaControllerEntity, TrackerEntity):
    """GPS device tracker with optional cached vehicle image."""

    _attr_translation_key = "vehicle"

    def __init__(self, coordinator: PsaControllerDataUpdateCoordinator) -> None:
        """Initialize the tracker."""
        super().__init__(coordinator, "vehicle")

    @property
    def latitude(self) -> float | None:
        """Return latitude."""
        coordinates = vehicle_value(
            self.coordinator.data, "last_position", "geometry", "coordinates"
        )
        if not isinstance(coordinates, list) or len(coordinates) < 2:
            return None
        return float(coordinates[1])

    @property
    def longitude(self) -> float | None:
        """Return longitude."""
        coordinates = vehicle_value(
            self.coordinator.data, "last_position", "geometry", "coordinates"
        )
        if not isinstance(coordinates, list) or len(coordinates) < 2:
            return None
        return float(coordinates[0])

    @property
    def location_accuracy(self) -> int:
        """Return an approximate accuracy in meters."""
        return 10

    @property
    def battery_level(self) -> int | None:
        """Return main traction battery level when electric data is present."""
        level = vehicle_value(self.coordinator.data, "energy", 0, "level")
        if level is None:
            return None
        try:
            return int(float(level))
        except (TypeError, ValueError):
            return None

    @property
    def source_type(self) -> SourceType:
        """Return the source type."""
        return SourceType.GPS

    @property
    def entity_picture(self) -> str | None:
        """Return picture URL if cached under www/."""
        vin = self.coordinator.client.vin
        path = local_vehicle_image_path(self.hass, vin)
        if os.path.isfile(path):
            return public_vehicle_image_url(vin)
        return None
