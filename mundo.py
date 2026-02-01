import os
import random
import math
import heapq
from config import *
from animal import Animal

class Mundo:
    def __init__(self):
        self.mapa_logico = []
        self.edificios = {} 
        
        # --- ECONOMÍA ACTUALIZADA ---
        self.recursos_totales = {"madera": 0, "piedra": 0, "comida": 0}
        
        # --- CICLO DÍA/NOCHE ---
        self.tiempo = 0.3 
        self.dia = 1
        self.mes = 1
        self.anio = 1
        self.color_ambiente = (0,0,0,0) # Backend calcula alpha/overlay logic si es necesario, o solo envía tiempo. Enviamos color igual.
        
        # --- ANIMALES ---
        self.animales = []
        
        # --- BITÁCORA (LOG DE EVENTOS) ---
        self.bitacora = [] # Lista de {mensaje, tipo, fecha}

        self.generar_mundo_fractal()

    def registrar_evento(self, mensaje, tipo="info"):
        # Tipos: info, nacimiento, muerte, construccion, descubrimiento
        fecha_str = f"A{self.anio}/M{self.mes}/D{self.dia}"
        evento = {
            "mensaje": mensaje,
            "tipo": tipo,
            "fecha": fecha_str
        }
        self.bitacora.insert(0, evento) # Insertar al inicio (más reciente primero)
        if len(self.bitacora) > 50:
            self.bitacora.pop() # Mantener solo 50 últimos

    def actualizar_tiempo(self):
        # Avanzar el tiempo
        # Incremento por frame = 1.0 / (Segundos * FPS)
        incremento = 1.0 / (DURACION_DIA_SEGUNDOS * FPS)
        self.tiempo += incremento
        nuevo_dia = False
        if self.tiempo >= 1.0:
            self.tiempo = 0.0 # Nuevo día
            self.dia += 1
            nuevo_dia = True
            
            # Calendario Simplificado (30 días = 1 mes, 12 meses = 1 año)
            if self.dia > 30:
                self.dia = 1
                self.mes += 1
                if self.mes > 12:
                    self.mes = 1
                    self.anio += 1
            
        # Calcular color ambiente (Overlay) - Útil para el frontend si quiere usar este dato
        # 0.0 - 0.2: Amanecer (Oscuro -> Claro)
        # 0.2 - 0.7: Día (Transparente)
        # 0.7 - 0.8: Atardecer (Naranja -> Oscuro)
        # 0.8 - 1.0: Noche (Oscuro)
        
        alpha = 0
        color = (0,0,0)
        
        if self.tiempo < 0.2: # Amanecer
            progreso = self.tiempo / 0.2
            alpha = int(MAX_OSCURIDAD * (1 - progreso))
            color = (20, 20, 40)
            
        elif self.tiempo < 0.7: # Día pleno
            alpha = 0
            
        elif self.tiempo < 0.8: # Atardecer
            progreso = (self.tiempo - 0.7) / 0.1
            alpha = int(MAX_OSCURIDAD * 0.6 * progreso)
            color = (255, 150, 50)
            
        else: # Noche
            alpha = MAX_OSCURIDAD
            color = COLOR_NOCHE

        self.color_ambiente = (color[0], color[1], color[2], alpha)
        return nuevo_dia
    
    def actualizar_naturaleza(self):
        # Simulación ecológica estocástica
        import random
        for _ in range(20):
            c = random.randint(0, COLUMNAS - 1)
            f = random.randint(0, FILAS - 1)
            
            tile = self.mapa_logico[f][c]
            
            # Solo crece en tierra vacía y transitable
            if tile["transitable"] and tile["recurso"] is None:
                if tile["tipo"] == "pasto":
                    # Probabilidad de brote espontáneo
                    rng = random.random()
                    if rng < 0.005:  # 0.5% de probabilidad
                        # Qué crece?
                        opciones = ["arbol", "fruta", "vegetal", "animal"]
                        pesos = [0.4, 0.3, 0.2, 0.1]
                        eleccion = random.choices(opciones, weights=pesos)[0]
                        
                        if eleccion == "animal":
                            # SPAM ANIMALES DINÁMICOS
                            tipo = random.choice(["gallina", "cabra"])
                            self.animales.append(Animal(c, f, tipo))
                        else:
                            tile["recurso"] = eleccion
                        
                        tile["transitable"] = True 
                        
                elif tile["tipo"] == "arena":
                     if random.random() < 0.001: # Muy raro en arena
                         tile["recurso"] = "roca"  

    def generar_mundo_fractal(self):
        print("Generando biomas y comida...")
        seed1 = random.randint(0, 1000)
        seed2 = random.randint(0, 1000)
        seed3 = random.randint(0, 1000)

        for fila in range(FILAS):
            fila_datos = []
            for col in range(COLUMNAS):
                # 1. Ruido Fractal Base
                e1 = math.sin(col * 0.05 + seed1) + math.cos(fila * 0.05 + seed1)
                e2 = 0.5 * (math.sin(col * 0.15 + seed2) + math.cos(fila * 0.15 + seed2))
                ruido = e1 + e2 
                
                # 2. Máscara de Isla (Circular)
                nx = 2 * col / COLUMNAS - 1
                ny = 2 * fila / FILAS - 1
                distancia_centro = math.sqrt(nx*nx + ny*ny)
                
                mascara = (1 - distancia_centro * 1.2)
                elevacion = ruido + mascara * 2 - 1.5 
                
                if distancia_centro > 0.85: elevacion = -2.0 
                
                recurso = None
                transitable = True
                altura = 1
                color = (0,0,0) # Placeholder, frontend decide colores
                
                if elevacion < -0.8: # Agua profunda
                    tipo = "agua"; transitable = False;
                    altura = 0
                elif elevacion < -0.6: # Playa
                    tipo = "arena"; transitable = True;
                    altura = 1
                    rng = random.random()
                    if rng < 0.02: recurso = "roca"
                    elif rng < 0.04: recurso = "vegetal"
                elif elevacion < 1.0: # Pasto/Bosque
                    tipo = "pasto"; transitable = True;
                    altura = 2
                    if elevacion > 0.2: altura = 3 
                    
                    densidad = math.sin(col * 0.1 + seed3) + math.cos(fila * 0.1 + seed3)
                    rng = random.random()
                    
                    if densidad > 0.5: 
                        if rng < 0.30: recurso = "arbol"
                        elif rng < 0.35: recurso = "fruta"
                    else: 
                        if rng < 0.05: recurso = "arbol"
                        elif rng < 0.08: recurso = "animal"
                else: # Montaña
                    tipo = "piedra"; transitable = True;
                    altura = int(4 + (elevacion * 2))
                    if altura > 10: altura = 10
                    
                    if random.random() < 0.15: recurso = "roca"
                    if elevacion > 1.5: transitable = False 

                fila_datos.append({"tipo": tipo, "transitable": transitable, "recurso": recurso, "altura": altura})
            self.mapa_logico.append(fila_datos)
        
        # --- COLOCAR CENTRO URBANO ---
        cx, cy = COLUMNAS // 2, FILAS // 2
        for dy in range(-2, 3):
            for dx in range(-2, 3):
                if 0 <= cx+dx < COLUMNAS and 0 <= cy+dy < FILAS:
                    self.mapa_logico[cy+dy][cx+dx]["altura"] = 2
                    self.mapa_logico[cy+dy][cx+dx]["tipo"] = "pasto"
                    self.mapa_logico[cy+dy][cx+dx]["transitable"] = True
                    self.mapa_logico[cy+dy][cx+dx]["recurso"] = None
        
        self.colocar_edificio(cx, cy, "centro")
        print(f"Centro urbano establecido en {cx}, {cy}")
        
        # --- NUEVO: ASEGURAR CONECTIVIDAD (FLOOD FILL) ---
        self.asegurar_conectividad(cx, cy)

    def asegurar_conectividad(self, start_x, start_y):
        # 1. Identificar la isla principal usando Flood Fill desde el centro
        visitados = set()
        cola = [(start_x, start_y)]
        visitados.add((start_x, start_y))
        
        while cola:
            cx, cy = cola.pop(0)
            
            vecinos = [(0, 1), (0, -1), (1, 0), (-1, 0)]
            for dx, dy in vecinos:
                nx, ny = cx + dx, cy + dy
                
                if 0 <= nx < COLUMNAS and 0 <= ny < FILAS:
                    tile = self.mapa_logico[ny][nx]
                    if (nx, ny) not in visitados and tile["transitable"]:
                        visitados.add((nx, ny))
                        cola.append((nx, ny))
        
        # 2. Eliminar islas desconectadas (las convertimos en agua)
        # Opcional: construir puentes. Por ahora, limpiamos el mapa.
        print(f"Isla principal: {len(visitados)} tiles.")
        
        cambios = 0
        for f in range(FILAS):
            for c in range(COLUMNAS):
                if (c, f) not in visitados:
                    tile = self.mapa_logico[f][c]
                    if tile["transitable"] and tile["tipo"] != "agua":
                        # Isla desconectada -> Convertir en agua
                        tile["tipo"] = "agua"
                        tile["transitable"] = False
                        tile["altura"] = 0
                        tile["recurso"] = None
                        cambios += 1
                        
        print(f"Se eliminaron {cambios} tiles desconectados para asegurar una sola isla.")

    def obtener_recurso(self, col, fila):
        if 0 <= col < COLUMNAS and 0 <= fila < FILAS: return self.mapa_logico[int(fila)][int(col)]["recurso"]
        return None
    def eliminar_recurso(self, col, fila):
        if 0 <= col < COLUMNAS and 0 <= fila < FILAS:
            self.mapa_logico[int(fila)][int(col)]["recurso"] = None
            self.mapa_logico[int(fila)][int(col)]["transitable"] = True
    def es_transitable(self, col, fila):
        if 0 <= col < COLUMNAS and 0 <= fila < FILAS: return self.mapa_logico[int(fila)][int(col)]["transitable"]
        return False
    def obtener_tipo(self, col, fila):
        if 0 <= col < COLUMNAS and 0 <= fila < FILAS: return self.mapa_logico[int(fila)][int(col)]["tipo"]
        return None
    def colocar_edificio(self, col, fila, tipo):
        if 0 <= col < COLUMNAS and 0 <= fila < FILAS:
            self.edificios[(col, fila)] = tipo
            self.mapa_logico[fila][col]["recurso"] = None

    def depositar_recursos(self, inventario_habitante):
        for tipo, cantidad in inventario_habitante.items():
            if tipo in self.recursos_totales:
                self.recursos_totales[tipo] += cantidad
            elif tipo in ["animal", "vegetal", "fruta"]:
                self.recursos_totales["comida"] += cantidad
        return {"madera": 0, "piedra": 0, "comida": 0, "animal":0, "vegetal":0, "fruta":0}

    def obtener_altura(self, col, fila):
        if 0 <= col < COLUMNAS and 0 <= fila < FILAS:
             return self.mapa_logico[int(fila)][int(col)]["altura"]
        return 0

    # --- PATHFINDING A* (Búsqueda de caminos) ---
    def heuristica(self, a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def obtener_camino(self, inicio, fin):
        start_node = (int(inicio[0]), int(inicio[1]))
        end_node = (int(fin[0]), int(fin[1]))

        if not self.es_transitable(end_node[0], end_node[1]):
             found_neighbor = False
             vecinos = [(0, 1), (0, -1), (1, 0), (-1, 0)]
             for dx, dy in vecinos:
                 nx, ny = end_node[0] + dx, end_node[1] + dy
                 if self.es_transitable(nx, ny):
                     end_node = (nx, ny)
                     found_neighbor = True
                     break
             if not found_neighbor:
                 return []

        frontera = []
        heapq.heappush(frontera, (0, start_node))
        origenes = {}
        costo_acumulado = {}
        
        origenes[start_node] = None
        costo_acumulado[start_node] = 0
        
        while frontera:
            current = heapq.heappop(frontera)[1]
            if current == end_node: break
            
            vecinos = [(0, 1), (0, -1), (1, 0), (-1, 0)]
            for dx, dy in vecinos:
                next_node = (current[0] + dx, current[1] + dy)
                
                if 0 <= next_node[0] < COLUMNAS and 0 <= next_node[1] < FILAS:
                    if self.mapa_logico[next_node[1]][next_node[0]]["transitable"]:
                        new_cost = costo_acumulado[current] + 1
                        if next_node not in costo_acumulado or new_cost < costo_acumulado[next_node]:
                            costo_acumulado[next_node] = new_cost
                            prioridad = new_cost + self.heuristica(end_node, next_node)
                            heapq.heappush(frontera, (prioridad, next_node))
                            origenes[next_node] = current
                            
        camino = []
        if end_node not in origenes: return [] 
            
        curr = end_node
        while curr != start_node:
            camino.append(curr)
            curr = origenes[curr]
        camino.reverse()
        return camino

    def obtener_animal_en_pos(self, col, fila, radio=1):
        for animal in self.animales:
             d = math.sqrt((animal.col - col)**2 + (animal.fila - fila)**2)
             if d < radio:
                 return animal
        return None

    def eliminar_animal(self, animal):
        if animal in self.animales:
            self.animales.remove(animal)