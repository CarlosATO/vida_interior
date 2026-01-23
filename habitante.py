import os
import math
import random
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
            "hambre": 20,      # 0 = lleno, 100 = muriendo
            "sed": 10,         # Nueva necesidad: SED
            "energia": 80,     # No empiezan al 100 para que duerman antes
            "social": 40,      # Necesitan amigos
            "diversion": 50
        }
        
        # Personalidad (Factores multiplicadores)
        self.personalidad = {
            "trabajador": random.uniform(0.8, 1.2),
            "sociable": random.uniform(0.8, 1.2),
            "gloton": random.uniform(0.8, 1.2),
            "curioso": random.uniform(0.8, 1.2)
        }

        # Colores Identidad (Procedural temporal - Para frontend)
        self.color_cuerpo = "#6496FF" if genero == "Masculino" else "#FF6496"
        if nombre == "Mateo": self.color_cuerpo = "#5078DC"
        elif nombre == "Sofia": self.color_cuerpo = "#DC64B4"
        
        # --- SOCIEDAD ---
        self.pareja = None
        self.compatibilidad = {} # {nombre_otro: 0-100}

        # --- CONOCIMIENTO (NUEVO) ---
        self.conocimientos = []
        self.es_heroe = False
        self.tiempo_invencion = 0
        
        # Estado Visual (Bocadillos)
        self.tiempo_bocadillo = 0
        self.mensaje_actual = ""

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
        
        # Deterioro pasivo de necesidades (MAS RÁPIDO para debug/actividad)
        self.necesidades["hambre"] += 0.05 * self.personalidad["gloton"]
        self.necesidades["sed"] += 0.08 # Sed sube rápido
        self.necesidades["energia"] -= 0.02 * self.personalidad["trabajador"] 
        self.necesidades["social"] -= 0.02 * self.personalidad["sociable"]
        
        # Clamp valores
        for k in self.necesidades:
            self.necesidades[k] = max(0, min(100, self.necesidades[k]))

        # 3. Obedecer
        if orden == "ESPERAR":
            self.accion_actual = "ESPERAR"
            # Si estoy aburrido, buscar algo que hacer random
            if random.random() < 0.1:
                self.accion_actual = "BUSCANDO"

        elif orden == "BEBER":
            self.accion_actual = "BEBIENDO"
            c, f = datos # Coordenadas de agua
            
            # Moverse al agua si está lejos
            if abs(self.col - c) > 1 or abs(self.fila - f) > 1:
                self.camino = mundo.obtener_camino((self.col, self.fila), (c, f))
                self.moviendose = True
                self.accion_actual = "CAMINAR"
            else:
                # Beber
                self.necesidades["sed"] = 0
                self.necesidades["energia"] += 5
                print(f"💧 {self.nombre} bebió agua.")
                self.mensaje_actual = "💧"
                self.tiempo_bocadillo = 60

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
            
            # --- NUEVO: COMPORTAMIENTO COMUNITARIO ---
            # Si es de noche ( > 0.8) y no estamos durmiendo, ir al CENTRO
            # Asumimos que el centro está cerca de COL//2, FIL//2
            if mundo.tiempo > 0.82 and self.accion_actual != "DORMIR":
                # Ir al centro urbano
                cx, cy = COLUMNAS // 2, FILAS // 2
                # Offset aleatorio alrededor de la fogata
                destino_final = (cx + random.randint(-4, 4), cy + random.randint(-4, 4))
                if not mundo.es_transitable(destino_final[0], destino_final[1]):
                     destino_final = (cx, cy)
                
                # Al llegar, hablar
                dist = math.sqrt((self.col - destino_final[0])**2 + (self.fila - destino_final[1])**2)
                if dist < 3:
                     self.accion_actual = "SOCIALIZAR"
                     # Buscar a alguien para hablar
                     for otro in habitantes:
                         if otro != self:
                             d_otro = math.sqrt((self.col - otro.col)**2 + (self.fila - otro.fila)**2)
                             if d_otro < 4:
                                 self.interactuar(otro)
                                 break
                     return

            # --- PETICIÓN DE RUTA (A*) ---
            start = (int(round(self.col)), int(round(self.fila)))
            if start != destino_final:
                ruta = mundo.obtener_camino(start, destino_final)
                if ruta:
                    self.camino = ruta
                    self.moviendose = True
                else:
                    self.accion_actual = "ESPERAR"

        elif orden == "REPRODUCIR":
            self.accion_actual = "AMAR"
            if self.pareja:
                dist = math.sqrt((self.col - self.pareja.col)**2 + (self.fila - self.pareja.fila)**2)
                if dist < 2.0:
                    # Costo masivo
                    self.necesidades["energia"] -= 30
                    self.necesidades["social"] = 0 
                    
                    # Nace un bebé
                    nombre_hijo = random.choice(["Neo", "Trinity", "Morfeo", "Cifra", "Tanque", "Dozer", "Apoc", "Ratona"]) + str(random.randint(0,99))
                    genero_hijo = random.choice(["Masculino", "Femenino"])
                    
                    # Instanciar (Python permite usar la clase dentro de sus propios métodos si ya está definida o usando type(self))
                    # Usamos type(self) para ser seguros si cambiamos nombre clase
                    nuevo = type(self)(self.col, self.fila, nombre_hijo, genero_hijo)
                    
                    # Herencia simple
                    nuevo.personalidad["sociable"] = (self.personalidad["sociable"] + self.pareja.personalidad["sociable"]) / 2
                    
                    habitantes.append(nuevo)
                    print(f"👶 ¡Nació {nombre_hijo}! Hijos de {self.nombre} y {self.pareja.nombre}")
                    
                    self.mensaje_actual = "❤️"
                    self.tiempo_bocadillo = 120
                    # Cooldown for reproduction? High energy cost acts as soft cooldown.

        elif orden == "CRAFT":
            receta_nombre = datos
            receta = RECETAS_UNIVERSALES.get(receta_nombre)
            if receta:
                # Consumir recursos
                for ing, cant in receta.items():
                    self.inventario[ing] -= cant
                
                # Crear Item (Abstratto por ahora, solo flag o inventario)
                # Si es herramienta, bonus?
                if "herramienta" in receta_nombre.lower():
                    self.personalidad["trabajador"] *= 1.2 # Mejora trabajador?
                
                print(f"🔨 {self.nombre} fabricó {receta_nombre}")
                self.mensaje_actual = "🔨"
                self.tiempo_bocadillo = 60

        elif orden == "CONSTRUIR":
            # datos = "TipoEdificio"
            tipo_edificio = datos if datos else "casa"
            # Colocar en el mundo
            mundo.colocar_edificio(int(self.col), int(self.fila), tipo_edificio.lower())
            
            # Actualizar memoria propia y de testigos cercanos?
            self.memoria[(int(self.col), int(self.fila))] = f"edificio_{tipo_edificio.lower()}"
            
            print(f"🏠 {self.nombre} construyó {tipo_edificio}")
            self.mensaje_actual = "🏠"
            self.tiempo_bocadillo = 120
        
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
        
        # Intentar transmitir
        if tema not in receptor.conocimientos:
            # Receptor aprende!
            receptor.conocimientos.append(tema)
            print(f"🗣️ {self.nombre} enseñó {tema} a {receptor.nombre}")
            
            # Visuals (Datos para el frontend)
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