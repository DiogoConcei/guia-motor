NORMAL = "NORMAL"
DESVIANDO = "DESVIANDO"
PARADO = "PARADO"

class StateMachine:
    def __init__(self):
        self.estado_atual = NORMAL

    def _estado_atual(self):
        return self.estado_atual

    def _troca_estado(self):
        pass

    def _estado_normal(self):
        pass

    def _estado_parado(self):
        pass

    def _estado_desviando(self):
        pass