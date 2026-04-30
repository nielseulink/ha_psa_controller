"""Base entities for PSA Controller."""

from __future__ import annotations

from typing import Any

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import PsaControllerDataUpdateCoordinator


class PsaControllerEntity(CoordinatorEntity[PsaControllerDataUpdateCoordinator]):
    """Base class for PSA Controller entities."""

    _attr_has_entity_name = True

    def __init__(
        self, coordinator: PsaControllerDataUpdateCoordinator, key: str
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.client.vin}_{key}"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.client.vin)},
            manufacturer=self.coordinator.brand,
            model=self.coordinator.model,
            name=self.coordinator.device_name,
            configuration_url=self.coordinator.client.base_url,
        )


def value_at(data: dict[str, Any], *path: str | int) -> Any:
    """Return a nested value from dictionaries and lists."""
    value: Any = data
    for part in path:
        if isinstance(part, int):
            if not isinstance(value, list) or len(value) <= part:
                return None
            value = value[part]
            continue

        if not isinstance(value, dict):
            return None
        value = value.get(part)

    return value


def vehicle_value(data: dict[str, Any], *path: str | int) -> Any:
    """Return a nested value from the vehicle payload."""
    return value_at(data, "vehicle", *path)


def charge_control_value(data: dict[str, Any], *path: str | int) -> Any:
    """Return a nested value from the charge-control payload."""
    return value_at(data, "charge_control", *path)
