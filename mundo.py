import pygame
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
        self.imagenes_bloques = {}
        self.imagenes_recursos = {} 
        self.imagenes_edificios = {}
        
        # --- ZOOM Y CÁMARA ---
        self.zoom = 1.0
        self.ancho_tile = ANCHO_TILE
        self.alto_tile = ALTO_TILE
        
        # Almacenamos las imágenes ORIGINALES para no perder calidad al escalar
        self.assets_base_bloques = {}
        self.assets_base_recursos = {}
        self.assets_base_edificios = {}
        
        # --- ECONOMÍA ACTUALIZADA ---
        self.recursos_totales = {"madera": 0, "piedra": 0, "comida": 0}
        
        # --- CICLO DÍA/NOCHE ---
        self.tiempo = 0.3 # Empezamos de día (0.0=Amanacer, 0.5=Mediodía, 1.0=Noche)
        self.color_ambiente = (0,0,0,0)
        
        # --- ANIMALES ---
        self.animales = []
        
        self.cargar_imagenes()
        self.generar_mundo_fractal()

    def actualizar_tiempo(self):
        # Avanzar el tiempo
        # Incremento por frame = 1.0 / (Segundos * FPS)
        incremento = 1.0 / (DURACION_DIA_SEGUNDOS * FPS)
        self.tiempo += incremento
        if self.tiempo >= 1.0:
            self.tiempo = 0.0 # Nuevo día
            
        # Calcular color ambiente (Overlay)
        # 0.0 - 0.2: Amanecer (Oscuro -> Claro)
        # 0.2 - 0.7: Día (Transparente)
        # 0.7 - 0.8: Atardecer (Naranja -> Oscuro)
        # 0.8 - 1.0: Noche (Oscuro)
        
        alpha = 0
        color = (0,0,0)
        
        if self.tiempo < 0.2: # Amanecer
            # De 180 a 0
            progreso = self.tiempo / 0.2
            alpha = int(MAX_OSCURIDAD * (1 - progreso))
            color = (20, 20, 40)
            
        elif self.tiempo < 0.7: # Día pleno
            alpha = 0
            
        elif self.tiempo < 0.8: # Atardecer
            progreso = (self.tiempo - 0.7) / 0.1
            alpha = int(MAX_OSCURIDAD * 0.6 * progreso) # Un poco oscuro
            color = (255, 150, 50) # Tono naranja
            
        else: # Noche
            # De atardecer a noche cerrada
            alpha = MAX_OSCURIDAD
            color = COLOR_NOCHE

        self.color_ambiente = (color[0], color[1], color[2], alpha)
    
    def actualizar_naturaleza(self):
        # Simulación ecológica estocástica (para no matar el CPU)
        # Elegimos 20 tiles al azar cada frame para ver si crece algo
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

    def cargar_imagenes(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        ruta_tiles = os.path.join(base_dir, "assets", "tiles")
        
        # Bloques
        tipos = ["pasto", "agua", "arena", "piedra", "pared"]
        for tipo in tipos:
            ruta = os.path.join(ruta_tiles, f"bloque_{tipo}.png")
            if os.path.exists(ruta):
                img = pygame.image.load(ruta).convert_alpha()
                self.assets_base_bloques[tipo] = img
                self.imagenes_bloques[tipo] = img
        
        # Edificios
        ruta_casa = os.path.join(ruta_tiles, "edificio_centro.png")
        if os.path.exists(ruta_casa):
            img = pygame.image.load(ruta_casa).convert_alpha()
            self.assets_base_edificios["centro"] = img
            self.imagenes_edificios["centro"] = img
            
        # Recursos
        recursos = ["arbol", "roca", "animal", "vegetal", "fruta"]
        for rec in recursos:
            ruta = os.path.join(ruta_tiles, f"recurso_{rec}.png")
            if os.path.exists(ruta):
                img = pygame.image.load(ruta).convert_alpha()
                self.assets_base_recursos[rec] = img
                self.imagenes_recursos[rec] = img
            else:
                print(f"⚠️ Faltó generar imagen para: {rec}")

    def cambiar_zoom(self, cambio):
        nuevo_zoom = self.zoom + cambio
        if nuevo_zoom < 0.5: nuevo_zoom = 0.5
        if nuevo_zoom > 2.0: nuevo_zoom = 2.0
        
        if nuevo_zoom != self.zoom:
            self.zoom = nuevo_zoom
            self.ancho_tile = int(ANCHO_TILE * self.zoom)
            self.alto_tile = int(ALTO_TILE * self.zoom)
            
            self._escalar_diccionario(self.assets_base_bloques, self.imagenes_bloques)
            self._escalar_diccionario(self.assets_base_recursos, self.imagenes_recursos)
            self._escalar_diccionario(self.assets_base_edificios, self.imagenes_edificios)

    def _escalar_diccionario(self, base, destino):
        for k, img_orig in base.items():
            w = int(img_orig.get_width() * self.zoom)
            h = int(img_orig.get_height() * self.zoom)
            destino[k] = pygame.transform.scale(img_orig, (w, h))

    def generar_mundo_fractal(self):
        print("Generando biomas y comida...")
        seed1 = random.randint(0, 1000)
        seed2 = random.randint(0, 1000)
        seed3 = random.randint(0, 1000)

        for fila in range(FILAS):
            fila_datos = []
        for fila in range(FILAS):
            fila_datos = []
            for col in range(COLUMNAS):
                # 1. Ruido Fractal Base
                e1 = math.sin(col * 0.05 + seed1) + math.cos(fila * 0.05 + seed1)
                e2 = 0.5 * (math.sin(col * 0.15 + seed2) + math.cos(fila * 0.15 + seed2))
                ruido = e1 + e2 
                
                # 2. Máscara de Isla (Circular)
                # Normalizamos coordenadas a rango [-1, 1]
                nx = 2 * col / COLUMNAS - 1
                ny = 2 * fila / FILAS - 1
                distancia_centro = math.sqrt(nx*nx + ny*ny)
                
                # La elevación baja drásticamente cuanto más lejos del centro
                # Usamos una función suave: (1 - distancia^2)
                mascara = (1 - distancia_centro * 1.2)
                
                elevacion = ruido + mascara * 2 - 1.5 # Ajuste mágico para equilibrar
                
                # Forzar agua en los bordes extremos
                if distancia_centro > 0.85: elevacion = -2.0 
                
                recurso = None
                transitable = True
                altura = 1 # Altura base
                
                if elevacion < -0.8: # Agua profunda
                    tipo = "agua"; transitable = False; color = (0, 0, 180)
                    altura = 0
                elif elevacion < -0.6: # Playa
                    tipo = "arena"; transitable = True; color = (240, 230, 140)
                    altura = 1
                    rng = random.random()
                    if rng < 0.02: recurso = "roca"
                    elif rng < 0.04: recurso = "vegetal"
                elif elevacion < 1.0: # Pasto/Bosque
                    tipo = "pasto"; transitable = True; color = (34, 139, 34)
                    altura = 2
                    if elevacion > 0.2: altura = 3 # Variación
                    
                    densidad = math.sin(col * 0.1 + seed3) + math.cos(fila * 0.1 + seed3)
                    rng = random.random()
                    
                    if densidad > 0.5: 
                        if rng < 0.30: recurso = "arbol"
                        elif rng < 0.35: recurso = "fruta"
                    else: 
                        if rng < 0.05: recurso = "arbol"
                        elif rng < 0.08: recurso = "animal"
                else: # Montaña
                    tipo = "piedra"; transitable = True; color = (120, 120, 120)
                    altura = int(4 + (elevacion * 2))
                    if altura > 10: altura = 10
                    
                    if random.random() < 0.15: recurso = "roca"
                    if elevacion > 1.5: transitable = False 

                fila_datos.append({"tipo": tipo, "transitable": transitable, "color": color, "recurso": recurso, "altura": altura})
            self.mapa_logico.append(fila_datos)
        
        # --- COLOCAR CENTRO URBANO ---
        cx, cy = COLUMNAS // 2, FILAS // 2
        # Aplanar el terreno para el centro
        for dy in range(-2, 3):
            for dx in range(-2, 3):
                if 0 <= cx+dx < COLUMNAS and 0 <= cy+dy < FILAS:
                    self.mapa_logico[cy+dy][cx+dx]["altura"] = 2
                    self.mapa_logico[cy+dy][cx+dx]["tipo"] = "pasto"
                    self.mapa_logico[cy+dy][cx+dx]["transitable"] = True
                    self.mapa_logico[cy+dy][cx+dx]["recurso"] = None
        
        self.colocar_edificio(cx, cy, "centro")
        print(f"Centro urbano establecido en {cx}, {cy}")

    # --- FUNCIONES DE UTILIDAD Y DIBUJO ---
    def grid_to_iso(self, col, fila):
        iso_x = (col - fila) * (self.ancho_tile // 2) + OFFSET_X
        iso_y = (col + fila) * (self.alto_tile // 2) + OFFSET_Y
        return iso_x, iso_y

    def iso_to_grid(self, pantalla_x, pantalla_y, camara_x, camara_y):
        adj_x = pantalla_x + camara_x - OFFSET_X
        adj_y = pantalla_y + camara_y - OFFSET_Y
        mitad_ancho = self.ancho_tile // 2
        mitad_alto = self.alto_tile // 2
        # Evitar div por cero si zoom es muy chiquito
        if mitad_ancho == 0: mitad_ancho = 1
        if mitad_alto == 0: mitad_alto = 1
        
        col = (adj_x / mitad_ancho + adj_y / mitad_alto) / 2
        fila = (adj_y / mitad_alto - (adj_x / mitad_ancho)) / 2
        return int(col), int(fila)

    def dibujar_rombo_fallback(self, pantalla, color, x, y):
        mitad_ancho = self.ancho_tile // 2
        mitad_alto = self.alto_tile // 2
        puntos = [(x, y), (x + mitad_ancho, y + mitad_alto), (x, y + self.alto_tile), (x - mitad_ancho, y + mitad_alto)]
        pygame.draw.polygon(pantalla, color, puntos)
        pygame.draw.polygon(pantalla, (0,0,0), puntos, 1)

    def dibujar_recurso_fallback(self, pantalla, tipo_recurso, x, y):
        # Plan B si fallan las imágenes nuevas
        color = (255, 255, 255)
        if tipo_recurso == "animal": color = (150, 100, 50) 
        elif tipo_recurso == "vegetal": color = (50, 200, 50) 
        elif tipo_recurso == "fruta": color = (200, 50, 50) 
        radio = int(8 * self.zoom)
        pygame.draw.circle(pantalla, color, (x, y + int(15*self.zoom)), radio)

    def dibujar(self, pantalla, camara_x, camara_y):
        buffer = 200
        OFFSET_CAPAS = int(15 * self.zoom) # Escalar el apilado

        for fila in range(FILAS):
            for col in range(COLUMNAS):
                iso_x, iso_y = self.grid_to_iso(col, fila)
                screen_x = iso_x - camara_x
                screen_y = iso_y - camara_y
                
                if not (-buffer < screen_x < ANCHO_PANTALLA + buffer and -buffer < screen_y < ALTO_PANTALLA + buffer): continue
                
                tile = self.mapa_logico[fila][col]
                tipo = tile["tipo"]
                altura = tile["altura"]
                
                # --- 1. DIBUJAR TERRENO (APILADO) ---
                capas = altura if altura > 0 else 1
                if tipo == "agua": capas = 1 
                
                top_y = screen_y 

                if tipo in self.imagenes_bloques:
                    img = self.imagenes_bloques[tipo]
                    mitad_bloque = self.ancho_tile // 2
                    for i in range(capas):
                        draw_y = screen_y - (i * OFFSET_CAPAS)
                        top_y = draw_y 
                        pantalla.blit(img, (screen_x - mitad_bloque, draw_y))
                    
                    if altura == 0: 
                         pantalla.blit(img, (screen_x - mitad_bloque, screen_y + int(10*self.zoom)))
                         top_y = screen_y + int(10*self.zoom)

                else: 
                     self.dibujar_rombo_fallback(pantalla, tile["color"], screen_x, screen_y)

                # --- 2. DIBUJAR OBJETOS ENCIMA ---
                if tile["recurso"]:
                    if tile["recurso"] in self.imagenes_recursos:
                        img = self.imagenes_recursos[tile["recurso"]]
                        off_x = (self.ancho_tile - img.get_width()) // 2
                        # Ajustar posición vertical con zoom
                        pantalla.blit(img, (screen_x - (self.ancho_tile//2) + off_x, top_y - int(30*self.zoom)))
                    else: self.dibujar_recurso_fallback(pantalla, tile["recurso"], screen_x, top_y)
                
                if (col, fila) in self.edificios:
                    tipo_ed = self.edificios[(col, fila)]
                    if tipo_ed in self.imagenes_edificios:
                        img = self.imagenes_edificios[tipo_ed]
                        off_x = (self.ancho_tile - img.get_width()) // 2
                        pantalla.blit(img, (screen_x - (self.ancho_tile//2) + off_x, top_y - int(45*self.zoom)))
                    else: pygame.draw.rect(pantalla, (200, 50, 50), (screen_x-10, top_y-20, int(20*self.zoom), int(20*self.zoom)))

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
    def colocar_edificio(self, col, fila, tipo):
        if 0 <= col < COLUMNAS and 0 <= fila < FILAS:
            self.edificios[(col, fila)] = tipo
            self.mapa_logico[fila][col]["recurso"] = None

    # --- NUEVA FUNCIÓN DE DEPÓSITO (MANEJA COMIDA) ---
    def depositar_recursos(self, inventario_habitante):
        for tipo, cantidad in inventario_habitante.items():
            # Si es madera o piedra, se suma normal
            if tipo in self.recursos_totales:
                self.recursos_totales[tipo] += cantidad
            
            # Si es comida (animal, vegetal, fruta), se suma al total de "comida"
            elif tipo in ["animal", "vegetal", "fruta"]:
                self.recursos_totales["comida"] += cantidad
                
        # Vaciar inventario
        return {"madera": 0, "piedra": 0, "comida": 0, "animal":0, "vegetal":0, "fruta":0}

    def obtener_altura(self, col, fila):
        if 0 <= col < COLUMNAS and 0 <= fila < FILAS:
             return self.mapa_logico[int(fila)][int(col)]["altura"]
        return 0

    # --- PATHFINDING A* (Búsqueda de caminos) ---
    def heuristica(self, a, b):
        # Distancia Manhattan
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def obtener_camino(self, inicio, fin):
        """
        Devuelve una lista de tuplas [(c1, f1), (c2, f2)...] desde inicio hasta fin.
        Inicio y fin son tuplas (col, fila).
        Devuelve [] si no hay camino.
        """
        start_node = (int(inicio[0]), int(inicio[1]))
        end_node = (int(fin[0]), int(fin[1]))

        if not self.es_transitable(end_node[0], end_node[1]):
             # Si el destino es impasable, intentamos un vecino transitable
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
            
            if current == end_node:
                break
            
            vecinos = [(0, 1), (0, -1), (1, 0), (-1, 0)]
            for dx, dy in vecinos:
                next_node = (current[0] + dx, current[1] + dy)
                
                # Check límites y transitabilidad
                if 0 <= next_node[0] < COLUMNAS and 0 <= next_node[1] < FILAS:
                    if self.mapa_logico[next_node[1]][next_node[0]]["transitable"]:
                        new_cost = costo_acumulado[current] + 1
                        if next_node not in costo_acumulado or new_cost < costo_acumulado[next_node]:
                            costo_acumulado[next_node] = new_cost
                            prioridad = new_cost + self.heuristica(end_node, next_node)
                            heapq.heappush(frontera, (prioridad, next_node))
                            origenes[next_node] = current
                            
        # Reconstruir camino
        camino = []
        if end_node not in origenes:
            return [] # No se encontró camino
            
        curr = end_node
        while curr != start_node:
            camino.append(curr)
            curr = origenes[curr]
        camino.reverse()
        return camino

    # --- NUEVOS MÉTODOS PARA ANIMALES ---
    def obtener_animal_en_pos(self, col, fila, radio=1):
        for animal in self.animales:
             d = math.sqrt((animal.col - col)**2 + (animal.fila - fila)**2)
             if d < radio:
                 return animal
        return None

    def eliminar_animal(self, animal):
        if animal in self.animales:
            self.animales.remove(animal)