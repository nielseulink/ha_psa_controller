"""Constants for the PSA Controller integration."""

from __future__ import annotations

from datetime import timedelta

DOMAIN = "psa_controller"

CONF_HOST = "host"
CONF_VIN = "vin"
CONF_BRAND = "brand"
CONF_MODEL = "model"
CONF_VEHICLE_IMAGE_URL = "vehicle_image_url"

IMAGE_SUBDIR = "ha_psa_car_controller"

# Cached map/entity vehicle PNG basename is ``{vin}{VEHICLE_MAP_IMAGE_FILE_SUFFIX}.png``.
# Bump the suffix when the image pipeline changes so a new file is generated.
VEHICLE_MAP_IMAGE_FILE_SUFFIX = "_opt"

DEFAULT_SCAN_INTERVAL = timedelta(seconds=60)

DATA_COORDINATOR = "coordinator"
