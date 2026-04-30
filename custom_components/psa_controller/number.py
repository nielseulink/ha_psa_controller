"""Number entities for PSA Controller."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DATA_COORDINATOR, DOMAIN
from .coordinator import PsaControllerDataUpdateCoordinator
from .entity import PsaControllerEntity, charge_control_value


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up PSA Controller numbers."""
    coordinator: PsaControllerDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id][
        DATA_COORDINATOR
    ]
    async_add_entities([PsaChargeThresholdNumber(coordinator)])


class PsaChargeThresholdNumber(PsaControllerEntity, NumberEntity):
    """Number entity for the PSA charge threshold."""

    _attr_name = "Charge Threshold"
    _attr_icon = "mdi:battery-charging-80"
    _attr_native_min_value = 0
    _attr_native_max_value = 100
    _attr_native_step = 1
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_mode = NumberMode.SLIDER

    def __init__(self, coordinator: PsaControllerDataUpdateCoordinator) -> None:
        """Initialize the number entity."""
        super().__init__(coordinator, "charge_threshold_number")

    @property
    def native_value(self) -> float | None:
        """Return the current charging threshold."""
        value = charge_control_value(self.coordinator.data, "percentage_threshold")
        if value is None:
            return None
        return float(value)

    async def async_set_native_value(self, value: float) -> None:
        """Set the charging threshold."""
        await self.coordinator.client.async_set_charge_threshold(int(value))
        await self.coordinator.async_request_refresh()
