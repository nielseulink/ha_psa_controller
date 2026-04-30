# ha_psa_car_controller

Custom Home Assistant integration (**PSA Car controller**) for a local [psa_car_controller](https://github.com/flobz/psa_car_controller/tree/master) instance.

This replaces a YAML package with a HACS-installable integration. During setup, Home Assistant asks for:

- PSA Controller URL, for example **`http://192.168.0.100:5000`**
- Vehicle **VIN** (see PSA Controller logs or config such as `cars.json`, or your manufacturer app / registration documents)
- **Brand** and **model** (used for the device name, including the VIN)
- Optional vehicle image URL; the image is downloaded, **normalized to a 400×400 PNG** (centered, transparent padding) and saved as `www/ha_psa_car_controller/<VIN>_opt.png` for the device tracker picture

**Integration icon:** `custom_components/psa_controller/brand/icon.png` is the [psacc-ha](https://github.com/flobz/psacc-ha/blob/main/psacc-ha/logo.png) logo.

To refresh the vehicle picture after changing the image pipeline or URL, delete `www/ha_psa_car_controller/<VIN>_opt.png` and restart Home Assistant or reload the integration. You can also replace the image with your own at this location.

## Installation with HACS

1. Add this repository to HACS as a custom repository (name: **ha_psa_car_controller**).
2. Select category **Integration**.
3. Install **PSA Car controller**.
4. Restart Home Assistant.
5. Go to **Settings > Devices & services > Add integration**.
6. Search for **PSA Car controller**.
7. Complete the configuration form (host, VIN, brand, model, optional image URL).

## Entities

The integration creates sensors for battery level, mileage, range, charging status, preconditioning status, charge threshold, fuel information, outside temperature, 12V battery status and ignition status.

It also creates binary sensors for plugged-in state, vehicle movement and engine running state.

A **device tracker** exposes GPS position from PSA data and uses the cached vehicle image as `entity_picture` when configured.

The integration includes buttons for wake-up, **climate on and climate off**, plus a number entity to change the charge threshold.

## Requirements

- Home Assistant **2026.3** or newer.
- **Pillow** (installed automatically as an integration dependency).
- The `psa_car_controller` service must already be running and reachable from Home Assistant.
