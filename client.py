import socket
import json
import threading
import time
import logging

_LOGGER = logging.getLogger(__name__)

class KonkeClient:
    def __init__(self, host, port, username, password, zkid, hass):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.zkid = zkid
        self.hass = hass

        self.sock = None
        self.callback = None
        self._running = False

    def set_callback(self, cb):
        self.callback = cb

    def connect(self):
        self._running = True
        self.sock = socket.create_connection((self.host, self.port), timeout=5)
        self._login()
        threading.Thread(target=self._recv_loop, daemon=True).start()
        threading.Thread(target=self._heartbeat_loop, daemon=True).start()

    def _login(self):
        self._send({
            "nodeid": "*",
            "opcode": "LOGIN",
            "requester": "HJ_Server",
            "arg": {
                "username": self.username,
                "password": self.password,
                "zkid": self.zkid,
                "seq": "",
                "device": "",
                "version": "",
            },
        })

    def query(self, nodeid):
        self._send({
            "nodeid": str(nodeid),
            "opcode": "QUERY",
            "arg": "*",
            "requester": "HJ_Server",
            "reqId": int(time.time()),
        })

    def switch(self, nodeid, value):
        self._send({
            "nodeid": str(nodeid),
            "opcode": "SWITCH",
            "arg": value,
            "requester": "HJ_Server",
            "reqId": int(time.time()),
        })

    def _send(self, msg):
        raw = "!" + json.dumps(msg) + "$"
        self.sock.sendall(raw.encode())

    def close(self):
        self._running = False
        if self.sock:
            self.sock.close()
            self.sock = None

    def _heartbeat_loop(self):
        while self._running:
            try:
                self._send({
                    "nodeid": "*",
                    "opcode": "CCU_HB",
                    "arg": "*",
                    "requester": "HJ_Server",
                })
            except Exception:
                if self.callback:
                    self.callback({"opcode": "__DISCONNECT__"})
                return
            time.sleep(30)

    def _recv_loop(self):
        buf = ""
        try:
            while self._running:
                data = self.sock.recv(1024).decode()
                if not data:
                    raise ConnectionError("socket closed")
                buf += data
                while "$" in buf:
                    frame, buf = buf.split("$", 1)
                    if frame.startswith("!"):
                        msg = json.loads(frame[1:])
                        if self.callback:
                            self.callback(msg)
        except Exception:
            if self.callback:
                self.callback({"opcode": "__DISCONNECT__"})

    def send_fan_coil_run_model(self, nodeid: str, run_model: int):
        self._send({
            "nodeid": str(nodeid),
            "opcode": "FAN_COIL_SET_RUN_MODEL",
            "arg": run_model,
            "requester": "HJ_Server",
            "reqId": int(time.time()),
        })

    def send_fan_coil_temperature(self, nodeid: str, temperature: int):
        self._send({
            "nodeid": str(nodeid),
            "opcode": "FAN_COIL_SET_TEMPERATURE",
            "arg": temperature,
            "requester": "HJ_Server",
            "reqId": int(time.time()),
        })

    def send_fan_coil_fan_speed(self, nodeid: str, fan_speed: int):
        self._send({
            "nodeid": str(nodeid),
            "opcode": "FAN_COIL_SET_FUN_SPEED",
            "arg": fan_speed,
            "requester": "HJ_Server",
            "reqId": int(time.time()),
        })
