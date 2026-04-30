"""Coordinator and API client for PSA Controller."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from aiohttp import ClientError

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class PsaControllerApiClient:
    """Small API client for the local psa_car_controller service."""

    def __init__(self, hass: HomeAssistant, base_url: str, vin: str) -> None:
        """Initialize the API client."""
        self._session = async_get_clientsession(hass)
        self.base_url = base_url.rstrip("/")
        self.vin = vin

    async def async_get_json(
        self, path: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Fetch JSON from the PSA controller."""
        url = f"{self.base_url}/{path.lstrip('/')}"
        async with self._session.get(url, params=params) as response:
            response.raise_for_status()
            data = await response.json(content_type=None)
            if isinstance(data, dict):
                return data
            return {"value": data}

    async def async_get_vehicle_info(self) -> dict[str, Any]:
        """Fetch vehicle information."""
        return await self.async_get_json(f"get_vehicleinfo/{self.vin}")

    async def async_get_charge_control(self) -> dict[str, Any]:
        """Fetch charge-control information."""
        return await self.async_get_json("charge_control", {"vin": self.vin})

    async def async_wakeup(self) -> None:
        """Ask the vehicle to wake up."""
        await self.async_get_json(f"wakeup/{self.vin}")

    async def async_set_preconditioning(self, enabled: bool) -> None:
        """Turn preconditioning on or off."""
        await self.async_get_json(f"preconditioning/{self.vin}/{int(enabled)}")

    async def async_set_charge_threshold(self, percentage: int) -> None:
        """Set the charging threshold."""
        await self.async_get_json(
            "charge_control", {"vin": self.vin, "percentage": percentage}
        )


class PsaControllerDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinate updates from PSA Controller."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: PsaControllerApiClient,
        *,
        brand: str,
        model: str,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=DEFAULT_SCAN_INTERVAL,
        )
        self.client = client
        self.brand = brand
        self.model = model

    @property
    def device_name(self) -> str:
        """Human-friendly device name including VIN."""
        return f"{self.brand} {self.model} ({self.client.vin})"

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch the latest data from the PSA controller."""
        try:
            vehicle, charge_control = await asyncio.gather(
                self.client.async_get_vehicle_info(),
                self.client.async_get_charge_control(),
            )
        except (TimeoutError, ClientError, ValueError) as err:
            raise UpdateFailed(f"Error communicating with PSA Controller: {err}") from err

        return {
            "vehicle": vehicle,
            "charge_control": charge_control,
        }
