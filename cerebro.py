import random
import math

# --- CONOCIMIENTO UNIVERSAL (FÍSICA DEL MUNDO) ---
# Los habitantes NO nacen sabiendo esto. Deben descubrirlo.
RECETAS_UNIVERSALES = {
    # Nombre: {Inputs}, Output (implícito es 1 'Nombre')
    "Fuego": {"madera": 1, "piedra": 1},
    "Refugio": {"madera": 2, "piedra": 2},
    "Herramientas": {"madera": 1},
    "Rueda": {"madera": 2, "piedra": 1} # Ejemplo extra
}

class Accion:
    def __init__(self, nombre, costo=1.0):
        self.nombre = nombre
        self.costo = costo
        self.datos = None # Argumentos extra (ej: destino)

    def es_posible(self, cuerpo, mundo):
        return True

    def ejecutar_simulado(self, estado_simulado):
        # Modifica una copia del estado para el planner
        pass

class Cerebro:
    def __init__(self):
        self.plan_actual = [] # Lista de acciones pendientes
        self.centro_mapa = None 

    def percibir(self, cuerpo, mundo):
        # 1. Actualizar Memoria Visual
        radio_vision = 8
        c = int(round(cuerpo.col))
        f = int(round(cuerpo.fila))
        
        # Limpiamos memoria muy vieja o lejana? No por ahora.
        
        # Escaneamos tiles
        for dy in range(-radio_vision, radio_vision + 1):
            for dx in range(-radio_vision, radio_vision + 1):
                nx, ny = c + dx, f + dy
                # Solo guardar si hay algo interesante
                recurso = mundo.obtener_recurso(nx, ny)
                if recurso:
                    cuerpo.memoria[(nx, ny)] = recurso
                
                if (nx, ny) in mundo.edificios:
                    cuerpo.memoria[(nx, ny)] = f"edificio_{mundo.edificios[(nx, ny)]}"

        # Escanear Animales (snapshot)
        for animal in mundo.animales:
            d = math.sqrt((animal.col - cuerpo.col)**2 + (animal.fila - cuerpo.fila)**2)
            if d <= radio_vision:
                pos_int = (int(animal.col), int(animal.fila))
                cuerpo.memoria[pos_int] = f"animal_{animal.tipo}"

        # Setup centro
        if not self.centro_mapa:
            for pos, tipo in cuerpo.memoria.items():
                if tipo == "edificio_centro":
                    self.centro_mapa = pos
                    break

    def pensar(self, cuerpo, mundo, habitantes):
        self.percibir(cuerpo, mundo)
        
        # Si tenemos un plan en curso, seguimos (salvo emergencia)
        if self.plan_actual:
            # Chequear emergencias (Hambre crítica)
            if cuerpo.necesidades["hambre"] > 90 and self.plan_actual[0].nombre != "COMER":
                self.plan_actual = [] # Abortar plan
                # print(f"{cuerpo.nombre}: ¡Hambre crítica! Abortando plan.")
            else:
                accion = self.plan_actual.pop(0)
                # Validar que sigue siendo posible (ej: el recurso sigue ahí?)
                if accion.es_posible(cuerpo, mundo):
                    return accion.nombre, accion.datos
                else:
                    self.plan_actual = [] # Plan roto, replanificar

        # --- PLANIFICADOR GOAP ---
        # 1. Definir Objetivos (Prioridad descendente)
        objetivos = []
        
        # A. Supervivencia Inmediata
        if cuerpo.necesidades["hambre"] > 50:
            objetivos.append(("saciado", 10))
        if cuerpo.necesidades["sed"] > 50:
            objetivos.append(("hidratado", 10))
        if cuerpo.necesidades["energia"] < 20:
             objetivos.append(("descansado", 10))

        # DEBUG
        if random.random() < 0.05: print(f"🧠 {cuerpo.nombre}: {objetivos} -> {self.plan_actual}")
             
        # B. Comodidad / Mantenimiento
        if cuerpo.necesidades["energia"] < 60:
             objetivos.append(("descansado", 5))
             
        # C. Ambición / Curiosidad (Si estamos bien)
        if cuerpo.necesidades["hambre"] < 20 and cuerpo.necesidades["energia"] > 60:
            objetivos.append(("sabio", 2)) # Descubrir cosas
            objetivos.append(("rico", 1)) # Acumular recursos
            
        # D. Reproducción (La necesidad social y energía alta activan esto)
        if cuerpo.pareja and cuerpo.necesidades["social"] > 80 and cuerpo.necesidades["energia"] > 70:
            objetivos.append(("reproducirse", 15))

        # E. Crafting (Si tenemos recursos suficientes)
        if cuerpo.necesidades["hambre"] < 40:
             # Check recipes
             for nom, receta in RECETAS_UNIVERSALES.items():
                 posible = True
                 for ing, cant in receta.items():
                     if cuerpo.inventario.get(ing, 0) < cant:
                         posible = False
                         break
                 if posible:
                     objetivos.append(("craft", 8))
                     break

        # Default
        objetivos.append(("vivo", 1))

        # Ordenar por prioridad
        objetivos.sort(key=lambda x: x[1], reverse=True)

        # 2. Buscar plan para el objetivo más importante
        for objetivo, prioridad in objetivos:
            plan = self.construir_plan(cuerpo, mundo, objetivo)
            if plan:
                self.plan_actual = plan
                # Ejecutar primer paso de inmediato
                primera = self.plan_actual.pop(0)
                return primera.nombre, primera.datos
        
        return "ESPERAR", None

    def construir_plan(self, cuerpo, mundo, objetivo):
        # Un planner muy simple: Hardcoded strategies por ahora, 
        # para no complicar la búsqueda en grafos en este paso
        
        plan = []
        
        if objetivo == "hidratado":
             # Estrategia: Buscar elemento "agua" -> Ir -> Beber
             # Buscar en memoria
             pos_agua = self.buscar_recurso_cercano(cuerpo, ["agua"])
             
             if pos_agua:
                 dist = self.distancia(cuerpo, pos_agua)
                 if dist > 1.5:
                     acc_ir = Accion("CAMINAR")
                     acc_ir.datos = pos_agua
                     plan.append(acc_ir)
                     
                 acc_beber = Accion("BEBER")
                 acc_beber.datos = pos_agua
                 plan.append(acc_beber)
                 return plan
             else:
                 # Explorar para encontrar agua (ir hacia bordes/playa?)
                 acc_explorar = Accion("EXPLORAR")
                 # Asumir que agua suele estar en bordes o ríos
                 dx = random.randint(-15, 15)
                 dy = random.randint(-15, 15)
                 nx, ny = int(cuerpo.col + dx), int(cuerpo.fila + dy)
                 acc_explorar.datos = (nx, ny)
                 return [acc_explorar] 

        elif objetivo == "saciado":
            # Estrategia: Buscar comida -> Ir -> Comer
            pos_comida = self.buscar_recurso_cercano(cuerpo, ["fruta", "vegetal", "animal_gallina", "animal_cabra"])
            if pos_comida:
                dist = self.distancia(cuerpo, pos_comida)
                if dist > 1.5:
                    acc_ir = Accion("CAMINAR")
                    acc_ir.datos = pos_comida
                    plan.append(acc_ir)
                
                acc_comer = Accion("COMER")
                acc_comer.datos = pos_comida
                plan.append(acc_comer)
                return plan
            else:
                # Explorar para encontrar comida
                acc_explorar = Accion("EXPLORAR")
                # Generar punto random
                dx = random.randint(-10, 10)
                dy = random.randint(-10, 10)
                nx, ny = int(cuerpo.col + dx), int(cuerpo.fila + dy)
                if mundo.es_transitable(nx, ny):
                     acc_explorar.datos = (nx, ny)
                     return [acc_explorar]

        elif objetivo == "descansado":
            # Estrategia: Ir a casa (si hay) o dormir donde sea
            if self.centro_mapa:
                dist = self.distancia(cuerpo, self.centro_mapa)
                if dist > 3:
                     acc_ir = Accion("CAMINAR")
                     acc_ir.datos = self.centro_mapa
                     plan.append(acc_ir)
            acc_dormir = Accion("DORMIR")
            plan.append(acc_dormir)
            return plan

        elif objetivo == "sabio":
            # Estrategia: EXPERIMENTAR (Invención)
            # Requiere tener items para combinar
            total_items = sum(cuerpo.inventario.values())
            if total_items >= 2:
                acc_exp = Accion("EXPERIMENTAR")
                return [acc_exp]
            else:
                # Recolectar algo cualquiera para tener material
                return self.plan_recolectar_algo(cuerpo, mundo)

        elif objetivo == "rico":
             # Recolectar lo que sea
             return self.plan_recolectar_algo(cuerpo, mundo)

        elif objetivo == "vivo":
            # Si no hay nada urgente, hacemos algo util o paseamos
            if random.random() < 0.7:
                return self.plan_recolectar_algo(cuerpo, mundo) # Acumular recursos
            else:
                acc_explorar = Accion("EXPLORAR")
                # Generar punto random
                dx = random.randint(-8, 8)
                dy = random.randint(-8, 8)
                nx, ny = int(cuerpo.col + dx), int(cuerpo.fila + dy)
                acc_explorar.datos = (nx, ny)
                return [acc_explorar] 

        elif objetivo == "reproducirse":
            if cuerpo.pareja:
                dist = self.distancia(cuerpo, (cuerpo.pareja.col, cuerpo.pareja.fila))
                plan = []
                if dist > 2:
                     acc_ir = Accion("CAMINAR")
                     acc_ir.datos = (cuerpo.pareja.col, cuerpo.pareja.fila)
                     plan.append(acc_ir)
                
                acc_amor = Accion("REPRODUCIR")
                plan.append(acc_amor)
                return plan
        
        elif objetivo == "craft":
             for nom, receta in RECETAS_UNIVERSALES.items():
                 posible = True
                 for ing, cant in receta.items():
                     if cuerpo.inventario.get(ing, 0) < cant:
                         posible = False
                         break
                 if posible:
                     acc = Accion("CRAFT")
                     acc.datos = nom
                     return [acc] 

        return None

    def plan_recolectar_algo(self, cuerpo, mundo):
        # Buscar arbol o roca
        pos = self.buscar_recurso_cercano(cuerpo, ["arbol", "roca"])
        if pos:
            dist = self.distancia(cuerpo, pos)
            plan = []
            if dist > 1.5:
                acc_ir = Accion("CAMINAR")
                acc_ir.datos = pos
                plan.append(acc_ir)
            
            tipo_recurso = cuerpo.memoria.get(pos) # Puede estar "arbol" o "roca"
            acc_work = Accion("RECOLECTAR") # Antes TRABAJAR
            acc_work.datos = (pos[0], pos[1], tipo_recurso)
            plan.append(acc_work)
            return plan
        else:
             acc_explorar = Accion("EXPLORAR")
             dx = random.randint(-8, 8)
             dy = random.randint(-8, 8)
             acc_explorar.datos = (int(cuerpo.col + dx), int(cuerpo.fila + dy))
             return [acc_explorar] 

    def buscar_recurso_cercano(self, cuerpo, tipos):
        mejor_dist = 9999
        mejor_pos = None
        for pos, tipo in cuerpo.memoria.items():
            if tipo in tipos:
                d = self.distancia(cuerpo, pos)
                if d < mejor_dist:
                    mejor_dist = d
                    mejor_pos = pos
        return mejor_pos

    def distancia(self, cuerpo, pos):
        return math.sqrt((cuerpo.col - pos[0])**2 + (cuerpo.fila - pos[1])**2)