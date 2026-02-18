import random
from config import VELOCIDAD_BASE
import math
import config

class Animal:
    def __init__(self, col, fila, tipo):
        self.col = float(col)
        self.fila = float(fila)
        self.tipo = tipo # "gallina", "cabra"
        
        self.destino_col = self.col
        self.destino_fila = self.fila
        self.velocidad = VELOCIDAD_BASE * 0.5 # Más lentos que los humanos
        
        self.acciones = ["COMER", "CAMINAR", "DORMIR"]
        self.accion_actual = "CAMINAR"
        self.timer_accion = 0
        
        self.energia = 100
        self.vivo = True

    def update(self, mundo):
        if not self.vivo: return

        self.timer_accion -= 1
        
        if self.timer_accion <= 0:
            self.cambiar_comportamiento(mundo)

        if self.accion_actual == "CAMINAR":
            self.moverse()
        elif self.accion_actual == "COMER":
            # Si estamos en pasto, comemos (simulado)
            pass

    def cambiar_comportamiento(self, mundo):
        opcion = random.choice(self.acciones)
        self.accion_actual = opcion
        self.timer_accion = random.randint(60, 200) # 1 a 3 segundos
        
        if opcion == "CAMINAR":
            # Elegir destino cercano aleatorio
            dx = random.randint(-3, 3)
            dy = random.randint(-3, 3)
            nuevo_c = int(self.col + dx)
            nuevo_f = int(self.fila + dy)
            
            if mundo.es_transitable(nuevo_c, nuevo_f):
                self.destino_col = nuevo_c
                self.destino_fila = nuevo_f
            else:
                self.accion_actual = "ESPERAR"

    def moverse(self):
        dx = self.destino_col - self.col
        dy = self.destino_fila - self.fila
        dist = math.sqrt(dx*dx + dy*dy)
        
        if dist > self.velocidad:
            self.col += (dx / dist) * self.velocidad
            self.fila += (dy / dist) * self.velocidad
        else:
            self.col = self.destino_col
            self.fila = self.destino_fila
            self.accion_actual = "COMER" # Al llegar, pastar

    def to_dict(self):
        return {
            "col": self.col,
            "fila": self.fila,
            "tipo": self.tipo,
            "destino_col": self.destino_col,
            "destino_fila": self.destino_fila,
            "accion_actual": self.accion_actual,
            "timer_accion": self.timer_accion,
            "energia": self.energia,
            "vivo": self.vivo
        }

    @classmethod
    def from_dict(cls, data):
        a = cls(data["col"], data["fila"], data["tipo"])
        a.destino_col = data.get("destino_col", a.col)
        a.destino_fila = data.get("destino_fila", a.fila)
        a.accion_actual = data.get("accion_actual", "CAMINAR")
        a.timer_accion = data.get("timer_accion", 0)
        a.energia = data.get("energia", 100)
        a.vivo = data.get("vivo", True)
        return a
