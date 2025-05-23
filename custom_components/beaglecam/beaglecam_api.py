import aiohttp

class BeagleCamAPI:
    def __init__(self, ip, username, password, session):
        self._url = f"http://{ip}/set3DPiCmd"
        self._username = username
        self._password = password
        self._session = session

    async def validate_connection(self):
        """Initial validation using cmd 312."""
        payload = {
            "cmd": 312,
            "pro": "get_prconnectstate",
            "user": self._username,
            "pwd": self._password
        }
        async with self._session.post(self._url, json=payload) as response:
            response.raise_for_status()
            return await response.json()

    async def get_print_status(self):
        """Poll printer status using cmd 318."""
        payload = {
            "cmd": 318,
            "pro": "get_prgresp",
            "user": self._username,
            "pwd": self._password
        }
        async with self._session.post(self._url, json=payload) as response:
            response.raise_for_status()
            return await response.json()

    async def get_temperature_status(self):
        payload = {
            "cmd": 302,
            "pro": "get_tempinfo",
            "user": self._username,
            "pwd": self._password
        }

        async with self._session.post(self._url, json=payload) as response:
            response.raise_for_status()
            return await response.json()
