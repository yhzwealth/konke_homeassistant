import asyncio
import logging
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

MAX_NODEID = 200

class KonkeCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, client):
        super().__init__(
            hass,
            _LOGGER,
            name="Konke Coordinator",
            update_interval=None,  # push
        )
        self.client = client
        self.devices = {}   # nodeid -> device_info
        self.client.set_callback(self.handle_message)

    async def async_start(self):
        await self.hass.async_add_executor_job(self.client.connect)
        await self._async_connect_and_discover()

    async def _async_connect_and_discover(self):
        while True:
            try:
                await self.hass.async_add_executor_job(self.client.connect)
                await self._async_discover_devices()
                _LOGGER.info("Konke connected")
                break
            except Exception as e:
                _LOGGER.error("Konke connect failed: %s", e)
                await asyncio.sleep(10)

    async def _async_discover_devices(self):
        _LOGGER.info("Konke: start discovering devices")
        for nodeid in range(1, MAX_NODEID + 1):
            self.client.query(nodeid)
            await asyncio.sleep(0.05)  # 防止打爆网关

    def handle_message(self, msg):
        if msg.get("opcode") == "__DISCONNECT__":
            _LOGGER.warning("Konke disconnected, reconnecting...")
            self.hass.async_create_task(self._async_reconnect())
            return
        opcode = msg.get("opcode")
        nodeid = msg.get("nodeid")
        arg = msg.get("arg")

        if nodeid not in self.devices and opcode in ("SWITCH", "FAN_COIL_STATUS", "CHOPIN_FRESH_AIR_STATUS", "FLOOR_HEATING_DEV_STATUS"):
            _LOGGER.info("Device %s opcode=%s, arg=%s", nodeid, opcode, arg)
            device_type = self._infer_device_type(arg, opcode)
            self.devices[nodeid] = {
                "nodeid": nodeid,
                "type": device_type,
                "state": arg,
            }
            _LOGGER.info("Discovered device %s type=%s", nodeid, device_type)
            self.async_set_updated_data(self.devices)
            return

    async def _async_reconnect(self):
        await self.hass.async_add_executor_job(self.client.close)
        await asyncio.sleep(5)
        await self._async_connect_and_discover()

    def _infer_device_type(self, arg, opcode):
        if arg in ("ON", "OFF"):
            return "switch"
        if arg in ("OPEN", "CLOSE", "STOP"):
            return "cover"
        if opcode == "FAN_COIL_STATUS":
            return "climate"
        return "unknown"
