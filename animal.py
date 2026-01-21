import pygame
import random
import math
from config import *

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

    def dibujar(self, pantalla, mundo, camara_x, camara_y):
        iso_x, iso_y = mundo.grid_to_iso(self.col, self.fila)
        
        try:
            altura = mundo.obtener_altura(self.col, self.fila)
        except:
            altura = 0
            
        OFFSET_CAPAS = int(15 * mundo.zoom)
        offset_y_terreno = (altura - 1) * OFFSET_CAPAS if altura > 0 else -10 
        
        x_dibujo = iso_x - camara_x
        y_dibujo = iso_y - camara_y - offset_y_terreno
        
        z = mundo.zoom
        
        # --- DIBUJO ---
        color = COLOR_GALLINA if self.tipo == "gallina" else COLOR_CABRA
        radio = int(6 * z) if self.tipo == "gallina" else int(10 * z)
        
        # Sombra
        pygame.draw.ellipse(pantalla, (0,0,0, 80), (x_dibujo - radio, y_dibujo - radio//2, radio*2, radio))
        
        # Cuerpo
        pygame.draw.circle(pantalla, color, (x_dibujo, y_dibujo - radio), radio)
        
        # Detalle (Pico o Cuernos)
        if self.tipo == "gallina":
             pygame.draw.circle(pantalla, (255, 100, 0), (x_dibujo + int(4*z), y_dibujo - int(4*z)), int(3*z))
        elif self.tipo == "cabra":
             pygame.draw.line(pantalla, (50,50,50), (x_dibujo - int(2*z), y_dibujo - int(12*z)), (x_dibujo - int(8*z), y_dibujo - int(18*z)), int(2*z))
             pygame.draw.line(pantalla, (50,50,50), (x_dibujo + int(2*z), y_dibujo - int(12*z)), (x_dibujo + int(8*z), y_dibujo - int(18*z)), int(2*z))

