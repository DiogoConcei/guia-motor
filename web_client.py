from websockets.sync.client import connect
from zeroconf import Zeroconf
from web_streaming import WebStream
import time


class WebClient:
    def __init__(self, cam):
        self.byte_ip: bytes | str = ""
        self.port: int | None = None
        self.url: str = ""
        self.message: str = ""
        self.timer = time.perf_counter()
        self.service_type = "_ws._tcp.local."
        self.cam = cam
        self.web_streaming = None

    def start(self):
        with Zeroconf() as zc:
            server_info = zc.get_service_info(f"{self.service_type}", f"PudimBrain.{self.service_type}")

            if server_info is None:
                raise ConnectionError("Servidor não encontrado")

            addresses = server_info.parsed_addresses()

            if not addresses:
                raise ConnectionError("Nenhum ip encontrado")

            self.byte_ip = addresses[0]
            self.port = server_info.port

        # Condicional
            self.url = f"ws://{self.byte_ip}:{self.port}/image"

        with connect(self.url) as websocket:
            self.start_stream(websocket)

    def start_stream(self, ws):
        self.web_streaming = WebStream(self.cam, ws)

        while True:
            self.web_streaming.stream()
