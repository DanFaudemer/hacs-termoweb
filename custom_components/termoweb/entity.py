"""Base entity for Termoweb integration."""

from __future__ import annotations

from typing import Any

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import TermowebDataUpdateCoordinator


class TermowebEntity(CoordinatorEntity[TermowebDataUpdateCoordinator]):
    """Base entity for Termoweb integration."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: TermowebDataUpdateCoordinator,
        heater_id: int,
        heater_data: dict[str, Any],
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self._heater_id = heater_id
        self._attr_unique_id = f"{heater_id}"

        # Set device info
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, str(heater_id))},
            name=heater_data.get("name", f"Radiator {heater_id}"),
            manufacturer="Termoweb",
            model="Radiator",
        )

    @property
    def heater_data(self) -> dict[str, Any]:
        """Return the heater data from the coordinator."""
        return self.coordinator.data.get(self._heater_id, {})

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return super().available and self._heater_id in self.coordinator.data