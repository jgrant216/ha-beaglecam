import aiohttp
import logging

_LOGGER = logging.getLogger(__name__)


class BeagleCamAPI:
    def __init__(self, ip, username, password, session):
        self._url = f"http://{ip}/set3DPiCmd"
        self._username = username
        self._password = password
        self._session = session

        # Add counters for logging throttling
        self._call_counts = {
            "connection_state": 0,
            "print_status": 0,
            "temperature_status": 0,
        }

    async def get_connection_state(self):
        """
        Performs an initial validation by sending command 312 to the device.

        API Example Return:
            dict: A dictionary with the device's status, typically in the format:
                {
                    "cmd": 312,
                    "result": 0,
                    "connect_state": 1,
                    "print_state": 102,
                    "heat_state": 0,
                    "fan_speed": 0,
                    "tlv_sd_state": 0,
                    "filament_open": 0
                }

            - result: 0 indicates success.
            - connect_state: 1 if connected.
            - print_state: 102 indicates idle
            - Other keys represent hardware status indicators.
        """
        payload = {
            "cmd": 312,
            "pro": "get_prconnectstate",
            "user": self._username,
            "pwd": self._password
        }
        async with self._session.post(self._url, json=payload) as response:
            response.raise_for_status()
            responseJson = await response.json()
            self._call_counts["connection_state"] += 1
            if self._call_counts["connection_state"] % 10 == 0:
                _LOGGER.debug("BeagleCamAPI.get_connection_state response: %s", responseJson)
            return responseJson

    async def get_print_status(self):
        """Poll printer status using cmd 318.
        
        API Example Return:
        {
            "cmd": 318,
            "result": 0,
            "file_name": "",
            "progress": 0,
            "time_left": 0,
            "time_cost": 0,
            "layerIndex": 0,
            "printingHeight": 0,
            "hadSize": 0
        }
        """
        payload = {
            "cmd": 318,
            "pro": "get_prgresp",
            "user": self._username,
            "pwd": self._password
        }
        async with self._session.post(self._url, json=payload) as response:
            response.raise_for_status()
            responseJson = await response.json()
            self._call_counts["print_status"] += 1
            if self._call_counts["print_status"] % 10 == 0:
                _LOGGER.debug("BeagleCamAPI.get_print_status response: %s", responseJson)
            return responseJson

    async def get_temperature_status(self):
        """

        API Example Return:
        {
            "cmd": 302,
            "result": 0,
            "tempture_noz": 14,
            "tempture_bed": 14,
            "des_tempture_noz": 0,
            "des_tempture_bed": 0
        }
        """
        payload = {
            "cmd": 302,
            "pro": "get_tempinfo",
            "user": self._username,
            "pwd": self._password
        }

        async with self._session.post(self._url, json=payload) as response:
            response.raise_for_status()
            responseJson = await response.json()
            self._call_counts["temperature_status"] += 1
            if self._call_counts["temperature_status"] % 10 == 0:
                _LOGGER.debug("BeagleCamAPI.get_temperature_status response: %s", responseJson)
            return responseJson
