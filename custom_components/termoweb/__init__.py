"""The Termoweb integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import CONF_EMAIL, DOMAIN
from .coordinator import TermowebDataUpdateCoordinator

PLATFORMS: list[Platform] = [Platform.CLIMATE]

type TermowebConfigEntry = ConfigEntry[TermowebDataUpdateCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: TermowebConfigEntry) -> bool:
    """Set up Termoweb from a config entry."""
    from termoweb import APIError, AuthenticationError, Termoweb

    email = entry.data[CONF_EMAIL]
    password = entry.data[CONF_PASSWORD]

    termoweb_client = Termoweb(email, password)

    try:
        await hass.async_add_executor_job(termoweb_client.connect)
    except AuthenticationError as err:
        raise ConfigEntryNotReady(f"Authentication failed: {err}") from err
    except APIError as err:
        raise ConfigEntryNotReady(f"Unable to connect to Termoweb: {err}") from err

    coordinator = TermowebDataUpdateCoordinator(hass, termoweb_client, entry)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: TermowebConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
