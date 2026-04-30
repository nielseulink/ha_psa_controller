"""PSA Controller integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import (
    CONF_BRAND,
    CONF_HOST,
    CONF_MODEL,
    CONF_VEHICLE_IMAGE_URL,
    CONF_VIN,
    DATA_COORDINATOR,
    DOMAIN,
)
from .config_flow import PsaControllerConfigFlow
from .coordinator import PsaControllerApiClient, PsaControllerDataUpdateCoordinator
from .image import async_ensure_vehicle_image_cached

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.DEVICE_TRACKER,
    Platform.NUMBER,
    Platform.SENSOR,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up PSA Controller from a config entry."""
    client = PsaControllerApiClient(
        hass,
        entry.data[CONF_HOST],
        entry.data[CONF_VIN],
    )
    coordinator = PsaControllerDataUpdateCoordinator(
        hass,
        client,
        brand=entry.data[CONF_BRAND],
        model=entry.data[CONF_MODEL],
    )
    await coordinator.async_config_entry_first_refresh()

    await async_ensure_vehicle_image_cached(
        hass,
        entry.data[CONF_VIN],
        entry.data.get(CONF_VEHICLE_IMAGE_URL),
    )

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        DATA_COORDINATOR: coordinator,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate old config entries."""
    if entry.version > PsaControllerConfigFlow.VERSION:
        return False

    if entry.version < PsaControllerConfigFlow.VERSION:
        data = dict(entry.data)
        data.setdefault(CONF_BRAND, "Stellantis")
        data.setdefault(CONF_MODEL, "Vehicle")
        hass.config_entries.async_update_entry(
            entry, data=data, version=PsaControllerConfigFlow.VERSION
        )

    return True
