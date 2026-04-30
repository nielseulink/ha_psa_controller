"""Config flow for PSA Controller."""

from __future__ import annotations

from urllib.parse import urlparse

from aiohttp import ClientError
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from .const import (
    CONF_BRAND,
    CONF_HOST,
    CONF_MODEL,
    CONF_VEHICLE_IMAGE_URL,
    CONF_VIN,
    DOMAIN,
)
from .coordinator import PsaControllerApiClient
from .image import async_cache_vehicle_image, is_public_http_url

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_VIN): str,
        vol.Required(CONF_BRAND): str,
        vol.Required(CONF_MODEL): str,
        vol.Optional(CONF_VEHICLE_IMAGE_URL, default=""): str,
    }
)


def _normalize_host(host: str) -> str:
    """Normalize a user-entered host to a base URL."""
    normalized = host.strip().rstrip("/")
    if "://" not in normalized:
        normalized = f"http://{normalized}"

    parsed = urlparse(normalized)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise InvalidHost

    return f"{parsed.scheme}://{parsed.netloc}"


async def validate_input(hass: HomeAssistant, data: dict[str, str]) -> dict[str, str]:
    """Validate the user input allows us to connect."""
    host = _normalize_host(data[CONF_HOST])
    vin = data[CONF_VIN].strip().upper()
    brand = (data[CONF_BRAND] or "").strip()
    model = (data[CONF_MODEL] or "").strip()

    if not vin:
        raise InvalidVin
    if not brand:
        raise InvalidBrand
    if not model:
        raise InvalidModel

    image_url = (data.get(CONF_VEHICLE_IMAGE_URL) or "").strip()
    if image_url and not is_public_http_url(image_url):
        raise InvalidImageUrl

    client = PsaControllerApiClient(hass, host, vin)
    try:
        await client.async_get_vehicle_info()
        await client.async_get_charge_control()
    except (TimeoutError, ClientError, ValueError) as err:
        raise CannotConnect from err

    result: dict[str, str] = {
        CONF_HOST: host,
        CONF_VIN: vin,
        CONF_BRAND: brand,
        CONF_MODEL: model,
    }
    if image_url:
        result[CONF_VEHICLE_IMAGE_URL] = image_url

    return result


class PsaControllerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for PSA Controller."""

    VERSION = 2

    async def async_step_user(
        self, user_input: dict[str, str] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidHost:
                errors[CONF_HOST] = "invalid_host"
            except InvalidVin:
                errors[CONF_VIN] = "invalid_vin"
            except InvalidBrand:
                errors[CONF_BRAND] = "invalid_brand"
            except InvalidModel:
                errors[CONF_MODEL] = "invalid_model"
            except InvalidImageUrl:
                errors[CONF_VEHICLE_IMAGE_URL] = "invalid_image_url"
            else:
                await self.async_set_unique_id(info[CONF_VIN])
                self._abort_if_unique_id_configured()
                if info.get(CONF_VEHICLE_IMAGE_URL):
                    await async_cache_vehicle_image(
                        self.hass, info[CONF_VIN], info[CONF_VEHICLE_IMAGE_URL]
                    )
                return self.async_create_entry(
                    title=f"{info[CONF_BRAND]} {info[CONF_MODEL]} ({info[CONF_VIN]})",
                    data=info,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidHost(HomeAssistantError):
    """Error to indicate the host is invalid."""


class InvalidVin(HomeAssistantError):
    """Error to indicate the VIN is invalid."""


class InvalidBrand(HomeAssistantError):
    """Error to indicate the brand is invalid."""


class InvalidModel(HomeAssistantError):
    """Error to indicate the model is invalid."""


class InvalidImageUrl(HomeAssistantError):
    """Error to indicate the vehicle image URL is invalid."""
