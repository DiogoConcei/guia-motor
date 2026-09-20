import time
import smbus2

class SensorMPU6050:
    def __init__(self, bus_number: int = 1, address: int = 0x68):
        self.bus_number: int = bus_number
        self.address: int = address
        self.bus = smbus2.SMBus(self.bus_number)

        # Fatores de escala padrão do MPU-6050
        # Acelerômetro configurado para +/- 2g
        self.accel_scale: float = 16384.0
        # Giroscópio configurado para +/- 250 graus/s
        self.gyro_scale: float = 131.0

        self._wakeup_sensor()

    def _wakeup_sensor(self):
        """O sensor inicia em modo de baixo consumo (dormindo). Escreve 0 no registrador de energia para acordá-lo."""
        power_mgmt_register: int = 0x6B
        self.bus.write_byte_data(self.address, power_mgmt_register, 0)
        time.sleep(0.1)

    def _read_raw_data(self, register: int):
        """Lê dois bytes do I2C e converte para um número inteiro com sinal (complemento de 2)."""
        high: int = self.bus.read_byte_data(self.address, register)
        low: int = self.bus.read_byte_data(self.address, register + 1)

        # Junta os dois bytes de 8 bits em um valor de 16 bits
        value: int = (high << 8) | low

        # Converte para número negativo caso passe da metade do limite (32768)
        if value > 32768:
            value = value - 65536

        return value

    def get_acceleration(self):
        """Retorna as acelerações nos eixos X, Y e Z em Força G."""
        x = self._read_raw_data(0x3B) / self.accel_scale
        y = self._read_raw_data(0x3D) / self.accel_scale
        z = self._read_raw_data(0x3F) / self.accel_scale

        return {"x": round(x, 2), "y": round(y, 2), "z": round(z, 2)}

    def get_gyroscope(self):
        """Retorna a rotação nos eixos X, Y e Z em graus por segundo."""
        x = self._read_raw_data(0x43) / self.gyro_scale
        y = self._read_raw_data(0x45) / self.gyro_scale
        z = self._read_raw_data(0x47) / self.gyro_scale

        return {"x": round(x, 2), "y": round(y, 2), "z": round(z, 2)}

    def get_temperature(self):
        """Retorna a temperatura interna do sensor em graus Celsius."""
        raw_temp = self._read_raw_data(0x41)
        # Fórmula padrão presente no datasheet do componente
        temp = (raw_temp / 340.0) + 36.53

        return round(temp, 2)