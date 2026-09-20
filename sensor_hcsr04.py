import time
import RPi.GPIO as GPIO
from threading import Thread, Lock


class SensorHCSR04(Thread):
    def __init__(self, trigger_pin: int, echo_pin: int):
        super().__init__()
        self.trigger_pin: int = trigger_pin
        self.echo_pin: int = echo_pin
        self.last_distance: float = 0.0
        self.count: int = 0
        self.is_broken: bool = False
        self.stopped = False
        self.lock = Lock()
        self.timeout: float = 0.05
        self._setup_gpio()

    def _setup_gpio(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(self.trigger_pin, GPIO.OUT)
        GPIO.setup(self.echo_pin, GPIO.IN)
        GPIO.output(self.trigger_pin, False)
        time.sleep(0.1)

    def run(self):
        while not self.stopped:
            if self.is_broken:
                self.stopped = True
                break

            temp = self.get_distance_cm()

            with self.lock:
                self.last_distance = temp

                if self.last_distance == -1.0:
                    self.count += 1

                if self.count > 3:
                    self.is_broken = True

    def read(self):
        with self.lock:
            return self.last_distance

    def exit(self):
        self.stopped = True
        self.join()
        self.cleanup()

    def get_distance_cm(self):
        """Dispara o sensor e calcula a distância em centímetros."""
        # 1. Envia um pulso de 10 microssegundos para iniciar a medição
        GPIO.output(self.trigger_pin, True)

        time.sleep(0.00001)
        GPIO.output(self.trigger_pin, False)

        start_time: float = time.time()
        stop_time: float = time.time()
        timeout_start: float = time.time()

        # 2. Espera o pino Echo ir para nível ALTO (início do retorno)
        while GPIO.input(self.echo_pin) == 0:
            start_time = time.time()
            if (start_time - timeout_start) > self.timeout:
                return -1.0  # Retorna −1 em caso de erro/timeout

        # 3. Espera o pino Echo ir para nível BAIXO (fim do retorno)
        while GPIO.input(self.echo_pin) == 1:
            stop_time = time.time()
            if (stop_time - timeout_start) > self.timeout:
                return -1.0  # Retorna −1 em caso de erro/timeout

        # 4. Calcula a distância (Velocidade do som = 34300 cm/s)
        # Divide por 2 porque o som vai e volta
        elapsed_time: float = stop_time - start_time
        distance: float = (elapsed_time * 34300) / 2

        return round(distance, 2)

    def cleanup(self):
        GPIO.cleanup([self.trigger_pin, self.echo_pin])
