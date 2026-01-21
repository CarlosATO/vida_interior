import pygame
import os
import math
import random
from config import *
from config import *
from cerebro import Cerebro, RECETAS_UNIVERSALES 

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

        # --- CONOCIMIENTO (NUEVO) ---
        self.conocimientos = []
        self.es_heroe = False
        self.tiempo_invencion = 0

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
        if orden == "ESPERAR":
            self.accion_actual = "ESPERAR"

        elif orden == "DORMIR":
            self.accion_actual = "DORMIR"
            self.necesidades["energia"] += 0.5
            if self.necesidades["energia"] >= 100:
                self.necesidades["energia"] = 100
                self.accion_actual = "ESPERAR" 

        elif orden == "RECOLECTAR":
            # datos = (c, f, tipo)
            c, f, tipo = datos
            self.accion_actual = "TRABAJAR" 
            self.objetivo_trabajo = (c, f, tipo)
            self.tiempo_trabajo = 60 # Iniciar contador
            
            # Ejecutar un frame de trabajo inmediatamente
            self.continuar_trabajo(mundo)

        elif orden == "EXPERIMENTAR":
            self.accion_actual = "PENSANDO"
            self.necesidades["energia"] -= 0.2
            
            # Lógica de Eureka
            # Elegir 2 items al azar del inventario (si tiene)
            items_disponibles = [k for k, v in self.inventario.items() if v > 0]
            if len(items_disponibles) >= 1:
                # Simular combinación (simplificado: solo chequeamos si tiene los ingredientes de alguna receta)
                # Iteramos recetas para ver si de casualidad "acierta"
                
                if random.random() < 0.02 * self.personalidad["curioso"]: # 2% chance per frame * curiosidad
                     # Intentar descubrir algo
                     for receta, ingredientes in RECETAS_UNIVERSALES.items():
                         if receta in self.conocimientos: continue
                         
                         tiene_todo = True
                         for ing, cant in ingredientes.items():
                             if self.inventario.get(ing, 0) < cant:
                                 tiene_todo = False
                                 break
                         
                         if tiene_todo:
                             # ¡EUREKA!
                             self.conocimientos.append(receta)
                             self.es_heroe = True
                             print(f"💡 ¡EUREKA! {self.nombre} descubrió: {receta} (experimentando)")
                             break
                             
        elif orden == "CAMINAR":
            self.accion_actual = "CAMINAR"
            destino_final = datos
            
            # --- PETICIÓN DE RUTA (A*) ---
            start = (int(round(self.col)), int(round(self.fila)))
            if start != destino_final:
                ruta = mundo.obtener_camino(start, destino_final)
                if ruta:
                    self.camino = ruta
                    self.moviendose = True
                else:
                    self.accion_actual = "ESPERAR"

        elif orden == "COMER":
            self.accion_actual = "COMER"
            if datos:
                c_com, f_com = datos
                recurso = mundo.obtener_recurso(c_com, f_com)
                animal = mundo.obtener_animal_en_pos(c_com, f_com, radio=1.5)
                
                if recurso in ["fruta", "vegetal"]:
                    mundo.eliminar_recurso(c_com, f_com)
                    self.necesidades["hambre"] = max(0, self.necesidades["hambre"] - 50)
                    self.necesidades["energia"] += 10
                    print(f"{self.nombre}: Comí {recurso}.")
                elif animal:
                    mundo.eliminar_animal(animal)
                    self.necesidades["hambre"] = max(0, self.necesidades["hambre"] - 80)
                    self.necesidades["energia"] += 20
                    print(f"{self.nombre}: Cazó una {animal.tipo}.")
                else:
                    pass

    def continuar_trabajo(self, mundo):
        if not self.objetivo_trabajo:
            self.accion_actual = "ESPERAR"
            return

        c, f, tipo = self.objetivo_trabajo
        
        # Verificar si el recurso sigue ahí
        if mundo.obtener_recurso(c, f) != tipo:
             self.accion_actual = "ESPERAR"
             self.objetivo_trabajo = None
             return

        # Continuar trabajando
        self.necesidades["energia"] -= 0.5
        self.tiempo_trabajo -= 1
        
        if self.tiempo_trabajo <= 0:
            mundo.eliminar_recurso(c, f)
            # Ganar item
            if tipo == "arbol": 
                self.inventario["madera"] += 1
                mundo.recursos_totales["madera"] += 1
            elif tipo == "roca": 
                self.inventario["piedra"] += 1
                mundo.recursos_totales["piedra"] += 1
                
            print(f"{self.nombre}: Terminó de recolectar {tipo}.")
            
            self.accion_actual = "ESPERAR"
            self.objetivo_trabajo = None

    def interactuar(self, otro):
        # Aumentar necesidad social
        self.necesidades["social"] = min(100, self.necesidades["social"] + 15)
        
        # Calcular compatibilidad si no existe
        if otro.nombre not in self.compatibilidad:
            diff = abs(self.personalidad["sociable"] - otro.personalidad["sociable"])
            self.compatibilidad[otro.nombre] = 100 - (diff * 50) 
            
        # --- LENGUAJE & ENSEÑANZA VIRAL ---
        # Si somos sociables, intentamos enseñar algo
        if random.random() < 0.5 * self.personalidad["sociable"]:
            self.hablar(otro)

        # Chance de enamorar
        comp = self.compatibilidad[otro.nombre]
        if self.pareja is None and otro.pareja is None:
            if comp > 80 and self.necesidades["social"] > 90:
                 if random.random() < 0.05:
                     self.pareja = otro
                     otro.pareja = self
                     print(f"❤️ ¡{self.nombre} y {otro.nombre} son pareja!")

    def hablar(self, receptor):
        # Elegir qué contar (Prioridad: Tecnologías)
        if not self.conocimientos: return # Nada que decir
        
        tema = random.choice(self.conocimientos)
        
        # Token de Conocimiento: (TIPO, CONTENIDO, CERTEZA)
        token = ("TECNOLOGIA", tema, 1.0)
        
        # Intentar transmitir
        if tema not in receptor.conocimientos:
            # Receptor aprende!
            receptor.conocimientos.append(tema)
            print(f"🗣️ {self.nombre} enseñó {tema} a {receptor.nombre}")
            
            # Visuals
            self.tiempo_bocadillo = 60
            self.mensaje_actual = "💬"
            receptor.tiempo_bocadillo = 60
            receptor.mensaje_actual = "💡"
        else:
             # Ya lo sabía, chismear
             self.tiempo_bocadillo = 30
             self.mensaje_actual = "bla"

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
            
            # Cabeza Femenina
            if self.genero == "Femenino":
                 pygame.draw.circle(pantalla, (250,250,250), (x_dibujo, cabeza_y + int(4*z)), int(2*z))
            
            # --- UI: BOCADILLO DE DIÁLOGO (NUEVO) ---
            if hasattr(self, "tiempo_bocadillo") and self.tiempo_bocadillo > 0:
                self.tiempo_bocadillo -= 1
                font_bubble = pygame.font.SysFont("Arial", int(14*z), bold=True)
                txt = font_bubble.render(getattr(self, "mensaje_actual", "."), True, (0,0,0))
                
                # Globo blanco
                rect_b = txt.get_rect(center=(x_dibujo, cabeza_y - int(15*z)))
                rect_b.inflate_ip(10, 5)
                pygame.draw.rect(pantalla, (255,255,255), rect_b, border_radius=5)
                pygame.draw.polygon(pantalla, (255,255,255), [(x_dibujo, rect_b.bottom), (x_dibujo-5, rect_b.bottom-5), (x_dibujo+5, rect_b.bottom-5)])
                
                pantalla.blit(txt, txt.get_rect(center=(x_dibujo, cabeza_y - int(15*z))))

            # Iconos de Estado (Dormir/Trabajar)
            elif self.accion_actual == "TRABAJAR":
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