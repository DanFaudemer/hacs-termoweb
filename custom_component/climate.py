"""Climate platform for Termoweb integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import TermowebConfigEntry
from .coordinator import TermowebDataUpdateCoordinator
from .entity import TermowebEntity

_LOGGER = logging.getLogger(__name__)

# Mapping between Termoweb modes and Home Assistant HVAC modes
TERMOWEB_TO_HVAC_MODE = {
    "off": HVACMode.OFF,
    "manual": HVACMode.HEAT,
}

HVAC_MODE_TO_TERMOWEB = {v: k for k, v in TERMOWEB_TO_HVAC_MODE.items()}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: TermowebConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the climate platform."""
    coordinator: TermowebDataUpdateCoordinator = config_entry.runtime_data

    entities = []
    for heater_id, heater_data in coordinator.data.items():
        entities.append(TermowebClimate(coordinator, heater_id, heater_data))

    async_add_entities(entities)


class TermowebClimate(TermowebEntity, ClimateEntity):
    """Representation of a Termoweb radiator."""

    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.TURN_ON | ClimateEntityFeature.TURN_OFF
    )
    _attr_hvac_modes = list(HVAC_MODE_TO_TERMOWEB.keys())
    _attr_name = None

    def __init__(
        self,
        coordinator: TermowebDataUpdateCoordinator,
        heater_id: int,
        heater_data: dict[str, Any],
    ) -> None:
        """Initialize the climate entity."""
        super().__init__(coordinator, heater_id, heater_data)

    @property
    def current_temperature(self) -> float | None:
        """Return the current temperature."""
        room_temp = self.heater_data.get("room_temp")
        if room_temp is not None:
            try:
                return float(room_temp)
            except (ValueError, TypeError):
                return None
        return None

    @property
    def target_temperature(self) -> float | None:
        """Return the target temperature."""
        target_temp = self.heater_data.get("target_temp")
        if target_temp is not None:
            try:
                return float(target_temp)
            except (ValueError, TypeError):
                return None
        return None

    @property
    def hvac_mode(self) -> HVACMode | None:
        """Return the current HVAC mode."""
        mode = self.heater_data.get("mode")
        if mode is not None:
            return TERMOWEB_TO_HVAC_MODE.get(mode, HVACMode.OFF)
        return HVACMode.OFF

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            raise ServiceValidationError("Temperature is required")

        current_mode = self.heater_data.get("mode", "heat")
        termoweb_mode = current_mode if current_mode in TERMOWEB_TO_HVAC_MODE else "heat"

        try:
            await self.coordinator.async_set_heater(
                self._heater_id, termoweb_mode, temperature
            )
        except Exception as err:
            raise ServiceValidationError(f"Failed to set temperature: {err}") from err

        await self.coordinator.async_request_refresh()

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new target HVAC mode."""
        if hvac_mode not in HVAC_MODE_TO_TERMOWEB:
            raise ServiceValidationError(f"Unsupported HVAC mode: {hvac_mode}")

        termoweb_mode = HVAC_MODE_TO_TERMOWEB[hvac_mode]
        target_temp = self.target_temperature or 20.0  # Default to 20°C if no target set

        try:
            await self.coordinator.async_set_heater(
                self._heater_id, termoweb_mode, target_temp
            )
        except Exception as err:
            raise ServiceValidationError(f"Failed to set HVAC mode: {err}") from err

        await self.coordinator.async_request_refresh()

    async def async_turn_on(self) -> None:
        """Turn the heater on."""
        await self.async_set_hvac_mode(HVACMode.HEAT)

    async def async_turn_off(self) -> None:
        """Turn the heater off."""
        await self.async_set_hvac_mode(HVACMode.OFF)