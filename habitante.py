import pygame
import os
import math
import random
from config import *
from cerebro import Cerebro 

class Habitante:
    def __init__(self, col, fila, nombre, genero):
        self.nombre = nombre
        self.genero = genero 
        
        # --- CUERPO FÍSICO ---
        self.col = float(col)
        self.fila = float(fila)
        self.destino_col = self.col
        self.destino_fila = self.fila
        
        # --- PATHFINDING ---
        self.camino = [] # Lista de puntos (col, fila) a seguir
        
        # --- ESTADO FÍSICO ---
        self.inventario = {"madera": 0, "piedra": 0}
        
        # Estados
        self.accion_actual = "ESPERAR" 
        self.moviendose = False
        self.tiempo_trabajo = 0
        self.objetivo_trabajo = None 

        # --- CEREBRO & MENTE ---
        self.cerebro = Cerebro()
        self.memoria = {} # Mapa mental: {(col, fila): "tipo_recurso"}
        
        # Necesidades (0 a 100)
        self.necesidades = {
            "hambre": 0,      # 0 = lleno, 100 = muriendo
            "energia": 100,   # 100 = full, 0 = desmayado
            "social": 100,    # 100 = satisfecho, 0 = solo
            "diversion": 100  # 100 = feliz, 0 = aburrido
        }
        
        # Personalidad (Factores multiplicadores)
        self.personalidad = {
            "trabajador": random.uniform(0.8, 1.2),
            "sociable": random.uniform(0.8, 1.2),
            "gloton": random.uniform(0.8, 1.2),
            "curioso": random.uniform(0.8, 1.2)
        }

        # Colores Identidad (Procedural temporal)
        self.color_cuerpo = (100, 150, 255) if genero == "Masculino" else (255, 100, 150)
        if nombre == "Mateo": self.color_cuerpo = (80, 120, 220)
        elif nombre == "Sofia": self.color_cuerpo = (220, 100, 180)
        
        # --- SOCIEDAD ---
        self.pareja = None
        self.compatibilidad = {} # {nombre_otro: 0-100}

    def ejecutar_ordenes(self, mundo, habitantes):
        # 1. Si ya está ocupado...
        if self.moviendose:
            self.continuar_caminata()
            return
        
        if self.accion_actual == "TRABAJAR":
            self.continuar_trabajo(mundo)
            return

        # 2. Consultar al CEREBRO
        orden, datos = self.cerebro.pensar(self, mundo, habitantes)
        
        # Deterioro pasivo de necesidades
        self.necesidades["hambre"] += 0.02 * self.personalidad["gloton"]
        self.necesidades["energia"] -= 0.01 * self.personalidad["trabajador"] # Cansa existir
        self.necesidades["social"] -= 0.03 * self.personalidad["sociable"]
        
        # Clamp valores
        for k in self.necesidades:
            self.necesidades[k] = max(0, min(100, self.necesidades[k]))

        # 3. Obedecer
        if orden == "DORMIR":
            self.accion_actual = "DORMIR"
            self.necesidades["energia"] += 0.5
            if self.necesidades["energia"] >= 100:
                self.necesidades["energia"] = 100
                self.accion_actual = "ESPERAR" 

        elif orden == "DEPOSITAR":
            self.inventario = mundo.depositar_recursos(self.inventario)
            self.accion_actual = "ESPERAR"

        elif orden == "TRABAJAR":
            self.accion_actual = "TRABAJAR"
            self.objetivo_trabajo = datos
            self.tiempo_trabajo = 60
            print(f"{self.nombre}: Trabajando...")

        elif orden == "CAMINAR":
            self.accion_actual = "CAMINAR"
            destino_final = datos
            
            # --- PETICIÓN DE RUTA (A*) ---
            # Solo si no tenemos camino o cambió el destino
            start = (int(round(self.col)), int(round(self.fila)))
            if start != destino_final:
                ruta = mundo.obtener_camino(start, destino_final)
                if ruta:
                    self.camino = ruta
                    self.moviendose = True
                else:
                    self.accion_actual = "ESPERAR" # No encontró camino
                    # print(f"{self.nombre}: No encuentro camino a {destino_final}")

        elif orden == "COMER":
            self.accion_actual = "COMER"
            # datos es la posición de la comida o None si es del inventario
            if datos:
                # Estamos en la fuente de comida
                c_com, f_com = datos
                
                # 1. Intentar comer recurso estático
                recurso = mundo.obtener_recurso(c_com, f_com)
                animal = mundo.obtener_animal_en_pos(c_com, f_com, radio=1.5)
                
                if recurso in ["fruta", "vegetal"]:
                    mundo.eliminar_recurso(c_com, f_com)
                    self.necesidades["hambre"] = max(0, self.necesidades["hambre"] - 50)
                    self.necesidades["energia"] += 10
                    print(f"{self.nombre}: Comí {recurso}.")
                    
                elif animal:
                    mundo.eliminar_animal(animal)
                    self.necesidades["hambre"] = max(0, self.necesidades["hambre"] - 80) # Más nutritivo
                    self.necesidades["energia"] += 20
                    print(f"{self.nombre}: Cazó una {animal.tipo}.")
                    
                else:
                    print(f"{self.nombre}: ¡La comida desapareció!")
            else:
                 # Comiendo del inventario (si tuviéramos)
                 pass

            # Recupera un poco de energía al descansar quieto
            self.necesidades["energia"] += 0.05
            
        elif orden == "SOCIALIZAR":
            self.accion_actual = "HABLANDO"
            if datos: # datos es el otro habitante
                self.interactuar(datos)
        
        elif orden == "HACER_BEBE":
             self.accion_actual = "CORAZÓN"
             # La lógica de spawn ocurre en main.py al detectar este estado

    def interactuar(self, otro):
        # Aumentar necesidad social
        self.necesidades["social"] = min(100, self.necesidades["social"] + 5)
        
        # Calcular compatibilidad si no existe
        if otro.nombre not in self.compatibilidad:
            diff = abs(self.personalidad["sociable"] - otro.personalidad["sociable"])
            self.compatibilidad[otro.nombre] = 100 - (diff * 50) # 50 to 100 approx
            
        # Chance de enamorar
        comp = self.compatibilidad[otro.nombre]
        if self.pareja is None and otro.pareja is None:
            if comp > 80 and self.necesidades["social"] > 90:
                 # Se gustan
                 if random.random() < 0.05:
                     self.pareja = otro
                     otro.pareja = self
                     print(f"❤️ ¡{self.nombre} y {otro.nombre} son pareja!")

    def continuar_caminata(self):
        if not self.camino:
            self.moviendose = False
            self.accion_actual = "ESPERAR"
            return

        # Siguiente nodo en la lista
        target = self.camino[0] # (col, fila)
        
        dx = target[0] - self.col
        dy = target[1] - self.fila
        dist = math.sqrt(dx*dx + dy*dy)
        
        velocidad = VELOCIDAD_BASE
        
        if dist <= velocidad:
            # Llegamos al nodo
            self.col = float(target[0])
            self.fila = float(target[1])
            self.camino.pop(0) # Quitamos el nodo visitado
            self.necesidades["energia"] -= 0.5
        else:
            # Nos movemos hacia el nodo
            self.col += (dx / dist) * velocidad
            self.fila += (dy / dist) * velocidad
            self.necesidades["energia"] -= 0.5

    def continuar_trabajo(self, mundo):
        self.tiempo_trabajo -= 1
        self.necesidades["energia"] -= 0.2
        
        if self.tiempo_trabajo <= 0:
            c, f, tipo = self.objetivo_trabajo
            if mundo.obtener_recurso(c, f) == tipo:
                mundo.eliminar_recurso(c, f)
                if tipo == "arbol": self.inventario["madera"] += 1
                elif tipo == "roca": self.inventario["piedra"] += 1
            
            self.accion_actual = "ESPERAR"
            self.objetivo_trabajo = None

    def dibujar(self, pantalla, mundo, camara_x, camara_y):
        iso_x, iso_y = mundo.grid_to_iso(self.col, self.fila)
        
        # Ajuste de altura por terreno (Voxels)
        try:
            altura = mundo.obtener_altura(self.col, self.fila)
        except:
            altura = 0
            
        OFFSET_CAPAS = int(15 * mundo.zoom)
        offset_y_terreno = (altura - 1) * OFFSET_CAPAS if altura > 0 else -10 
        
        x_dibujo = iso_x - camara_x
        y_dibujo = iso_y - camara_y - offset_y_terreno
        
        # Verificar si está en pantalla
        if -50 < x_dibujo < ANCHO_PANTALLA + 50 and -50 < y_dibujo < ALTO_PANTALLA + 50:
            
            # --- DIBUJO PROCEDURAL "PREMIUM" MINIMALISTA (ESCALADO) ---
            z = mundo.zoom
            
            # Dimensiones base escaladas
            w_sombra = int(20 * z)
            h_sombra = int(10 * z)
            
            altura_cuerpo = int(35 * z)
            ancho_cuerpo = int(14 * z)
            
            # Sombra
            pygame.draw.ellipse(pantalla, (0,0,0, 100), (x_dibujo - w_sombra//2, y_dibujo - h_sombra//2, w_sombra, h_sombra))
            
            pie_y = y_dibujo - int(5 * z)
            cabeza_y = pie_y - altura_cuerpo
            
            rect_cuerpo = pygame.Rect(x_dibujo - ancho_cuerpo//2, cabeza_y, ancho_cuerpo, altura_cuerpo)
            pygame.draw.rect(pantalla, self.color_cuerpo, rect_cuerpo, border_radius=int(7*z))
            
            # Brillo volumen
            pygame.draw.line(pantalla, (255,255,255), (x_dibujo - int(3*z), cabeza_y + int(5*z)), (x_dibujo - int(3*z), cabeza_y + int(15*z)), int(2*z))

            # Cabeza / Identidad
            if self.genero == "Femenino":
                 pygame.draw.circle(pantalla, (250,250,250), (x_dibujo, cabeza_y + int(4*z)), int(2*z))
            
            # UI Minimalista (Iconos)
            if self.accion_actual == "TRABAJAR":
                font = pygame.font.SysFont("Arial", int(12*z), bold=True)
                pantalla.blit(font.render("!", True, (255, 255, 0)), (x_dibujo + int(8*z), cabeza_y))
            elif self.accion_actual == "DORMIR":
                 font = pygame.font.SysFont("Arial", int(12*z))
                 pantalla.blit(font.render("z", True, (200, 200, 255)), (x_dibujo + int(8*z), cabeza_y))

            # Barra de Energía
            if self.necesidades["energia"] < 100:
                width = int(20 * z)
                height = int(3 * z)
                if height < 1: height = 1
                bar_x = x_dibujo - width // 2
                bar_y = cabeza_y - int(8 * z)
                pct = self.necesidades["energia"] / 100.0
                pygame.draw.rect(pantalla, (50,50,50), (bar_x, bar_y, width, height))
                pygame.draw.rect(pantalla, (0, 255, 100), (bar_x, bar_y, width * pct, height))