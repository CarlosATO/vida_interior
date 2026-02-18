import os
import math
import random
from config import *
import config
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
        self.inventario = {"madera": 0, "piedra": 0, "comida": 0}
        self.max_inventario = 5 # Capacidad de carga
        
        # Estados
        self.accion_actual = "ESPERAR" 
        self.moviendose = False
        self.tiempo_trabajo = 0
        self.objetivo_trabajo = None 

        # --- CEREBRO & MENTE ---
        self.cerebro = Cerebro()
        # Memoria cualitativa: {(col, fila): {"tipo": "tipo_recurso", "confianza": 1.0, "fecha_descubrimiento": tick}}
        self.memoria = {} 
        
        # Necesidades (0 a 100)
        self.necesidades = {
            "hambre": 10,
            "sed": 5,
            "energia": 90,
            "social": 40,
            "diversion": 50
        }
        
        # --- HABILIDADES & EXPERIENCIA (NUEVO) ---
        self.habilidades = {
            "recoleccion": 1.0, # Multiplicador de velocidad (1.0 = normal)
            "caza": 1.0,
            "social": 1.0,
            "ingenio": 1.0
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
        
        # --- FAMILIA ---
        self.padre = None  # Referencia al padre
        self.madre = None  # Referencia a la madre
        self.hijos = []    # Lista de referencias a hijos
        self.edad = 0      # Edad en ticks (para madurez)

        # --- CONOCIMIENTO (NUEVO) ---
        self.conocimientos = []
        self.es_heroe = False
        self.tiempo_invencion = 0
        
        # Estado Visual (Bocadillos)
        self.tiempo_bocadillo = 0
        self.mensaje_actual = ""
        
        # --- DATA SCIENCE (Logs) ---
        self.historia_decisiones = [] # Lista de dicts {tick, necesidades, decision, razon}

    def ejecutar_ordenes(self, mundo, habitantes):
        # Incrementar edad
        self.edad += 1
        
        # 1. Si ya está ocupado...
        if self.moviendose:
            self.continuar_caminata()
            return
        
        if self.accion_actual == "TRABAJAR":
            self.continuar_trabajo(mundo)
            return

        # 2. Consultar al CEREBRO
        orden, datos = self.cerebro.pensar(self, mundo, habitantes)
        
        # Deterioro pasivo de necesidades (MAS LENTO para permitir vida)
        # Hambre: 0.012 * 60 ticks = 0.72 por segundo (Antes 1.2).
        self.necesidades["hambre"] += 0.012 * self.personalidad["gloton"]
        self.necesidades["sed"] += 0.010 # La sed sube un poco más lento que hambre
        self.necesidades["energia"] -= 0.01 * self.personalidad["trabajador"] 
        self.necesidades["social"] -= 0.01 * self.personalidad["sociable"]
        
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
                mundo.registrar_evento(f"💧 {self.nombre} bebió agua.", "info")
                self.mensaje_actual = "💧"
                self.tiempo_bocadillo = 60

        elif orden == "DORMIR":
            self.accion_actual = "DORMIR"
            self.necesidades["energia"] += 0.5
            if self.necesidades["energia"] >= 100:
                self.necesidades["energia"] = 100
                self.accion_actual = "ESPERAR" 

        elif orden == "DORMIR_SUELO":
            self.accion_actual = "DORMIR_SUELO"
            self.necesidades["energia"] += 0.3 # Recupera menos que en cama
            self.necesidades["social"] -= 0.1 # Es triste dormir en el suelo
            if self.necesidades["energia"] >= 90: # No descansa al 100%
                self.accion_actual = "ESPERAR"

        elif orden == "RECOLECTAR":
            # datos = (c, f, tipo)
            c, f, tipo = datos
            self.accion_actual = "TRABAJAR" 
            self.objetivo_trabajo = (c, f, tipo)
            
            # Tiempo base 60, reducido por habilidad recoleccion
            # Ej: nivel 2.0 -> 30 ticks
            self.tiempo_trabajo = max(10, int(60 / self.habilidades["recoleccion"])) 
            
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
                             mundo.registrar_evento(f"💡 ¡EUREKA! {self.nombre} descubrió: {receta}", "descubrimiento")
                             break
                             
        elif orden == "CAMINAR":
            self.accion_actual = "CAMINAR"
            destino_final = datos
            
            # --- NUEVO: COMPORTAMIENTO COMUNITARIO ---
            # Si es de noche ( > 0.8) y no estamos durmiendo, ir al CENTRO
            # Asumimos que el centro está cerca de config.COLUMNAS//2, config.FILAS//2
            if mundo.tiempo > 0.82 and self.accion_actual != "DORMIR" and self.accion_actual != "DORMIR_SUELO":
                # Ir al centro urbano
                cx, cy = config.COLUMNAS // 2, config.FILAS // 2
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
                                 self.interactuar(otro, mundo)
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
                    mundo.registrar_evento(f"👶 ¡Nació {nombre_hijo}! ({self.nombre} + {self.pareja.nombre})", "nacimiento")
                    
                    self.mensaje_actual = "❤️"
                    self.tiempo_bocadillo = 120
                    self.mensaje_actual = "❤️"
                    self.tiempo_bocadillo = 120
                    # Cooldown for reproduction? High energy cost acts as soft cooldown.
        
        elif orden == "SOCIALIZAR" or orden == "INTERACTUAR":
             target = datos
             if target and target in habitantes:
                 self.interactuar(target, mundo)
                 self.accion_actual = "SOCIALIZAR"
             else:
                 self.accion_actual = "ESPERAR"

        elif orden == "EXPLORAR":
            self.accion_actual = "EXPLORAR"
            destino_final = datos
            
            # Si no hay destino, buscamos uno random
            if not destino_final:
                # Intento simple de moverse
                destino_final = (self.col + random.randint(-5, 5), self.fila + random.randint(-5, 5))
            
            # Reutilizar lógica de caminata
            start = (int(round(self.col)), int(round(self.fila)))
            # Validar que sea transitable (si es random podria caer en agua)
            if not mundo.es_transitable(destino_final[0], destino_final[1]):
                 # Buscar vecino transitable
                 found = False
                 for dx in range(-1, 2):
                     for dy in range(-1, 2):
                         nx, ny = int(destino_final[0] + dx), int(destino_final[1] + dy)
                         if mundo.es_transitable(nx, ny):
                             destino_final = (nx, ny)
                             found = True
                             break
                     if found: break
            
            if start != destino_final and mundo.es_transitable(destino_final[0], destino_final[1]):
                ruta = mundo.obtener_camino(start, destino_final)
                if ruta:
                    self.camino = ruta
                    self.moviendose = True
                else:
                    self.accion_actual = "ESPERAR"
            else:
                 self.accion_actual = "ESPERAR"



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
                
                mundo.registrar_evento(f"🔨 {self.nombre} fabricó {receta_nombre}", "trabajo")
                self.mensaje_actual = "🔨"
                self.tiempo_bocadillo = 60

        elif orden == "CONSTRUIR":
            # datos = "TipoEdificio"
            tipo_edificio = datos if datos else "casa"
            # Colocar en el mundo
            mundo.colocar_edificio(int(self.col), int(self.fila), tipo_edificio.lower())
            
            # Actualizar memoria propia y de testigos cercanos?
            self.memoria[(int(self.col), int(self.fila))] = f"edificio_{tipo_edificio.lower()}"
            
            mundo.registrar_evento(f"🏠 {self.nombre} construyó {tipo_edificio}", "construccion")
            self.mensaje_actual = "🏠"
            self.tiempo_bocadillo = 120
        
        elif orden == "COMER":
            self.accion_actual = "COMER"
            if datos == "INVENTARIO":
                if self.inventario.get("comida", 0) > 0:
                    self.inventario["comida"] -= 1
                    self.necesidades["hambre"] = max(0, self.necesidades["hambre"] - 60)
                    self.necesidades["energia"] += 15
                    mundo.registrar_evento(f"{self.nombre}: Comió de su inventario.", "info")
                    self.mensaje_actual = "🍎"
                    self.tiempo_bocadillo = 60
                else:
                    self.accion_actual = "ESPERAR" # Fallo
            elif datos:
                c_com, f_com = datos
                recurso = mundo.obtener_recurso(c_com, f_com)
                animal = mundo.obtener_animal_en_pos(c_com, f_com, radio=1.5)
                
                if recurso in ["fruta", "vegetal"]:
                    mundo.eliminar_recurso(c_com, f_com)
                    self.necesidades["hambre"] = max(0, self.necesidades["hambre"] - 50)
                    self.necesidades["energia"] += 10
                    mundo.registrar_evento(f"{self.nombre}: Comí {recurso}.", "info")
                elif animal:
                    mundo.eliminar_animal(animal)
                    self.necesidades["hambre"] = max(0, self.necesidades["hambre"] - 80)
                    self.necesidades["energia"] += 20
                    mundo.registrar_evento(f"{self.nombre}: Cazó una {animal.tipo}.", "info")
                else:
                    # El recurso ya no está, limpiar memoria para no quedar atrapado
                    if (c_com, f_com) in self.memoria:
                        del self.memoria[(c_com, f_com)]
                    self.accion_actual = "ESPERAR"
        
        elif orden == "ENSEÑAR":
            self.accion_actual = "ENSEÑANDO"
            hijo = datos  # El hijo a quien enseñar
            
            if hijo and hijo in habitantes:
                dist = math.sqrt((self.col - hijo.col)**2 + (self.fila - hijo.fila)**2)
                
                if dist < 4:  # Están cerca
                    # Transferir conocimientos que el hijo no tiene
                    conocimientos_nuevos = [c for c in self.conocimientos if c not in hijo.conocimientos]
                    
                    if conocimientos_nuevos:
                        # Enseñar uno o dos conocimientos
                        ensenar = random.sample(conocimientos_nuevos, min(len(conocimientos_nuevos), 2))
                        for conocimiento in ensenar:
                            hijo.conocimientos.append(conocimiento)
                        
                        mundo.registrar_evento(
                            f"👨‍👧 {self.nombre} enseñó {', '.join(ensenar)} a su hijo/a {hijo.nombre}", 
                            "info"
                        )
                        
                        # Visuals
                        self.mensaje_actual = "📚"
                        self.tiempo_bocadillo = 60
                        hijo.mensaje_actual = "✨"
                        hijo.tiempo_bocadillo = 60
                        
                        # Beneficios: aumenta vínculo social para ambos
                        self.necesidades["social"] = min(100, self.necesidades["social"] + 20)
                        hijo.necesidades["social"] = min(100, hijo.necesidades["social"] + 20)
                        
                    self.accion_actual = "ESPERAR"

    def continuar_trabajo(self, mundo):
        if not self.objetivo_trabajo:
            self.accion_actual = "ESPERAR"
            return

        c, f, tipo = self.objetivo_trabajo
        
        # Verificar si el recurso sigue ahí
        if mundo.obtener_recurso(c, f) != tipo:
             if (c, f) in self.memoria:
                 del self.memoria[(c, f)]
             self.accion_actual = "ESPERAR"
             self.objetivo_trabajo = None
             return

        # Continuar trabajando
        self.necesidades["energia"] -= 0.5
        self.tiempo_trabajo -= 1
        
        if self.tiempo_trabajo <= 0:
            # MEJORAR HABILIDAD
            self.habilidades["recoleccion"] = min(5.0, self.habilidades["recoleccion"] + 0.05)
            
            # CHEQUEAR CAPACIDAD
            total_items = sum(self.inventario.values())
            if total_items >= self.max_inventario:
                mundo.registrar_evento(f"{self.nombre}: Inventario lleno, no pudo recoger.", "warning")
                self.accion_actual = "ESPERAR"
                self.objetivo_trabajo = None
                return

            mundo.eliminar_recurso(c, f)
            # Ganar item
            if tipo == "arbol": 
                self.inventario["madera"] += 1
                mundo.recursos_totales["madera"] += 1
            elif tipo == "roca": 
                self.inventario["piedra"] += 1
                mundo.recursos_totales["piedra"] += 1
            elif tipo in ["fruta", "vegetal"]:
                self.inventario["comida"] += 1
            
            # Limpiar memoria al terminar éxito
            if (c, f) in self.memoria:
                del self.memoria[(c, f)]
                
            mundo.registrar_evento(f"{self.nombre}: Recolectó {tipo}.", "trabajo")
            
            self.accion_actual = "ESPERAR"
            self.objetivo_trabajo = None

    def interactuar(self, otro, mundo):
        # Aumentar necesidad social
        self.necesidades["social"] = min(100, self.necesidades["social"] + 15)
        
        # MEJORAR HABILIDAD SOCIAL
        self.habilidades["social"] = min(5.0, self.habilidades["social"] + 0.02)

        # COMPARTIR MEMORIA (NUEVO)
        # Compartir el lugar más confiable que conozco
        if self.memoria:
            mejor_pos = max(self.memoria.items(), key=lambda x: x[1]["confianza"])
            pos, info = mejor_pos
            if info["confianza"] > 1.2:
                # El otro aprende este lugar
                otro.cerebro.actualizar_memoria(otro, pos, info["tipo"], mundo.tiempo)
        
        # Calcular compatibilidad si no existe
        if otro.nombre not in self.compatibilidad:
            diff = abs(self.personalidad["sociable"] - otro.personalidad["sociable"])
            self.compatibilidad[otro.nombre] = 100 - (diff * 50) 
            
        # --- LENGUAJE & ENSEÑANZA VIRAL ---
        # Si somos sociables, intentamos enseñar algo
        if random.random() < 0.5 * self.personalidad["sociable"]:
            self.hablar(otro, mundo)

        # Chance de enamorar
        comp = self.compatibilidad[otro.nombre]
        if self.pareja is None and otro.pareja is None:
            if comp > 80 and self.necesidades["social"] > 90:
                 if random.random() < 0.05:
                     self.pareja = otro
                     otro.pareja = self
                     mundo.registrar_evento(f"❤️ ¡{self.nombre} y {otro.nombre} son pareja!", "amor")

    def hablar(self, receptor, mundo):
        # Elegir qué contar (Prioridad: Tecnologías)
        if not self.conocimientos: return # Nada que decir
        
        tema = random.choice(self.conocimientos)
        
        # Intentar transmitir
        if tema not in receptor.conocimientos:
            # Receptor aprende!
            receptor.conocimientos.append(tema)
            mundo.registrar_evento(f"🗣️ {self.nombre} enseñó {tema} a {receptor.nombre}", "info")
            
            # Visuals (Datos para el frontend)
            self.tiempo_bocadillo = 60
            self.mensaje_actual = "💬"
            receptor.tiempo_bocadillo = 60
            receptor.mensaje_actual = "💡"
        else:
             # Ya lo sabía, chismear
             self.tiempo_bocadillo = 30
             self.mensaje_actual = "bla"

    def to_dict(self):
        # Convertir memoria (llaves tuplas a strings para JSON)
        memoria_json = {}
        for pos, info in self.memoria.items():
            key = f"{pos[0]},{pos[1]}"
            memoria_json[key] = info

        return {
            "nombre": self.nombre,
            "genero": self.genero,
            "col": self.col,
            "fila": self.fila,
            "destino_col": self.destino_col,
            "destino_fila": self.destino_fila,
            "inventario": self.inventario,
            "max_inventario": self.max_inventario,
            "necesidades": self.necesidades,
            "habilidades": self.habilidades,
            "personalidad": self.personalidad,
            "camino": self.camino,
            "accion_actual": self.accion_actual,
            "moviendose": self.moviendose,
            "tiempo_trabajo": self.tiempo_trabajo,
            "objetivo_trabajo": self.objetivo_trabajo,
            "memoria": memoria_json,
            "pareja_nombre": self.pareja.nombre if self.pareja else None,
            "hijos_nombres": [h.nombre for h in self.hijos],
            "padre_nombre": self.padre.nombre if self.padre else None,
            "madre_nombre": self.madre.nombre if self.madre else None,
            "edad": self.edad,
            "conocimientos": self.conocimientos,
            "es_heroe": self.es_heroe,
            "historia_decisiones": self.historia_decisiones
        }

    @classmethod
    def from_dict(cls, data):
        h = cls(data["col"], data["fila"], data["nombre"], data["genero"])
        h.destino_col = data.get("destino_col", h.col)
        h.destino_fila = data.get("destino_fila", h.fila)
        h.inventario = data.get("inventario", h.inventario)
        h.max_inventario = data.get("max_inventario", 5)
        h.necesidades = data.get("necesidades", h.necesidades)
        h.habilidades = data.get("habilidades", h.habilidades)
        h.personalidad = data.get("personalidad", h.personalidad)
        h.camino = data.get("camino", [])
        h.accion_actual = data.get("accion_actual", "ESPERAR")
        h.moviendose = data.get("moviendose", False)
        h.tiempo_trabajo = data.get("tiempo_trabajo", 0)
        h.objetivo_trabajo = data.get("objetivo_trabajo", None)
        h.edad = data.get("edad", 0)
        h.conocimientos = data.get("conocimientos", [])
        h.es_heroe = data.get("es_heroe", False)
        h.historia_decisiones = data.get("historia_decisiones", [])
        
        # Reconstruir memoria (strings a tuplas)
        mem_data = data.get("memoria", {})
        h.memoria = {}
        for k, v in mem_data.items():
            pos = tuple(map(int, k.split(',')))
            h.memoria[pos] = v
            
        # Nota: pareja/padres/hijos se vinculan en el nivel superior (Mundo)
        h._temp_data = data # Guardar para vinculación posterior
        return h

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
        
        # Velocidad base escalada levemente con "ingenio/experiencia"
        # Máximo +50% de velocidad
        bono_velocidad = (self.habilidades["ingenio"] - 1.0) * 0.1 
        velocidad = VELOCIDAD_BASE * (1.0 + min(0.5, bono_velocidad))
        
        if dist <= velocidad:
            # Llegamos al nodo
            self.col = float(target[0])
            self.fila = float(target[1])
            self.camino.pop(0) # Quitamos el nodo visitado
            # Moverse cuesta menos si eres hábil? No, consume energía igual.
            self.necesidades["energia"] -= 0.5
        else:
            # Nos movemos hacia el nodo
            self.col += (dx / dist) * velocidad
            self.fila += (dy / dist) * velocidad
            self.necesidades["energia"] -= 0.5