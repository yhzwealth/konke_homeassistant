from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .client import KonkeClient
from .coordinator import KonkeCoordinator

PLATFORMS = ["switch", "cover", "climate"]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    client = KonkeClient(
        host=entry.data["host"],
        port=entry.data["port"],
        username=entry.data["username"],
        password=entry.data["password"],
        zkid=entry.data["zkid"],
        hass=hass,
    )

    coordinator = KonkeCoordinator(hass, client)
    await coordinator.async_start()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True
