import random
import math

# --- CONOCIMIENTO UNIVERSAL (FÍSICA DEL MUNDO) ---
import config
from config import RECETAS_UNIVERSALES

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
                    self.actualizar_memoria(cuerpo, (nx, ny), recurso, mundo.tiempo)
                
                # Detectar AGUA
                tipo_tile = mundo.obtener_tipo(nx, ny)
                if tipo_tile == "agua":
                    self.actualizar_memoria(cuerpo, (nx, ny), "agua", mundo.tiempo)
                
                if (nx, ny) in mundo.edificios:
                    self.actualizar_memoria(cuerpo, (nx, ny), f"edificio_{mundo.edificios[(nx, ny)]}", mundo.tiempo)

        # Escanear Animales (snapshot)
        for animal in mundo.animales:
            d = math.sqrt((animal.col - cuerpo.col)**2 + (animal.fila - cuerpo.fila)**2)
            if d <= radio_vision:
                pos_int = (int(animal.col), int(animal.fila))
                self.actualizar_memoria(cuerpo, pos_int, f"animal_{animal.tipo}", mundo.tiempo)

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
                    # LOGGING DATA SCIENCE
                    self.registrar_decision(cuerpo, accion.nombre, "continuar_plan", mundo.tiempo)
                    return accion.nombre, accion.datos
                else:
                    self.plan_actual = [] # Plan roto, replanificar

        # --- PLANIFICADOR GOAP (JERARQUÍA DE MASLOW) ---
        # 1. Definir Objetivos (Prioridad estricta)
        objetivos = []
        razon_decision = "vida_normal"
        
        # NIVEL 1: FISIOLÓGICO (Supervivencia Inmediata)
        # Hambre
        if cuerpo.necesidades["hambre"] > 30:
            prio = 50 # Alta prioridad base
            if cuerpo.necesidades["hambre"] > 70: prio = 100 # PÁNICO
            
            # Si tengo comida en inventario, comer es la prioridad MÁXIMA
            if cuerpo.inventario.get("comida", 0) > 0:
                objetivos.append(("comer_inventario", 999))
                razon_decision = "hambre_inventario"
            else:
                objetivos.append(("saciado", prio))
                razon_decision = "hambre_busqueda"

        # Sed
        if cuerpo.necesidades["sed"] > 30:
            prio = 50
            if cuerpo.necesidades["sed"] > 70: prio = 100
            objetivos.append(("hidratado", prio))
            razon_decision = "sed"

        # NIVEL 2: SEGURIDAD (Refugio y Energía)
        if cuerpo.necesidades["energia"] < 30:
             # Si está muy cansado, dormir es crítico (riesgo de colapso)
             prio = 80
             objetivos.append(("descansado", prio))
             razon_decision = "cansancio_critico"
             
        # NIVEL 3: PERTENENCIA (Social)
        # Solo si las necesidades fisiológicas no son críticas
        if cuerpo.necesidades["hambre"] < 70 and cuerpo.necesidades["sed"] < 70:
            if cuerpo.necesidades["social"] < 60:
                objetivos.append(("socializar", 45))
                
            # Protección Familiar (Enseñar hijos)
            if len(cuerpo.hijos) > 0:
                for hijo in cuerpo.hijos:
                    if hijo in habitantes:
                        dist = math.sqrt((cuerpo.col - hijo.col)**2 + (cuerpo.fila - hijo.fila)**2)
                        if dist < 30 and len(hijo.conocimientos) < len(cuerpo.conocimientos):
                            objetivos.append(("enseñar_hijo", 15))
                            break

            # SOCIALIZAR (Nuevo)
            if cuerpo.necesidades["social"] < 60:
                # Buscar a alguien para hablar
                objetivos.append(("socializar", 45))


        # NIVEL 4: AUTORREALIZACIÓN & TRABAJO (Idle/Stockpile)
        # Si todo está "bajo control" (Hambre < 40, Energía > 40)
        if cuerpo.necesidades["hambre"] < 40 and cuerpo.necesidades["energia"] > 40:
            
            # A. ACUMULAR COMIDA (Instinto de Ardilla)
            current_food = cuerpo.inventario.get("comida", 0)
            if current_food < cuerpo.max_inventario:
                objetivos.append(("recolectar_comida", 10)) # Prioridad media
            
            # B. CRAFTING (Mejorar vida)
            # Solo si conozco recetas y tengo materiales
            for nom, receta in RECETAS_UNIVERSALES.items():
                 # Verificar si ya conoce la receta (sistema de conocimientos)
                 if nom not in cuerpo.conocimientos: continue
                 
                 posible = True
                 for ing, cant in receta.items():
                     if cuerpo.inventario.get(ing, 0) < cant:
                         posible = False
                         break
                 if posible:
                     objetivos.append(("craft", 8))
                     break
            
            # C. RECOLECTAR MATERIALES (Con propósito)
            # Solo si tengo inventario y sé para qué sirve
            if sum(cuerpo.inventario.values()) < cuerpo.max_inventario:
                # Si sé hacer fuego o casas, busco madera/piedra
                # O si soy MUY CURIOSO (> 1.2), recolecto para experimentar
                es_curioso = cuerpo.personalidad["curioso"] > 1.2
                sabe_usar_materiales = False
                
                # Check rápido si conoce alguna receta
                if len(cuerpo.conocimientos) > 0 or es_curioso:
                    sabe_usar_materiales = True
                
                if sabe_usar_materiales:
                    objetivos.append(("recolectar_materiales", 5))

            # D. Exploración
            objetivos.append(("explorar", 2))

        # NIVEL 5: TRASCENDENTAL (Imaginación)
        # Solo para habitantes con alta imaginación o que ya tienen necesidades muy cubiertas
        if cuerpo.imaginacion > 1.2 and cuerpo.necesidades["hambre"] < 30:
            # A. Crear Símbolo (Totem)
            if not self.buscar_estructura_cercana(cuerpo, ["edificio_totem"]):
                 # Si tiene suficientes recursos o "imagina" buscarlos
                 objetivos.append(("crear_totem", 15))
            
            # B. Peregrinaje (Visitar Totems de otros o propios)
            else:
                 objetivos.append(("peregrinaje", 10))

        # Default fallback
        objetivos.append(("vivo", 1))

        # Ordenar por prioridad descendente
        objetivos.sort(key=lambda x: x[1], reverse=True)

        # 2. Buscar plan
        for objetivo, prioridad in objetivos:
            plan = self.construir_plan(cuerpo, mundo, objetivo, habitantes)
            if plan:
                self.plan_actual = plan
                # Ejecutar primer paso
                primera = self.plan_actual.pop(0)
                # LOGGING DATA SCIENCE
                self.registrar_decision(cuerpo, primera.nombre, f"{objetivo}", mundo.tiempo)
                return primera.nombre, primera.datos
        
        # SI FALLA TODO (Crisis existencial):
        # Fallback de emergencia último recurso: DORMIR SUELO
        if cuerpo.necesidades["energia"] < 50:
             self.registrar_decision(cuerpo, "DORMIR_SUELO", "fallback_emergencia", mundo.tiempo)
             return "DORMIR_SUELO", None
        
        # O caminar random
        self.registrar_decision(cuerpo, "EXPLORAR", "aburrimiento_total", mundo.tiempo)
        
        # Generar coords validas para explorar
        acc_fallback = Accion("EXPLORAR")
        for _ in range(10):
            dx = random.randint(-5, 5)
            dy = random.randint(-5, 5)
            nx, ny = int(cuerpo.col + dx), int(cuerpo.fila + dy)
            if mundo.es_transitable(nx, ny):
                # Validar que no caiga fuera del mapa
                if 0 <= nx < mundo.config.COLUMNAS and 0 <= ny < mundo.config.FILAS:
                     return "EXPLORAR", (nx, ny)

        return "ESPERAR", None

    # --- HELPER METHODS (Monkey patch o Mixin idealmente, pero aquí directo) ---
    from cerebro_helpers import registrar_decision, buscar_agua_instinto
    registrar_decision = registrar_decision
    buscar_agua_instinto = buscar_agua_instinto

    def construir_plan(self, cuerpo, mundo, objetivo, habitantes):
        # Un planner muy simple: Hardcoded strategies
        plan = []
        
        # --- 1. SUPERVIVENCIA: COMIDA/AGUA ---
        if objetivo == "comer_inventario":
            acc_comer = Accion("COMER")
            acc_comer.datos = "INVENTARIO"
            return [acc_comer]

        elif objetivo == "hidratado":
             pos_agua = self.buscar_recurso_cercano(cuerpo, ["agua"], mundo)
             if pos_agua:
                 if self.distancia(cuerpo, pos_agua) > 1.5:
                     acc_ir = Accion("CAMINAR")
                     acc_ir.datos = pos_agua
                     plan.append(acc_ir)
                 acc_beber = Accion("BEBER")
                 acc_beber.datos = pos_agua
                 plan.append(acc_beber)
                 return plan
             else:
                 # Instinto de supervivencia (Omnisciencia si es crítico)
                 if cuerpo.necesidades["sed"] > 30:
                     pos = self.buscar_agua_instinto(cuerpo, mundo)
                     if pos:
                         self.actualizar_memoria(cuerpo, pos, "agua", mundo.tiempo)
                         acc_ir = Accion("CAMINAR")
                         acc_ir.datos = pos
                         return [acc_ir]
                 return self.estrategia_exploracion(cuerpo, mundo)

        elif objetivo == "saciado":
            # Buscar comida en el mundo (no tenemos en inventario)
            pos_comida = self.buscar_recurso_cercano(cuerpo, ["fruta", "vegetal", "animal_gallina"], mundo)
            if pos_comida:
                if self.distancia(cuerpo, pos_comida) > 1.5:
                    acc_ir = Accion("CAMINAR")
                    acc_ir.datos = pos_comida
                    plan.append(acc_ir)
                acc_comer = Accion("COMER")
                acc_comer.datos = pos_comida
                plan.append(acc_comer)
                return plan
            else:
                return self.estrategia_exploracion(cuerpo, mundo)

        elif objetivo == "recolectar_comida":
            pos_comida = self.buscar_recurso_cercano(cuerpo, ["fruta", "vegetal"], mundo)
            if pos_comida:
                if self.distancia(cuerpo, pos_comida) > 1.5:
                    acc_ir = Accion("CAMINAR")
                    acc_ir.datos = pos_comida
                    plan.append(acc_ir)
                
                tipo_comida = cuerpo.memoria.get(pos_comida, "comida")
                acc_rec = Accion("RECOLECTAR")
                acc_rec.datos = (pos_comida[0], pos_comida[1], tipo_comida)
                plan.append(acc_rec)
                return plan
            else:
                return self.estrategia_exploracion(cuerpo, mundo)

        # --- 2. SEGURIDAD: REFUGIO ---
        elif objetivo == "descansado":
            # Buscar CASA > Construir CASA > Dormir suelo
            pos_casa = self.buscar_estructura_cercana(cuerpo, ["edificio_casa", "edificio_centro"])
            if pos_casa:
                if self.distancia(cuerpo, pos_casa) > 1.5:
                     acc_ir = Accion("CAMINAR")
                     acc_ir.datos = pos_casa
                     return [acc_ir]
                else:
                     return [Accion("DORMIR")]
            else:
                # Fallback crítico: Dormir en el suelo
                return [Accion("DORMIR_SUELO")]

        # --- 3. RECURSOS Y TRABAJO ---
        elif objetivo == "recolectar_materiales":
             pos_rec = self.buscar_recurso_cercano(cuerpo, ["madera", "piedra"], mundo)
             if pos_rec:
                 if self.distancia(cuerpo, pos_rec) > 1.5:
                     acc_ir = Accion("CAMINAR")
                     acc_ir.datos = pos_rec
                     return [acc_ir]
                     
                 tipo_mat = cuerpo.memoria.get(pos_rec, "madera")
                 acc_rec = Accion("RECOLECTAR")
                 acc_rec.datos = (pos_rec[0], pos_rec[1], tipo_mat)
                 return [acc_rec]
             else:
                 return self.estrategia_exploracion(cuerpo, mundo)
        
        elif objetivo == "sabio":
            # Experimentar si tiene items
            if sum(cuerpo.inventario.values()) >= 2:
                return [Accion("EXPERIMENTAR")]
            return self.plan_recolectar_algo(cuerpo, mundo)

        elif objetivo == "rico" or objetivo == "vivo":
            if random.random() < 0.7:
                return self.plan_recolectar_algo(cuerpo, mundo)
            else:
                return self.estrategia_exploracion(cuerpo, mundo)

        # --- 4. SOCIEDAD Y FAMILIA ---
        elif objetivo == "reproducirse":
            if cuerpo.pareja:
                dist = self.distancia(cuerpo, (cuerpo.pareja.col, cuerpo.pareja.fila))
                plan = []
                if dist > 2:
                     acc_ir = Accion("CAMINAR")
                     acc_ir.datos = (cuerpo.pareja.col, cuerpo.pareja.fila)
                     plan.append(acc_ir)
                plan.append(Accion("REPRODUCIR"))
                return plan

        elif objetivo == "enseñar_hijo":
            hijo_cercano = None
            dist_minima = 999
            for hijo in cuerpo.hijos:
                if hijo in habitantes:
                    d = self.distancia(cuerpo, (hijo.col, hijo.fila))
                    if d < dist_minima and len(hijo.conocimientos) < len(cuerpo.conocimientos):
                        dist_minima = d
                        hijo_cercano = hijo
            if hijo_cercano:
                plan = []
                if dist_minima > 3:
                    acc_ir = Accion("CAMINAR")
                    acc_ir.datos = (int(hijo_cercano.col), int(hijo_cercano.fila))
                    plan.append(acc_ir)
                acc_ensenar = Accion("ENSEÑAR")
                acc_ensenar.datos = hijo_cercano
                plan.append(acc_ensenar)
                return plan

        elif objetivo == "socializar":
            # Buscar habitante más cercano
             mejor_dist = 999
             mejor_target = None
             for h in habitantes:
                 if h == cuerpo: continue
                 d = self.distancia(cuerpo, (h.col, h.fila))
                 if d < mejor_dist:
                     mejor_dist = d
                     mejor_target = h
             
             if mejor_target:
                 plan = []
                 if mejor_dist > 2.0:
                     acc_ir = Accion("CAMINAR")
                     acc_ir.datos = (mejor_target.col, mejor_target.fila) # Ir a su posición actual
                     plan.append(acc_ir)
                 
                 acc_soc = Accion("SOCIALIZAR")
                 acc_soc.datos = mejor_target
                 plan.append(acc_soc)
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

        # --- 5. TRASCENDENTAL: IMAGINACIÓN ---
        elif objetivo == "crear_totem":
             # Verificar si tiene recursos para tótem
             from config import COSTO_TOTEM
             tiene_todo = True
             for ing, cant in COSTO_TOTEM.items():
                 if cuerpo.inventario.get(ing, 0) < cant:
                     tiene_todo = False
                     break
             
             if tiene_todo:
                 return [Accion("CONSTRUIR_TOTEM")]
             else:
                 # Planificar recolectar lo que falta
                 return self.plan_recolectar_algo(cuerpo, mundo)

        elif objetivo == "peregrinaje":
             pos_totem = self.buscar_estructura_cercana(cuerpo, ["edificio_totem"])
             if pos_totem:
                 if self.distancia(cuerpo, pos_totem) > 2.0:
                     acc_ir = Accion("CAMINAR")
                     acc_ir.datos = pos_totem
                     return [acc_ir]
                 else:
                     return [Accion("MEDITAR")]

        return None

    def estrategia_exploracion(self, cuerpo, mundo):
        acc = Accion("EXPLORAR")
        # Estrategia 1: Aleatorio válido
        for _ in range(20):
            dx = random.randint(-10, 10)
            dy = random.randint(-10, 10)
            nx, ny = int(cuerpo.col + dx), int(cuerpo.fila + dy)
            if mundo.es_transitable(nx, ny):
                acc.datos = (nx, ny)
                return [acc]
        
        # Estrategia 2: Pánico (adyacente)
        for dy in range(-1, 2):
             for dx in range(-1, 2):
                 if dx==0 and dy==0: continue
                 nx, ny = int(cuerpo.col + dx), int(cuerpo.fila + dy)
                 if mundo.es_transitable(nx, ny):
                      acc.datos = (nx, ny)
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
             for _ in range(10):
                 dx = random.randint(-8, 8)
                 dy = random.randint(-8, 8)
                 nx, ny = int(cuerpo.col + dx), int(cuerpo.fila + dy)
                 if mundo.es_transitable(nx, ny):
                     acc_explorar.datos = (nx, ny)
                     return [acc_explorar]
             return None 

    def buscar_estructura_cercana(self, cuerpo, tipos):
        mejor_puntaje = -9999
        mejor_pos = None
        for pos, info in cuerpo.memoria.items():
            if info["tipo"] in tipos:
                d = self.distancia(cuerpo, pos)
                # Heurística: Preferir cercano y con alta confianza
                puntaje = info["confianza"] * 10 - d
                if puntaje > mejor_puntaje:
                    mejor_puntaje = puntaje
                    mejor_pos = pos
        return mejor_pos

    def buscar_recurso_cercano(self, cuerpo, tipos, mundo=None):
        mejor_puntaje = -9999
        mejor_pos = None
        
        # Centro del mapa (ficticio o real)
        cx, cy = config.COLUMNAS // 2, config.FILAS // 2
        es_tarde = mundo and mundo.tiempo > 0.6
        
        for pos, info in cuerpo.memoria.items():
            if info["tipo"] in tipos:
                d = self.distancia(cuerpo, pos)
                # Heurística base
                puntaje = info["confianza"] * 5 - d 
                
                # Bonus por cercanía al hogar si es tarde (Apego)
                if es_tarde:
                    dist_al_hogar = math.sqrt((pos[0] - cx)**2 + (pos[1] - cy)**2)
                    puntaje -= dist_al_hogar * 0.5 # Penalizar lo que está lejos del centro
                
                if puntaje > mejor_puntaje:
                    mejor_puntaje = puntaje
                    mejor_pos = pos
        return mejor_pos

    def actualizar_memoria(self, cuerpo, pos, tipo, tiempo):
        # Si ya lo conocía, reforzar confianza
        if pos in cuerpo.memoria:
            cuerpo.memoria[pos]["confianza"] = min(2.0, cuerpo.memoria[pos]["confianza"] + 0.1)
            cuerpo.memoria[pos]["fecha"] = tiempo
        else:
            cuerpo.memoria[pos] = {"tipo": tipo, "confianza": 1.0, "fecha": tiempo}

    def distancia(self, cuerpo, pos):
        return math.sqrt((cuerpo.col - pos[0])**2 + (cuerpo.fila - pos[1])**2)