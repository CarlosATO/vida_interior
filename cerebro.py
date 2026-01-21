import random
import math

class Cerebro:
    def __init__(self):
        self.centro_mapa = None 
        # Pesos de personalidad base (se ajustarán con la personalidad del habitante)
        self.pesos = {
            "supervivencia": 2.0,
            "trabajo": 1.0,
            "exploracion": 0.5,
            "social": 0.8
        }

    def percibir(self, cuerpo, mundo):
        """
        Escanea el entorno y actualiza la memoria.
        """
        radio_vision = 8 # Bloques de visión
        c = int(round(cuerpo.col))
        f = int(round(cuerpo.fila))
        
        # Escaneamos un cuadrado alrededor
        for dy in range(-radio_vision, radio_vision + 1):
            for dx in range(-radio_vision, radio_vision + 1):
                nx, ny = c + dx, f + dy
                # Chequeamos límites (podríamos usar mundo.es_transitable pero queremos ver recursos)
                recurso = mundo.obtener_recurso(nx, ny)
                if recurso:
                    # Guardamos en memoria: "hay un arbol en (nx, ny)"
                    cuerpo.memoria[(nx, ny)] = recurso
                
                # También recordamos edificios
                if (nx, ny) in mundo.edificios:
                    tipo = mundo.edificios[(nx, ny)]
                    cuerpo.memoria[(nx, ny)] = f"edificio_{tipo}" # ej: edificio_centro

        # Escanear Animales (snapshot)
        for animal in mundo.animales:
            d = math.sqrt((animal.col - cuerpo.col)**2 + (animal.fila - cuerpo.fila)**2)
            if d <= radio_vision:
                # Guardamos la posicion aproximada
                pos_int = (int(animal.col), int(animal.fila))
                cuerpo.memoria[pos_int] = f"animal_{animal.tipo}"

        # Si vemos el centro, actualizamos nuestra referencia
        if not self.centro_mapa:
            for pos, tipo in cuerpo.memoria.items():
                if tipo == "edificio_centro":
                    self.centro_mapa = pos
                    break

    def pensar(self, cuerpo, mundo, habitantes):
        # 1. PERCEPCIÓN
        self.percibir(cuerpo, mundo)
        
        # 2. EVALUACIÓN DE UTILIDAD (Utility Scoring)
        mejor_accion = "ESPERAR"
        mejor_utilidad = -1
        datos_accion = None
        
        # --- OPCIÓN A: DORMIR (Supervivencia + Ciclo Circadiano) ---
        # Si la energía baja de cierto umbral, la utilidad dispara
        factor_energia = (100 - cuerpo.necesidades["energia"]) / 100.0
        utilidad_dormir = factor_energia * self.pesos["supervivencia"]
        
        # Factor Noche
        es_noche = mundo.tiempo > 0.82 or mundo.tiempo < 0.18
        dist_casa = self.distancia(cuerpo, self.centro_mapa) if self.centro_mapa else 0
        
        if es_noche:
            # Si es de noche, queremos dormir PERO solo si estamos en casa
            if dist_casa < 5:
                utilidad_dormir += 5.0 # ¡A dormir!
            else:
                utilidad_dormir = 0 # No duermas en el bosque
                
                # Crear deseo irresistible de ir a casa
                utilidad_ir_casa = 4.0 
                if utilidad_ir_casa > mejor_utilidad:
                    mejor_utilidad = utilidad_ir_casa
                    mejor_accion = "CAMINAR"
                    datos_accion = self.centro_mapa

        if cuerpo.necesidades["energia"] < 20: 
            utilidad_dormir *= 3.0 # Crítico: Prioridad absoluta
        
        # --- OPCIÓN ROMANCE: HACER BEBE (Prioridad sobre dormir si están felices) ---
        if cuerpo.pareja and es_noche:
             # Solo si están bien alimentados y felices
             if cuerpo.necesidades["hambre"] < 50 and cuerpo.necesidades["social"] > 80:
                 # Chequear si la pareja está cerca
                 dist_pareja = self.distancia(cuerpo, (cuerpo.pareja.col, cuerpo.pareja.fila))
                 if dist_pareja < 2:
                     utilidad_romance = 10.0 # ¡Es el momento!
                     # Pequeña chance para no hacerlo toda la noche
                     if random.random() < 0.1:
                         if utilidad_romance > mejor_utilidad:
                             mejor_utilidad = utilidad_romance
                             mejor_accion = "HACER_BEBE"
                             datos_accion = None
        
        if utilidad_dormir > mejor_utilidad:
            mejor_utilidad = utilidad_dormir
            mejor_accion = "DORMIR"
            datos_accion = None

        # --- OPCIÓN B: COMER (Supervivencia) ---
        utilidad_comer = (cuerpo.necesidades["hambre"] / 100.0) * self.pesos["supervivencia"] * 1.5
        # Bonus si es glotón
        utilidad_comer *= cuerpo.personalidad["gloton"]
        
        if utilidad_comer > mejor_utilidad:
            # Buscamos comida en memoria
            comida_pos = self.buscar_recurso_cercano(cuerpo, ["fruta", "vegetal", "animal_gallina", "animal_cabra"])
            
            if comida_pos:
                # Si estamos cerca, comemos. Si no, caminamos.
                dist = self.distancia(cuerpo, comida_pos)
                if dist < 1.5:
                    mejor_utilidad = utilidad_comer
                    mejor_accion = "COMER"
                    datos_accion = comida_pos
                else:
                    # La utilidad baja un poco por la distancia (costo)
                    utilidad_caminar_comida = utilidad_comer / (1 + dist * 0.1)
                    if utilidad_caminar_comida > mejor_utilidad:
                         mejor_utilidad = utilidad_caminar_comida
                         mejor_accion = "CAMINAR"
                         datos_accion = comida_pos
            else:
                 # Tenemos hambre pero no sabemos donde hay comida -> EXPLORAR
                 utilidad_explorar_hambre = utilidad_comer * 0.8
                 if utilidad_explorar_hambre > mejor_utilidad:
                     mejor_utilidad = utilidad_explorar_hambre
                     mejor_accion = "EXPLORAR" 

        # --- OPCIÓN C: DEPOSITAR (Logística) ---
        total_items = sum(cuerpo.inventario.values())
        capacidad_max = 10
        utilidad_depositar = (total_items / capacidad_max) * 2.0 # Prioridad muy alta si está lleno
        
        if utilidad_depositar > mejor_utilidad:
            target = self.centro_mapa if self.centro_mapa else (0,0) # Fallback
            dist = self.distancia(cuerpo, target)
            if dist < 2.0:
                mejor_utilidad = utilidad_depositar
                mejor_accion = "DEPOSITAR"
            else:
                utilidad_ir_deposito = utilidad_depositar
                if utilidad_ir_deposito > mejor_utilidad:
                    mejor_utilidad = utilidad_ir_deposito
                    mejor_accion = "CAMINAR"
                    datos_accion = target

        # --- OPCIÓN D: TRABAJAR (Productividad) ---
        # Solo trabajan si tienen energía y no mucha hambre
        deseo_trabajo = cuerpo.personalidad["trabajador"]
        # Estado fisico afecta ganas de trabajar (si estoy cansado o con hambre, no quiero)
        estado_fisico = (cuerpo.necesidades["energia"] / 100.0) * (1.0 - cuerpo.necesidades["hambre"]/100.0)
        
        utilidad_trabajo = deseo_trabajo * estado_fisico * self.pesos["trabajo"]
        
        if utilidad_trabajo > mejor_utilidad:
            # Buscar recursos para trabajar (Madera, Piedra)
            recurso_trabajo = self.buscar_recurso_cercano(cuerpo, ["arbol", "roca"])
            if recurso_trabajo:
                dist = self.distancia(cuerpo, recurso_trabajo)
                if dist < 1.5:
                    # Validar que SÍ exista el recurso (la memoria puede fallar)
                    tipo_real = mundo.obtener_recurso(recurso_trabajo[0], recurso_trabajo[1])
                    if tipo_real:
                        mejor_utilidad = utilidad_trabajo
                        mejor_accion = "TRABAJAR"
                        datos_accion = (recurso_trabajo[0], recurso_trabajo[1], tipo_real)
                    else:
                        # Falló la memoria, lo borramos y exploramos
                        del cuerpo.memoria[recurso_trabajo]
                        mejor_accion = "EXPLORAR"
                else:
                    mejor_utilidad = utilidad_trabajo
                    mejor_accion = "CAMINAR"
                    datos_accion = recurso_trabajo
            else:
                pass # Si no sé donde trabajar, quizás explorar gane por defecto

        # --- OPCIÓN F: SOCIALIZAR ---
        # Si se siente solo
        factor_soledad = (100 - cuerpo.necesidades["social"]) / 100.0
        utilidad_social = factor_soledad * self.pesos["social"]
        
        if utilidad_social > mejor_utilidad:
            # Buscar amigo cercano
            amigo = self.buscar_habitante_cercano(cuerpo, mundo, habitantes)
            if amigo:
                dist = self.distancia(cuerpo, (amigo.col, amigo.fila))
                if dist < 2:
                    mejor_utilidad = utilidad_social
                    mejor_accion = "SOCIALIZAR"
                    datos_accion = amigo
                else:
                    utilidad_caminar_amigo = utilidad_social * 0.8
                    if utilidad_caminar_amigo > mejor_utilidad:
                        mejor_utilidad = utilidad_caminar_amigo
                        mejor_accion = "CAMINAR"
                        datos_accion = (amigo.col, amigo.fila)

        # --- OPCIÓN E: EXPLORAR (Curiosidad/Ocio) ---
        # Base de aburrimiento
        utilidad_explorar = 0.3 * cuerpo.personalidad["curioso"]
        
        # Si la mejor utilidad hasta ahora es muy baja (estamos ociosos), explorar gana valor
        if mejor_utilidad < 0.4:
            utilidad_explorar += 0.2
            
        if utilidad_explorar > mejor_utilidad:
             mejor_utilidad = utilidad_explorar
             mejor_accion = "EXPLORAR"

        # --- EJECUCIÓN DE ACCIONES GENÉRICAS ---
        if mejor_accion == "EXPLORAR":
            # Elegir punto aleatorio transitable cercano
            for _ in range(5):
                dx = random.randint(-5, 5)
                dy = random.randint(-5, 5)
                nx, ny = int(cuerpo.col + dx), int(cuerpo.fila + dy)
                if mundo.es_transitable(nx, ny):
                    return "CAMINAR", (nx, ny)
            return "ESPERAR", None

        return mejor_accion, datos_accion

    def buscar_recurso_cercano(self, cuerpo, tipos_buscados):
        """Busca en la memoria el recurso más cercano de los tipos dados"""
        mejor_dist = 9999
        mejor_pos = None
        
        for pos, tipo in cuerpo.memoria.items():
            if tipo in tipos_buscados:
                d = self.distancia(cuerpo, pos)
                if d < mejor_dist:
                    mejor_dist = d
                    mejor_pos = pos
        return mejor_pos

    def buscar_habitante_cercano(self, cuerpo, mundo, habitantes):
        mejor_dist = 999
        amigo = None
        
        for h in habitantes:
            if h is cuerpo: continue # No interactuar con uno mismo
            
            dist = self.distancia(cuerpo, (h.col, h.fila))
            if dist < mejor_dist and dist < 10: # Radio visión
                mejor_dist = dist
                amigo = h
                
        return amigo

    def distancia(self, cuerpo, pos):
        return math.sqrt((cuerpo.col - pos[0])**2 + (cuerpo.fila - pos[1])**2)