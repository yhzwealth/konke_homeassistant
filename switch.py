from homeassistant.helpers.entity import DeviceInfo
from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity


from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]

    entities = []
    for nodeid, info in coordinator.devices.items():
        if info["type"] == "switch":
            entities.append(KonkeSwitch(coordinator, nodeid))

    async_add_entities(entities)


class KonkeSwitch(CoordinatorEntity, SwitchEntity):
    def __init__(self, coordinator, nodeid):
        super().__init__(coordinator)
        self.nodeid = nodeid
        self._attr_name = f"Konke Switch {nodeid}"
        self._attr_unique_id = f"konke_switch_{nodeid}"

    @property
    def device_info(self):
        return DeviceInfo(
            identifiers={(DOMAIN, self.nodeid)},
            name=f"开关 {self.nodeid}",
            manufacturer="Konke",
            model="Switch",
            sw_version="1.0.0",
        )

    @property
    def is_on(self):
        return self.coordinator.devices[self.nodeid]["state"] == "ON"

    async def async_turn_on(self):
        await self.hass.async_add_executor_job(
            self.coordinator.client.switch,
            self.nodeid,
            "ON"
        )

        # ✅ 立刻更新本地状态（乐观）
        self.coordinator.devices[self.nodeid]["state"] = "ON"
        self.coordinator.async_set_updated_data(self.coordinator.devices)

    async def async_turn_off(self):
        await self.hass.async_add_executor_job(
            self.coordinator.client.switch,
            self.nodeid,
            "OFF"
        )

        # ✅ 立刻更新本地状态（乐观）
        self.coordinator.devices[self.nodeid]["state"] = "OFF"
        self.coordinator.async_set_updated_data(self.coordinator.devices)

