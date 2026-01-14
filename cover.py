from homeassistant.helpers.entity import DeviceInfo
from homeassistant.components.cover import (
    CoverEntity,
    CoverEntityFeature,
)
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]

    entities = []
    for nodeid, info in coordinator.devices.items():
        if info["type"] == "cover":
            entities.append(KonkeCover(coordinator, nodeid))

    async_add_entities(entities)


class KonkeCover(CoordinatorEntity, CoverEntity):
    def __init__(self, coordinator, nodeid):
        super().__init__(coordinator)
        self.nodeid = nodeid

        self._attr_name = f"Konke cover {nodeid}"
        self._attr_unique_id = f"konke_cover_{nodeid}"

        self._attr_supported_features = (
            CoverEntityFeature.OPEN
            | CoverEntityFeature.CLOSE
            | CoverEntityFeature.STOP
        )

    @property
    def device_info(self):
        return DeviceInfo(
            identifiers={(DOMAIN, self.nodeid)},
            name=f"窗帘 {self.nodeid}",
            manufacturer="Konke",
            model="Switch",
            sw_version="1.0.0",
        )

    @property
    def is_closed(self):
        return self.coordinator.devices[self.nodeid]["state"] == "CLOSE"

    async def async_open_cover(self, **kwargs):
        await self.hass.async_add_executor_job(
            self.coordinator.client.switch,
            self.nodeid,
            "OPEN",
        )

        self.coordinator.devices[self.nodeid]["state"] = "OPEN"
        self.coordinator.async_set_updated_data(self.coordinator.devices)


    async def async_close_cover(self, **kwargs):
        await self.hass.async_add_executor_job(
            self.coordinator.client.switch,
            self.nodeid,
            "CLOSE",
        )

        self.coordinator.devices[self.nodeid]["state"] = "CLOSE"
        self.coordinator.async_set_updated_data(self.coordinator.devices)


    async def async_stop_cover(self, **kwargs):
        await self.hass.async_add_executor_job(
            self.coordinator.client.switch,
            self.nodeid,
            "STOP",
        )

        self.coordinator.devices[self.nodeid]["state"] = "STOP"
        self.coordinator.async_set_updated_data(self.coordinator.devices)
