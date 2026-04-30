"""Download and cache vehicle images under Home Assistant www/."""

from __future__ import annotations

import logging
import os
from io import BytesIO
from urllib.parse import urlparse

from aiohttp import ClientError

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import IMAGE_SUBDIR, VEHICLE_MAP_IMAGE_FILE_SUFFIX

_LOGGER = logging.getLogger(__name__)

# Match homeassistant-stellantis-vehicles: square tile for consistent map/picture display.
_VEHICLE_IMAGE_SIZE = (400, 400)


def _vehicle_png_basename(vin: str) -> str:
    return f"{vin}{VEHICLE_MAP_IMAGE_FILE_SUFFIX}.png"


def public_vehicle_image_url(vin: str) -> str:
    """Return the /local URL for a cached vehicle image."""
    return f"/local/{IMAGE_SUBDIR}/{_vehicle_png_basename(vin)}"


def local_vehicle_image_path(hass: HomeAssistant, vin: str) -> str:
    """Filesystem path to the cached PNG."""
    return hass.config.path("www", IMAGE_SUBDIR, _vehicle_png_basename(vin))


def is_public_http_url(url: str) -> bool:
    """Return True if url is a plausible http(s) URL."""
    parsed = urlparse(url.strip())
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _process_and_save_vehicle_png(data: bytes, dest_path: str) -> None:
    """Resize/pad to a square PNG (transparent margins), similar to Stellantis integration."""
    try:
        from PIL import Image, ImageOps, UnidentifiedImageError
    except ImportError:
        _LOGGER.warning(
            "Pillow is not installed; saving raw vehicle image bytes (install pillow)"
        )
        with open(dest_path, "wb") as handle:
            handle.write(data)
        return

    try:
        with Image.open(BytesIO(data)) as image:
            rgba = image.convert("RGBA")
            padded = ImageOps.pad(
                rgba,
                _VEHICLE_IMAGE_SIZE,
                method=Image.Resampling.LANCZOS,
                color=(0, 0, 0, 0),
                centering=(0.5, 0.5),
            )
            padded.save(dest_path, format="PNG", optimize=True)
    except (OSError, ValueError, UnidentifiedImageError) as err:
        raise RuntimeError(f"Could not decode or save vehicle image: {err}") from err


async def async_cache_vehicle_image(
    hass: HomeAssistant, vin: str, image_url: str
) -> str | None:
    """Download image_url, normalize, save under www/IMAGE_SUBDIR/. Return /local/... or None."""
    url = image_url.strip()
    if not url:
        return None

    if not is_public_http_url(url):
        _LOGGER.warning("Not caching vehicle image: invalid URL for VIN %s", vin)
        return None

    www_root = hass.config.path("www")
    dest_dir = hass.config.path("www", IMAGE_SUBDIR)
    if not os.path.isdir(www_root):
        _LOGGER.warning('Home Assistant "www" folder not found; vehicle image not cached')
        return None

    os.makedirs(dest_dir, exist_ok=True)
    dest_path = os.path.join(dest_dir, _vehicle_png_basename(vin))

    session = async_get_clientsession(hass)
    try:
        async with session.get(url, timeout=60) as response:
            response.raise_for_status()
            body = await response.read()
    except (TimeoutError, ClientError, OSError) as err:
        _LOGGER.warning("Failed to download vehicle image for %s: %s", vin, err)
        return None

    if not body:
        _LOGGER.warning("Empty response when downloading vehicle image for %s", vin)
        return None

    try:
        await hass.async_add_executor_job(_process_and_save_vehicle_png, body, dest_path)
    except OSError as err:
        _LOGGER.warning("Failed to save vehicle image for %s: %s", vin, err)
        return None
    except RuntimeError as err:
        _LOGGER.warning("Failed to process vehicle image for %s: %s", vin, err)
        return None

    _LOGGER.info("Cached vehicle image for %s under %s", vin, dest_path)
    return public_vehicle_image_url(vin)


async def async_ensure_vehicle_image_cached(
    hass: HomeAssistant, vin: str, image_url: str | None
) -> str | None:
    """If image_url is set, cache the file when missing; return public URL if file exists."""
    if not image_url or not str(image_url).strip():
        path = local_vehicle_image_path(hass, vin)
        if os.path.isfile(path):
            return public_vehicle_image_url(vin)
        return None

    path = local_vehicle_image_path(hass, vin)
    if os.path.isfile(path):
        return public_vehicle_image_url(vin)

    return await async_cache_vehicle_image(hass, vin, str(image_url))
