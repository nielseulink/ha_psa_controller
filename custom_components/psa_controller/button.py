"""Buttons for PSA Controller."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DATA_COORDINATOR, DOMAIN
from .coordinator import PsaControllerDataUpdateCoordinator
from .entity import PsaControllerEntity


@dataclass(frozen=True, kw_only=True)
class PsaButtonEntityDescription(ButtonEntityDescription):
    """Describe a PSA Controller button."""

    press_fn: Callable[[PsaControllerDataUpdateCoordinator], Awaitable[None]]


BUTTONS: tuple[PsaButtonEntityDescription, ...] = (
    PsaButtonEntityDescription(
        key="wakeup",
        name="Wake Up",
        press_fn=lambda coordinator: coordinator.client.async_wakeup(),
    ),
    PsaButtonEntityDescription(
        key="climate_on",
        name="Climate On",
        icon="mdi:air-conditioner",
        press_fn=lambda coordinator: coordinator.client.async_set_preconditioning(True),
    ),
    PsaButtonEntityDescription(
        key="climate_off",
        name="Climate Off",
        icon="mdi:air-conditioner-off",
        press_fn=lambda coordinator: coordinator.client.async_set_preconditioning(False),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up PSA Controller buttons."""
    coordinator: PsaControllerDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id][
        DATA_COORDINATOR
    ]
    async_add_entities(PsaButton(coordinator, description) for description in BUTTONS)


class PsaButton(PsaControllerEntity, ButtonEntity):
    """Representation of a PSA Controller button."""

    entity_description: PsaButtonEntityDescription

    def __init__(
        self,
        coordinator: PsaControllerDataUpdateCoordinator,
        description: PsaButtonEntityDescription,
    ) -> None:
        """Initialize the button."""
        super().__init__(coordinator, description.key)
        self.entity_description = description

    async def async_press(self) -> None:
        """Handle the button press."""
        await self.entity_description.press_fn(self.coordinator)
        await self.coordinator.async_request_refresh()
