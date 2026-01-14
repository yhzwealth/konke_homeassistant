from homeassistant.helpers.entity import DeviceInfo
from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import (
    HVACMode, FAN_AUTO, FAN_LOW, FAN_MEDIUM, FAN_HIGH, ClimateEntityFeature
)
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.const import UnitOfTemperature


from .const import DOMAIN

RUN_MODEL_MAP = {
    "COLD": HVACMode.COOL,
    "HOT": HVACMode.HEAT,
    "WIND": HVACMode.FAN_ONLY,
    "DEHUMIDIFICATION": HVACMode.DRY,
}

RUN_MODEL_INT_MAP = {
    HVACMode.COOL: "COLD",
    HVACMode.HEAT: "HOT",
    HVACMode.FAN_ONLY: "WIND",
    HVACMode.DRY: "DEHUMIDIFICATION",
}

FAN_SPEED_MAP = {
    "LOW": FAN_LOW,
    "MID": FAN_MEDIUM,
    "HIGH": FAN_HIGH,
    "AUTO": FAN_AUTO,
}

FAN_SPEED_INT_MAP = {
    FAN_LOW: "LOW",
    FAN_MEDIUM: "MID",
    FAN_HIGH: "HIGH",
    FAN_AUTO: "AUTO",
}

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]

    entities = []
    for nodeid, dev in coordinator.devices.items():
        if dev["type"] == "climate":
            entities.append(KonkeClimate(coordinator, nodeid))

    async_add_entities(entities)


class KonkeClimate(CoordinatorEntity, ClimateEntity):
    def __init__(self, coordinator, nodeid):
        super().__init__(coordinator)
        self.nodeid = nodeid
        self._attr_name = f"Konke AC {nodeid}"
        self._attr_unique_id = f"konke_climate_{nodeid}"
        self._attr_temperature_unit = UnitOfTemperature.CELSIUS
        self._attr_supported_features = (
            ClimateEntityFeature.TARGET_TEMPERATURE |  # 支持设温
            ClimateEntityFeature.TURN_OFF |            # 支持关机
            ClimateEntityFeature.TURN_ON |             # 支持开机
            ClimateEntityFeature.FAN_MODE              # (可选) 支持风速
        )

    @property
    def device_info(self):
        return DeviceInfo(
            identifiers={(DOMAIN, self.nodeid)},
            name=f"空调 {self.nodeid}",
            manufacturer="Konke",
            model="Fan Coil",
            sw_version="1.0.0",
        )


    @property
    def hvac_mode(self):
        state = self.coordinator.devices[self.nodeid]["state"]
        if not state["on"]:
            return HVACMode.OFF
        return RUN_MODEL_MAP.get(state["run_model"], HVACMode.AUTO)

    @property
    def hvac_modes(self):
        return [
            HVACMode.OFF,
            HVACMode.COOL,
            HVACMode.HEAT,
            HVACMode.FAN_ONLY,
            HVACMode.DRY,
        ]

    async def async_set_hvac_mode(self, hvac_mode):
        if hvac_mode == HVACMode.OFF:
            await self.hass.async_add_executor_job(
                self.coordinator.client.switch,
                self.nodeid,
                "OFF"
            )
            self.coordinator.devices[self.nodeid]["state"]['on'] = False
        else:
            if self.hvac_mode == HVACMode.OFF:
                await self.hass.async_add_executor_job(
                    self.coordinator.client.switch,
                    self.nodeid,
                    "ON"
                )
                self.coordinator.devices[self.nodeid]["state"]['on'] = True
            await self.hass.async_add_executor_job(
                self.coordinator.client.send_fan_coil_run_model,
                self.nodeid,
                RUN_MODEL_INT_MAP[hvac_mode]
            )
            self.coordinator.devices[self.nodeid]["state"]['run_model'] = RUN_MODEL_INT_MAP[hvac_mode]
        self.coordinator.async_set_updated_data(self.coordinator.devices)

    @property
    def target_temperature(self):
        return self.coordinator.devices[self.nodeid]["state"]["setting_temperature"]

    @property
    def current_temperature(self):
        t = self.coordinator.devices[self.nodeid]["state"]["room_temperature"]
        return None if t == 65535 else t

    async def async_set_temperature(self, temperature):
        if temperature is None:
            return
        await self.hass.async_add_executor_job(
            self.coordinator.client.send_fan_coil_temperature,
            self.nodeid,
            temperature
        )
        self.coordinator.devices[self.nodeid]["state"]['setting_temperature'] = temperature
        self.coordinator.async_set_updated_data(self.coordinator.devices)

    @property
    def fan_mode(self):
        state = self.coordinator.devices[self.nodeid]["state"]
        return FAN_SPEED_MAP.get(state["fan_speed"], FAN_AUTO)

    @property
    def fan_modes(self):
        return FAN_SPEED_INT_MAP.keys()

    async def async_set_fan_mode(self, fan_mode):
        await self.hass.async_add_executor_job(
            self.coordinator.client.send_fan_coil_fan_speed,
            self.nodeid,
            FAN_SPEED_INT_MAP[fan_mode]
        )
        self.coordinator.devices[self.nodeid]["state"]['fan_speed'] = FAN_SPEED_INT_MAP[fan_mode]
        self.coordinator.async_set_updated_data(self.coordinator.devices)

