"""Data update coordinator for Termoweb integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import CONF_EMAIL, DOMAIN, UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)


class TermowebDataUpdateCoordinator(DataUpdateCoordinator[dict[int, dict[str, Any]]]):
    """Class to manage fetching Termoweb data."""

    def __init__(
        self,
        hass: HomeAssistant,
        termoweb_client,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=UPDATE_INTERVAL,
            config_entry=config_entry,
        )
        self.termoweb_client = termoweb_client

    async def _async_update_data(self) -> dict[int, dict[str, Any]]:
        """Fetch data from the API."""
        from termoweb import APIError, AuthenticationError

        try:
            return await self.hass.async_add_executor_job(
                self.termoweb_client.get_devices
            )
        except AuthenticationError as err:
            raise ConfigEntryAuthFailed("Authentication failed") from err
        except APIError as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err

    async def async_set_heater(self, heater_id: int, mode: str, target_temp: float) -> None:
        """Set heater mode and target temperature."""
        from termoweb import APIError, AuthenticationError

        try:
            await self.hass.async_add_executor_job(
                self.termoweb_client.set_heater, heater_id, mode, target_temp
            )
        except AuthenticationError as err:
            raise ConfigEntryAuthFailed("Authentication failed") from err
        except APIError as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err