import time

try:
    import RPi.GPIO as GPIO
except (ImportError, RuntimeError):
    class DummyPWM:
        def __init__(self, pin, freq): pass

        def start(self, dc): pass

        def ChangeDutyCycle(self, dc): pass

        def stop(self): pass


    class GPIO_Mock:
        BCM = 'BCM'
        OUT = 'OUT'
        LOW = 0
        HIGH = 1

        def setmode(self, *args, **kwargs): pass

        def setwarnings(self, *args, **kwargs): pass

        def setup(self, *args, **kwargs): pass

        def output(self, *args, **kwargs): pass

        def cleanup(self, *args, **kwargs): pass

        def PWM(self, pin, freq): return DummyPWM(pin, freq)


    GPIO = GPIO_Mock()


class ControleMotores:
    def __init__(
            self,
            motor_esq_1: tuple[int, int] = (17, 27),
            motor_esq_2: tuple[int, int] = (2, 3),
            motor_dir_1: tuple[int, int] = (14, 15),
            motor_dir_2: tuple[int, int] = (23, 24),
            frequencia_pwm: int = 1000
    ):
        self.motores_esquerda: list[tuple[int, int]] = [motor_esq_1, motor_esq_2]
        self.motores_direita: list[tuple[int, int]] = [motor_dir_1, motor_dir_2]
        self.todos_pinos: list[int] = list(motor_esq_1 + motor_esq_2 + motor_dir_1 + motor_dir_2)

        # Lista para lembrar quais pinos estão ativados no momento
        self.pinos_ativos: list[int] = []

        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(self.todos_pinos, GPIO.OUT)

        self.pwms: dict = {}
        for pino in self.todos_pinos:
            pwm = GPIO.PWM(pino, frequencia_pwm)
            pwm.start(0)
            self.pwms[pino] = pwm

    def _limitar_velocidade(self, velocidade: int):
        return max(0, min(100, velocidade))

    def _acionar_motores(self, motores: list[tuple[int, int]], frente: bool, velocidade: int):
        vel = self._limitar_velocidade(velocidade)

        for pino_avanco, pino_recuo in motores:
            if frente:
                self.pwms[pino_avanco].ChangeDutyCycle(vel)
                self.pwms[pino_recuo].ChangeDutyCycle(0)

                # Guarda apenas o pino que está girando
                if pino_avanco not in self.pinos_ativos:
                    self.pinos_ativos.append(pino_avanco)
                if pino_recuo in self.pinos_ativos:
                    self.pinos_ativos.remove(pino_recuo)
            else:
                self.pwms[pino_avanco].ChangeDutyCycle(0)
                self.pwms[pino_recuo].ChangeDutyCycle(vel)

                if pino_recuo not in self.pinos_ativos:
                    self.pinos_ativos.append(pino_recuo)
                if pino_avanco in self.pinos_ativos:
                    self.pinos_ativos.remove(pino_avanco)

    def frente(self, velocidade: int = 100):
        self._acionar_motores(self.motores_esquerda, frente=True, velocidade=velocidade)
        self._acionar_motores(self.motores_direita, frente=True, velocidade=velocidade)

    def re(self, velocidade: int = 100):
        self._acionar_motores(self.motores_esquerda, frente=False, velocidade=velocidade)
        self._acionar_motores(self.motores_direita, frente=False, velocidade=velocidade)

    def girar_esquerda(self, velocidade: int = 100):
        self._acionar_motores(self.motores_esquerda, frente=False, velocidade=velocidade)
        self._acionar_motores(self.motores_direita, frente=True, velocidade=velocidade)

    def girar_direita(self, velocidade: int = 100):
        self._acionar_motores(self.motores_esquerda, frente=True, velocidade=velocidade)
        self._acionar_motores(self.motores_direita, frente=False, velocidade=velocidade)

    def desacelerar_motores(self):
        """Reduz a velocidade de 100 a 0 em passos de 20, afetando apenas os pinos em movimento."""
        # O range vai de 100 até -1, reduzindo de 20 em 20 (100, 80, 60, 40, 20, 0)
        for velocidade in range(100, -1, -20):
            for pino in self.pinos_ativos:
                self.pwms[pino].ChangeDutyCycle(velocidade)

            # Pausa de 0.2 segundos para a roda ter tempo físico de desacelerar
            time.sleep(0.2)

            # Após zerar, limpa a lista de pinos ativos
        self.pinos_ativos.clear()

    def parar(self):
        for pino in self.todos_pinos:
            self.pwms[pino].ChangeDutyCycle(0)
        self.pinos_ativos.clear()

    def release(self):
        self.parar()
        for pino in self.todos_pinos:
            self.pwms[pino].stop()