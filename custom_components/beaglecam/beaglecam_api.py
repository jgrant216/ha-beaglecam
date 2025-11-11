from collections import defaultdict

import aiohttp
import logging

_LOGGER = logging.getLogger(__name__)

PRINT_STATE_PRINTING = 101
PRINT_STATE_IDLE = 102
PRINT_STATE_PAUSED = 103

PRINT_STATE = {
    PRINT_STATE_PRINTING: "printing",
    PRINT_STATE_IDLE: "idle",
    PRINT_STATE_PAUSED: "paused",
}

class BeagleCamAPI:
    def __init__(self, ip: str, username: str, password: str, session: aiohttp.ClientSession):
        self._url = f"http://{ip}/set3DPiCmd"
        self._username = username
        self._password = password
        self._session = session

        # Add counters for logging throttling
        self._call_counts = defaultdict(int, **{
            "connection_state": 0,
            "print_status": 0,
            "temperature_status": 0,
        })

    async def _do_post(self, payload: dict, debug_key: str):
        async with self._session.post(self._url, json=payload) as response:
            response.raise_for_status()
            response_json = await response.json()
            self._call_counts[debug_key] += 1
            if self._call_counts[debug_key] % 10 == 0:
                _LOGGER.debug("BeagleCamAPI.%s response: %s", debug_key, response_json)
            return response_json

    async def check_user(self):
        """
        Example API Return:
        {
            "cmd":100,
            "result":0,
            "admin":1,
            "modle":0,  # possibly a typo for "model"
            "type":0
        }

        Example Invalid Login Return:
        {
            "cmd":100,
            "result":-3,
            "admin":1,
            "modle":0,
            "type":0
        }
        """
        payload = {
            "cmd": 100,
            "pro": "check_user",
            "user": self._username,
            "pwd": self._password
        }
        return await self._do_post(payload, "check_user")

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
            - print_state: 102 indicates idle, 101 indicates printing, 103 indicates paused.
            - Other keys represent hardware status indicators.
        """
        payload = {
            "cmd": 312,
            "pro": "get_prconnectstate",
            "user": self._username,
            "pwd": self._password
        }
        return await self._do_post(payload, "connection_state")

    async def get_print_status(self):
        """Poll print job status using cmd 318.
        
        API Example Return (Idle):
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

        API Example Return (Printing):
        {
            "cmd":318,
            "result":0,
            "file_name":"Revised Kobo Clara Switch 2_0.05mm_PLA_MK3S_9m.gcode",
            "progress":10,
            "time_left":484,
            "time_cost":52,
            "layerIndex":3,
            "printingHeight":0.300000,
            "hadSize":40414
        }
        """
        payload = {
            "cmd": 318,
            "pro": "get_prgresp",
            "user": self._username,
            "pwd": self._password
        }
        return await self._do_post(payload, "print_status")

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
        return await self._do_post(payload, "temperature_status")

    async def get_info(self):
        """
        API Example Return:
        {
            "cmd":101,
            "result":0,
            "p2pid":"....-######-.....",
            "hardware":"Beagle V2",
            "firmware":"1.2.9",
            "mirror_mode":3,
            "video_mode":0,
            "online_num":0,
            "network_type":"Wifi",
            "macaddress":"2C:C3:E6:..:..:..",
            "IPaddress":"192.168.###.###",
            "netmask":"255.255.255.0",
            "gateway":"192.168.###.1",
            "dns1":"192.168.###.###",
            "dns2":"192.168.###.###",
            "dhcp":1,
            "day_night_mode":0,
            "alarm_voice":"default"
            }
        """
        payload = {
            "cmd": 101,
            "pro": "info_get",
            "user": self._username,
            "pwd": self._password
        }
        return await self._do_post(payload, payload["pro"])

    async def get_baudrate(self):
        """
        Example API Return:
        {
            "cmd":251,
            "result":0,
            "baudrate":"115200:8:0:1",
            "ttyUSBList":[{"ttyName":"/dev/ttyACM0"}]
        }
        """
        payload = {
            "cmd": 251,
            "pro": "get_baudrate",
            "user": self._username,
            "pwd": self._password
        }
        return await self._do_post(payload, payload["pro"])

    async def get_tlv_params(self):
        """
        Example API Return:
        `{
            "cmd":337,
            "result":0,
            "enable":2,
            "maxx":250,
            "maxy":210,
            "maxz":210,
            "video_type":"H264",
            "fps":15,
            "min_inr_secs":5,
            "duration_tlv":0,
            "uv_layers":0,
            "prex":2,
            "prey":208,
            "prez":4,
            "xymove_speed":170,
            "zmove_speed":12,
            "move_delay_ms":500,
            "retract_length":5,
            "retract_speed":25,
            "extrude_length":5,
            "extrude_speed":25,
            "extra_filling":0.100000,
            "filling_speed":25
        }`
        """
        payload = {
            "cmd": 337,
            "pro": "get_tlv_params",
            "user": self._username,
            "pwd": self._password
        }
        return await self._do_post(payload, payload["pro"])

    async def get_model(self):
        """
        Example API Return:
        {
          "cmd": 253,
          "version": "2.1",
          "result": 0,
          "machineType": ["Marlin", "Klipper"],
          "machineTypeSelected": "Marlin",
          "KlipperObj": {
            "PrinterSelected": "",
            "ModelsList": [
              {
                "protocol": "moonraker",
                "webClient": [
                  "mainsail",
                  "fluidd"
                ],
                "url": "ws://ip:80/websocket",
                "accessToken": "",
                "apiKey": ""
              }
            ]
          },
          "selected": {  // One selection from the BrandModelList below, collapsed into a single level.
            "brand": "Prusa",
            "model": "i3 MK3S+",
            "size": "250x210x210mm",
            "category": "CoreXY",
            "usbpower": "true"
          },
          "BrandModelList": [
            {
              "name": "ANYCUBIC",
              "data": [
                {
                  "typename": "Mega S",
                  "size": "210x210x205mm",
                  "category": "CoreXY",
                  "usbpower": "false"
                },
                {
                  "typename": "Mega Pro",
                  "size": "210x210x205mm",
                  "category": "CoreXY",
                  "usbpower": "false"
                },
                {
                  "typename": "Mega SE",
                  "size": "220x220x250mm",
                  "category": "CoreXY",
                  "usbpower": "false"
                },
                {
                  "typename": "Mega Zero 2.0",
                  "size": "220x220x250mm",
                  "category": "CoreXY",
                  "usbpower": "false"
                },
                {
                  "typename": "Mega X",
                  "size": "300x300x305mm",
                  "category": "CoreXY",
                  "usbpower": "false"
                },
                {
                  "typename": "Vyper",
                  "size": "245x245x260mm",
                  "category": "CoreXY",
                  "usbpower": "false"
                },
                {
                  "typename": "Kobra",
                  "size": "220x220x250mm",
                  "category": "CoreXY",
                  "usbpower": "false"
                },
                {
                  "typename": "Kobra2",
                  "size": "220x220x250mm",
                  "category": "CoreXY",
                  "usbpower": "false"
                },
                {
                  "typename": "Kobra 2 Neo",
                  "size": "220x220x250mm",
                  "category": "CoreXY",
                  "usbpower": "false"
                },
                {
                  "typename": "Kobra Go",
                  "size": "220x220x250mm",
                  "category": "CoreXY",
                  "usbpower": "false"
                },
                {
                  "typename": "Kobra Neo",
                  "size": "220x220x250mm",
                  "category": "CoreXY",
                  "usbpower": "false"
                },
                {
                  "typename": "Kobra Plus",
                  "size": "300x300x350mm",
                  "category": "CoreXY",
                  "usbpower": "false"
                },
                {
                  "typename": "Kobra Max",
                  "size": "400x400x450mm",
                  "category": "CoreXY",
                  "usbpower": "false"
                },
                {
                  "typename": "Chiron",
                  "size": "400x400x450mm",
                  "category": "CoreXY",
                  "usbpower": "false"
                }
              ]
            },
            {
              "name": "Anet",
              "data": [
                {
                  "typename": "ET5X",
                  "size": "300x300x400mm",
                  "category": "CoreXY",
                  "usbpower": "true"
                },
                {
                  "typename": "A8",
                  "size": "220x220x240mm",
                  "category": "CoreXY",
                  "usbpower": "true"
                }
              ]
            },
            {
              "name": "Artillery",
              "data": [
                {
                  "typename": "SW X1",
                  "size": "300x300x400mm",
                  "category": "CoreXY",
                  "usbpower": "false"
                },
                {
                  "typename": "SW X2",
                  "size": "300x300x400mm",
                  "category": "CoreXY",
                  "usbpower": "false"
                },
                {
                  "typename": "Genius",
                  "size": "220x220x250mm",
                  "category": "CoreXY",
                  "usbpower": "false"
                },
                {
                  "typename": "Genius Pro",
                  "size": "220x220x250mm",
                  "category": "CoreXY",
                  "usbpower": "false"
                },
                {
                  "typename": "Hornet",
                  "size": "220x220x250mm",
                  "category": "CoreXY",
                  "usbpower": "false"
                }
              ]
            },
            {
              "name": "BIQU",
              "data": [
                {
                  "typename": "BX",
                  "size": "250x250x250mm",
                  "category": "CoreXY",
                  "usbpower": "false"
                }
              ]
            },
            {
              "name": "Creality",
              "data": [
                {
                  "typename": "Ender-2 Pro",
                  "size": "165x165x180mm",
                  "category": "CoreXY",
                  "usbpower": "false"
                },
                {
                  "typename": "Ender-3",
                  "size": "220x220x250mm",
                  "category": "CoreXY",
                  "usbpower": "false"
                },
                {
                  "typename": "Ender-3 Pro",
                  "size": "220x220x250mm",
                  "category": "CoreXY",
                  "usbpower": "false"
                },
                {
                  "typename": "Ender-3 V2",
                  "size": "220x220x250mm",
                  "category": "CoreXY",
                  "usbpower": "false"
                },
                {
                  "typename": "Ender-3 Neo",
                  "size": "220x220x250mm",
                  "category": "CoreXY",
                  "usbpower": "false"
                },
                {
                  "typename": "Ender-3 V2 Neo",
                  "size": "220x220x250mm",
                  "category": "CoreXY",
                  "usbpower": "false"
                },
                {
                  "typename": "Ender-3 S1",
                  "size": "220x220x270mm",
                  "category": "CoreXY",
                  "usbpower": "false"
                },
                {
                  "typename": "Ender-3 S1 Pro",
                  "size": "220x220x270mm",
                  "category": "CoreXY",
                  "usbpower": "false"
                },
                {
                  "typename": "Ender-3 S1 Plus",
                  "size": "300x300x300mm",
                  "category": "CoreXY",
                  "usbpower": "false"
                },
                {
                  "typename": "Ender-3 Max",
                  "size": "300x300x340mm",
                  "category": "CoreXY",
                  "usbpower": "false"
                },
                {
                  "typename": "Ender-3 Max Neo",
                  "size": "300x300x320mm",
                  "category": "CoreXY",
                  "usbpower": "false"
                },
                {
                  "typename": "Ender-3 V3 SE",
                  "size": "220x220x250mm",
                  "category": "CoreXY",
                  "usbpower": "false"
                },
                {
                  "typename": "Ender-5",
                  "size": "220x220x300mm",
                  "category": "CoreXY",
                  "usbpower": "false"
                },
                {
                  "typename": "Ender-5 Pro",
                  "size": "220x220x300mm",
                  "category": "CoreXY",
                  "usbpower": "false"
                },
                {
                  "typename": "Ender-5 Plus",
                  "size": "350x350x400mm",
                  "category": "CoreXY",
                  "usbpower": "false"
                },
                {
                  "typename": "Ender-7",
                  "size": "250x250x300mm",
                  "category": "CoreXY",
                  "usbpower": "false"
                },
                {
                  "typename": "CR-5 Pro",
                  "size": "300x225x380mm",
                  "category": "CoreXY",
                  "usbpower": "false"
                },
                {
                  "typename": "CR-6 SE",
                  "size": "235x235x250mm",
                  "category": "CoreXY",
                  "usbpower": "false"
                },
                {
                  "typename": "CR-10",
                  "size": "300x300x400mm",
                  "category": "CoreXY",
                  "usbpower": "false"
                },
                {
                  "typename": "CR-10 S",
                  "size": "300x300x400mm",
                  "category": "CoreXY",
                  "usbpower": "false"
                },
                {
                  "typename": "CR-10 V2",
                  "size": "300x300x400mm",
                  "category": "CoreXY",
                  "usbpower": "false"
                },
                {
                  "typename": "CR-10 V3",
                  "size": "300x300x400mm",
                  "category": "CoreXY",
                  "usbpower": "false"
                },
                {
                  "typename": "CR-10 Smart*",
                  "size": "300x300x400mm",
                  "category": "CoreXY",
                  "usbpower": "false"
                },
                {
                  "typename": "CR-10 Smart Pro*",
                  "size": "300x300x400mm",
                  "category": "CoreXY",
                  "usbpower": "false"
                },
                {
                  "typename": "CR-10 Max",
                  "size": "450x450x470mm",
                  "category": "CoreXY",
                  "usbpower": "false"
                },
                {
                  "typename": "CR10 S5",
                  "size": "500x500x500mm",
                  "category": "CoreXY",
                  "usbpower": "false"
                },
                {
                  "typename": "CR-20 Pro",
                  "size": "220x220x250mm",
                  "category": "CoreXY",
                  "usbpower": "false"
                },
                {
                  "typename": "CR 200B",
                  "size": "200x200x200mm",
                  "category": "CoreXY",
                  "usbpower": "false"
                }
              ]
            },
            {
              "name": "ELEGOO",
              "data": [
                {
                  "typename": "Neptune 2",
                  "size": "220x220x250mm",
                  "category": "CoreXY",
                  "usbpower": "false"
                },
                {
                  "typename": "Neptune 2D",
                  "size": "220x220x250mm",
                  "category": "CoreXY",
                  "usbpower": "false"
                },
                {
                  "typename": "Neptune 2S",
                  "size": "220x220x250mm",
                  "category": "CoreXY",
                  "usbpower": "false"
                },
                {
                  "typename": "Neptune 3",
                  "size": "220x220x280mm",
                  "category": "CoreXY",
                  "usbpower": "false"
                },
                {
                  "typename": "Neptune 3 Pro",
                  "size": "225x225x280mm",
                  "category": "CoreXY",
                  "usbpower": "false"
                },
                {
                  "typename": "Neptune 3 Plus",
                  "size": "320x320x400mm",
                  "category": "CoreXY",
                  "usbpower": "false"
                },
                {
                  "typename": "Neptune 3 Max",
                  "size": "420x420x500mm",
                  "category": "CoreXY",
                  "usbpower": "false"
                }
              ]
            },
            {
              "name": "Eryone",
              "data": [
                {
                  "typename": "ER-20",
                  "size": "250x220x200mm",
                  "category": "CoreXY",
                  "usbpower": "true"
                }
              ]
            },
            {
              "name": "Flsun",
              "data": [
                {
                  "typename": "Super Race",
                  "size": "260x260x330mm",
                  "category": "Delta",
                  "usbpower": "false"
                }
              ]
            },
            {
              "name": "Flying Bear",
              "data": [
                {
                  "typename": "Ghost 5",
                  "size": "255x210x200mm",
                  "category": "CoreXY",
                  "usbpower": "false"
                },
                {
                  "typename": "Ghost 6",
                  "size": "255x210x210mm",
                  "category": "CoreXY",
                  "usbpower": "false"
                },
                {
                  "typename": "Reborn 1",
                  "size": "350x310x340mm",
                  "category": "CoreXY",
                  "usbpower": "false"
                }
              ]
            },
            {
              "name": "Fokoos",
              "data": [
                {
                  "typename": "ODIN-5 F3",
                  "size": "235x235x250mm",
                  "category": "CoreXY",
                  "usbpower": "false"
                }
              ]
            },
            {
              "name": "Geeetech",
              "data": [
                {
                  "typename": "Mizar S",
                  "size": "255x255x260mm",
                  "category": "CoreXY",
                  "usbpower": "false"
                },
                {
                  "typename": "A20",
                  "size": "250x250x250mm",
                  "category": "CoreXY",
                  "usbpower": "false"
                },
                {
                  "typename": "A20M",
                  "size": "250x250x250mm",
                  "category": "CoreXY",
                  "usbpower": "false"
                },
                {
                  "typename": "i3 Pro",
                  "size": "200x200x180mm",
                  "category": "CoreXY",
                  "usbpower": "false"
                }
              ]
            },
            {
              "name": "Hellbot",
              "data": [
                {
                  "typename": "Magna 2 230",
                  "size": "230x230x250mm",
                  "category": "CoreXY",
                  "usbpower": "false"
                },
                {
                  "typename": "Magna 2 300",
                  "size": "300x300x400mm",
                  "category": "CoreXY",
                  "usbpower": "false"
                },
                {
                  "typename": "Magna 2 500",
                  "size": "500x500x500mm",
                  "category": "CoreXY",
                  "usbpower": "false"
                },
                {
                  "typename": "Magna SE",
                  "size": "230x230x250mm",
                  "category": "CoreXY",
                  "usbpower": "false"
                },
                {
                  "typename": "Magna SE PRO",
                  "size": "230x230x250mm",
                  "category": "CoreXY",
                  "usbpower": "false"
                },
                {
                  "typename": "Magna SE 300",
                  "size": "300x300x400mm",
                  "category": "CoreXY",
                  "usbpower": "false"
                },
                {
                  "typename": "Hidra*",
                  "size": "230x230x250mm",
                  "category": "CoreXY",
                  "usbpower": "false"
                },
                {
                  "typename": "Hidra Plus*",
                  "size": "300x300x350mm",
                  "category": "CoreXY",
                  "usbpower": "false"
                }
              ]
            },
            {
              "name": "iSUN3D",
              "data": [
                {
                  "typename": "iSUN_FLX3",
                  "size": "200x350x200mm",
                  "category": "CoreXY",
                  "usbpower": "false"
                }
              ]
            },
            {
              "name": "JGAURORA",
              "data": [
                {
                  "typename": "A5S",
                  "size": "305x305x320mm",
                  "category": "CoreXY",
                  "usbpower": "false"
                }
              ]
            },
            {
              "name": "Kingroon",
              "data": [
                {
                  "typename": "KP3S",
                  "size": "180x180x180mm",
                  "category": "CoreXY",
                  "usbpower": "false"
                },
                {
                  "typename": "KP3S Pro",
                  "size": "210x210x200mm",
                  "category": "CoreXY",
                  "usbpower": "false"
                },
                {
                  "typename": "KP3S Pro S1",
                  "size": "200x200x200mm",
                  "category": "CoreXY",
                  "usbpower": "false"
                }
              ]
            },
            {
              "name": "Kywoo",
              "data": [
                {
                  "typename": "Tycoon",
                  "size": "240x240x230mm",
                  "category": "CoreXY",
                  "usbpower": "false"
                },
                {
                  "typename": "Tycoon Slim",
                  "size": "240x240x300mm",
                  "category": "CoreXY",
                  "usbpower": "false"
                },
                {
                  "typename": "Tycoon Max",
                  "size": "300x300x230mm",
                  "category": "CoreXY",
                  "usbpower": "false"
                }
              ]
            },
            {
              "name": "Longer",
              "data": [
                {
                  "typename": "LK4 Pro",
                  "size": "220x220x250mm",
                  "category": "CoreXY",
                  "usbpower": "false"
                },
                {
                  "typename": "LK5 Pro",
                  "size": "300x300x400mm",
                  "category": "CoreXY",
                  "usbpower": "false"
                }
              ]
            },
            {
              "name": "Mingda",
              "data": [
                {
                  "typename": "Magician X",
                  "size": "230x230x260mm",
                  "category": "CoreXY",
                  "usbpower": "false"
                },
                {
                  "typename": "Magician Pro",
                  "size": "400x400x400mm",
                  "category": "CoreXY",
                  "usbpower": "false"
                },
                {
                  "typename": "Magician Max",
                  "size": "320x320x400mm",
                  "category": "CoreXY",
                  "usbpower": "false"
                }
              ]
            },
            {
              "name": "Monoprice",
              "data": [
                {
                  "typename": "Mini Delta",
                  "size": "110x110x120mm",
                  "category": "Delta",
                  "usbpower": "false"
                },
                {
                  "typename": "Mini Select V2",
                  "size": "120x120x120mm",
                  "category": "CoreXY",
                  "usbpower": "false"
                }
              ]
            },
            {
              "name": "Prusa",
              "data": [
                {
                  "typename": "i3 MK3S+",
                  "size": "250x210x210mm",
                  "category": "CoreXY",
                  "usbpower": "true"
                },
                {
                  "typename": "i3 MK3S+ & MMU2/MMU2S/MMU3",
                  "size": "250x210x210mm",
                  "category": "CoreXY",
                  "usbpower": "true"
                },
                {
                  "typename": "MK4",
                  "size": "250x210x220mm",
                  "category": "CoreXY",
                  "usbpower": "true"
                },
                {
                  "typename": "MK4 & MMU2/MMU2S/MMU3",
                  "size": "250x210x220mm",
                  "category": "CoreXY",
                  "usbpower": "true"
                },
                {
                  "typename": "MINI+",
                  "size": "180x180x180mm",
                  "category": "CoreXY",
                  "usbpower": "true"
                }
              ]
            },
            {
              "name": "Snapmaker",
              "data": [
                {
                  "typename": "A250T",
                  "size": "230x250x235mm",
                  "category": "CoreXY",
                  "usbpower": "false"
                },
                {
                  "typename": "A350T",
                  "size": "320x350x330mm",
                  "category": "CoreXY",
                  "usbpower": "false"
                }
              ]
            },
            {
              "name": "Sovol",
              "data": [
                {
                  "typename": "SV01",
                  "size": "280x240x300mm",
                  "category": "CoreXY",
                  "usbpower": "false"
                },
                {
                  "typename": "SV01 Pro",
                  "size": "280x240x300mm",
                  "category": "CoreXY",
                  "usbpower": "false"
                },
                {
                  "typename": "SV02",
                  "size": "280x240x300mm",
                  "category": "CoreXY",
                  "usbpower": "false"
                },
                {
                  "typename": "SV03",
                  "size": "350x350x400mm",
                  "category": "CoreXY",
                  "usbpower": "false"
                },
                {
                  "typename": "SV04",
                  "size": "300x300x400mm",
                  "category": "CoreXY",
                  "usbpower": "false"
                },
                {
                  "typename": "SV06",
                  "size": "220x220x250mm",
                  "category": "CoreXY",
                  "usbpower": "false"
                },
                {
                  "typename": "SV06 Plus",
                  "size": "300x300x340mm",
                  "category": "CoreXY",
                  "usbpower": "false"
                }
              ]
            },
            {
              "name": "Sunlu",
              "data": [
                {
                  "typename": "S8 Plus",
                  "size": "310x310x400mm",
                  "category": "CoreXY",
                  "usbpower": "false"
                },
                {
                  "typename": "Terminator 3",
                  "size": "220x220x250mm",
                  "category": "CoreXY",
                  "usbpower": "false"
                }
              ]
            },
            {
              "name": "Tenlog",
              "data": [
                {
                  "typename": "Hands 2",
                  "size": "220x220x250mm",
                  "category": "CoreXY",
                  "usbpower": "false"
                },
                {
                  "typename": "TL-D3 Pro",
                  "size": "300x300x350mm",
                  "category": "CoreXY",
                  "usbpower": "false"
                }
              ]
            },
            {
              "name": "Tevo",
              "data": [
                {
                  "typename": "HYDRA",
                  "size": "305x305x400mm",
                  "category": "CoreXY",
                  "usbpower": "false"
                }
              ]
            },
            {
              "name": "Two Trees",
              "data": [
                {
                  "typename": "BLU-3",
                  "size": "235x235x280mm",
                  "category": "CoreXY",
                  "usbpower": "false"
                },
                {
                  "typename": "BLU-5",
                  "size": "300x300x400mm",
                  "category": "CoreXY",
                  "usbpower": "false"
                },
                {
                  "typename": "SP-3",
                  "size": "220x220x220mm",
                  "category": "CoreXY",
                  "usbpower": "false"
                },
                {
                  "typename": "SP-5",
                  "size": "300x300x330mm",
                  "category": "CoreXY",
                  "usbpower": "false"
                }
              ]
            },
            {
              "name": "Tronxy",
              "data": [
                {
                  "typename": "X2",
                  "size": "220x220x220mm",
                  "category": "CoreXY",
                  "usbpower": "false"
                }
              ]
            },
            {
              "name": "Voxelab",
              "data": [
                {
                  "typename": "Aquila",
                  "size": "220x220x250mm",
                  "category": "CoreXY",
                  "usbpower": "false"
                },
                {
                  "typename": "Aquila C2",
                  "size": "220x220x250mm",
                  "category": "CoreXY",
                  "usbpower": "false"
                },
                {
                  "typename": "Aquila X2",
                  "size": "220x220x250mm",
                  "category": "CoreXY",
                  "usbpower": "false"
                },
                {
                  "typename": "Aquila S2",
                  "size": "220x220x240mm",
                  "category": "CoreXY",
                  "usbpower": "false"
                },
                {
                  "typename": "Aquila D1",
                  "size": "235x235x250mm",
                  "category": "CoreXY",
                  "usbpower": "false"
                }
              ]
            },
            {
              "name": "Wanhao",
              "data": [
                {
                  "typename": "SD12 230",
                  "size": "230x230x250mm",
                  "category": "CoreXY",
                  "usbpower": "false"
                }
              ]
            },
            {
              "name": "Wizmaker",
              "data": [
                {
                  "typename": "P1",
                  "size": "220x220x265mm",
                  "category": "CoreXY",
                  "usbpower": "false"
                }
              ]
            }
          ]
        }
        )
        """
        payload = {
            "cmd": 253,
            "pro": "get_model",
            "user": self._username,
            "pwd": self._password
        }
        return await self._do_post(payload, payload["pro"])

    async def get_osd(self):
        """
        Example API Return:
        {
            "cmd":171,
            "result":0,
            "timepos":4
        }
        """
        payload = {
            "cmd": 171,
            "pro": "osd_get",
            "user": self._username,
            "pwd": self._password
        }
        return await self._do_post(payload, payload["pro"])

    async def get_video_mode(self):
        """
        Example API Return:
        {
            "cmd":135,
            "result":0,
            "video_mode":0
        }
        """
        payload = {
            "cmd": 135,
            "pro": "video_mode_get",
            "user": self._username,
            "pwd": self._password
        }
        return await self._do_post(payload, payload["pro"])

    async def update_check(self):
        """
        Example API Return:
        {
            "cmd":219,
            "result":0,
            "curVersion":"1.2.9",
            "ota_info": {
                "ForceUpdateflag":"0",
                "HARDWARE":"BeagleV2_H1.0",
                "SWversion":"1.2.9",
                "VersionIntro":"<br>- Fixed the bug that Klipper printer connection failure on some accounts; <br>- Add more details on Klipper printer connection and status;",
                "FirmwareUrl":"https://beaglefirmware.oss-us-west-1.aliyuncs.com/BeagleV2/firmware_BeagleV2_kernel_system_1.2.9.bin"
            }
        }
        """
        payload = {
            "cmd": 219,
            "pro": "update_check",
            "user": self._username,
            "pwd": self._password
        }
        return await self._do_post(payload, payload["pro"])

    async def get_timelapse_videos(self):
        """
        Example API Return:
        {
            "cmd": 335,
            "result": 0,
            "count": 116, // total file count
            "filesList": [
                {
                    "name": "20230807_052949_h264.mp4",
                    "len": "12972K",
                    "time": "2023/08/07 11:12:48"
                },
                ...,
            ]
        }

        Video URLs are constructed as:
            `http://<beaglecam_ip>/mmc/tlv/<filename>`
        """
        payload = {
            "cmd": 335,
            "pro": "pri_file",
            "operate_cmd": 120,
            "user": self._username,
            "pwd": self._password
        }
        return await self._do_post(payload, payload["pro"])

    async def connect_printer(self):
        """
        Initiate connection to the printer. This method may take a long time if the printer is not available.

        Example API Return:
        {
            "cmd":310,
            "result":0
        }
        """
        payload = {
            "cmd": 310,
            "pro": "pr_connect",
            "user": self._username,
            "pwd": self._password
        }
        return await self._do_post(payload, payload["pro"])

    async def disconnect_printer(self):
        """
        Disconnect from the printer.

        Example API Return:
        {
            "cmd":311,
            "result":0
        }
        """
        payload = {
            "cmd": 311,
            "pro": "pr_disconnect",
            "user": self._username,
            "pwd": self._password
        }
        return await self._do_post(payload, payload["pro"])

    async def get_print_files(self):
        """
        Example API Return:
        {
            "cmd": 320,
            "result": 0,
            "count": 24,
            "filesList": [
                {
                    "name": "reprack_led_clip_v1_0.6n_0.2mm_PETG_MK3S_33m.gcode",
                    "len": "1453K",
                    "time": "2025/07/08 03:04:38"
                },
                ...,
            ],
        }

        Gcode file URLs are constructed as:
            `http://<beaglecam_ip>/mmc/<filename>`
        """
        payload = {
            "cmd": 320,
            "pro": "pri_file",
            "operate_cmd": 120,
            "user": self._username,
            "pwd": self._password
        }
        return await self._do_post(payload, payload["pro"])

    async def get_temperature_log(self):
        """
        Example API Return:
        {
            "cmd":330,
            "result":0,
            "count":3,
            "filesList": [
                {
                    "name":"20251109_132547.tlog",
                    "len":"25K",
                    "time":"2025/11/09 13:55:47"
                },
                {
                    "name":"20251109_135550.tlog",
                    "len":"1K",
                    "time":"2025/11/09 13:56:57"
                },
                {
                    "name":"20251110_100935.tlog",
                    "len":"11K",
                    "time":"2025/11/10 10:23:05"
                }
            ]
        }

        Temperature log file URLs are constructed as:
            `http://<beaglecam_ip>/mmc/tlog/<filename>`
        """
        payload = {
            "cmd": 330,
            "pro": "get_tlog",
            "user": self._username,
            "pwd": self._password
        }
        return await self._do_post(payload, payload["pro"])

    async def get_recording_params(self):
        """
        Example API Return:
        {
            "cmd":121,
            "result":0,
            "enable":0,
            "record_duration":600,
            "cover":1,
            "chno":0,
            "start_min":0,
            "stop_min":59,
            "start_hour":0,
            "stop_hour":23
        }
        """
        payload = {
            "cmd": 121,
            "pro": "get_rec_params",
            "user": self._username,
            "pwd": self._password
        }
        return await self._do_post(payload, payload["pro"])

    async def get_printer_settings(self):
        """
        Example API Return:
        {
            "cmd":340,
            "result":0,
            "feedrate":100,
            "flowrate":100,
            "zoffset":0
        }
        """
        payload = {
            "cmd": 340,
            "pro": "get_pr_setting",
            "user": self._username,
            "pwd": self._password
        }
        return await self._do_post(payload, payload["pro"])

    async def start_print(self, filename: str):
        """
        Start a print job with the specified Gcode file.

        Example API Return:
        {
            "cmd":313,
            "result":301
        }
        """
        payload = {
            "cmd": 313,
            "pro": "pr_start",
            "filename": filename,
            "user": self._username,
            "pwd": self._password
        }
        return await self._do_post(payload, payload["pro"])

    async def pause_print(self):
        """
        Pause the current print job.

        Example API Return:
        {
            "cmd":314,
            "result":0
        }
        """
        payload = {
            "cmd": 314,
            "pro": "pr_pause",
            "user": self._username,
            "pwd": self._password
        }
        return await self._do_post(payload, payload["pro"])

    async def stop_print(self):
        """
        Stop the current print job.

        Example API Return:
        {
            "cmd":317,
            "result":0
        }
        """
        payload = {
            "cmd": 317,
            "pro": "pr_off",
            "user": self._username,
            "pwd": self._password
        }
        return await self._do_post(payload, payload["pro"])

    async def get_model_info(self, filename: str):
        """
        Example API Return:

        {
            "cmd":322,
            "result":0,
            "uploaded":"2025/07/22 09:10:22",
            "size":180162,
            "filamentTotalUsed":7624.959961,
            "estimatedTotalTime":4657,
            "layerHeight":0.300000,
            "layerCount":3,
            "height":1.100000
        }
        """
        payload = {
            "cmd": 322,
            "pro": "get_model_info",
            "filename": filename,
            "user": self._username,
            "pwd": self._password
        }
        return await self._do_post(payload, payload["pro"])
