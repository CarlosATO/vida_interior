import config

def registrar_decision(self, cuerpo, decision, razon, tiempo):
    # Guardar snapshot para análisis
    snapshot = {
        "t": round(tiempo, 4),
        "hambre": round(cuerpo.necesidades["hambre"], 1),
        "sed": round(cuerpo.necesidades["sed"], 1),
        "energia": round(cuerpo.necesidades["energia"], 1),
        "social": round(cuerpo.necesidades["social"], 1),
        "diversion": round(cuerpo.necesidades["diversion"], 1),
        "decision": decision,
        "razon": razon,
        "pos": (round(cuerpo.col), round(cuerpo.fila)),
        "inventario": cuerpo.inventario.copy(),
        "personalidad": cuerpo.personalidad.copy(),
        "accion_actual": cuerpo.accion_actual,
        "es_heroe": cuerpo.es_heroe,
        "pareja": cuerpo.pareja.nombre if cuerpo.pareja else None
    }
    # Limitar historial en memoria RAM (últimos 1000 items)
    cuerpo.historia_decisiones.append(snapshot)
    if len(cuerpo.historia_decisiones) > 1000:
        cuerpo.historia_decisiones.pop(0)

def buscar_agua_instinto(self, cuerpo, mundo):
    # Busca el tile de agua más cercano en TODO el mapa (Costoso pero salva vidas)
    # Optimización: Buscar en espiral o por distancia
    # Por simplicidad: Scan completo pero con early exit si encuentra algo muy cerca
    
    mejor_dist = 9999
    mejor_pos = None
    
    # Búsqueda aleatoria optimizada (Monte Carlo)
    # En vez de recorrer 6400 tiles, probamos 100 puntos al azar, o scaneamos radios
    
    # Método 1: Fuerza bruta (seguro)
    # Nota: Acceder a mapa_logico es "trampa" (instinto)
    centro_x, centro_y = int(cuerpo.col), int(cuerpo.fila)
    radio_busqueda = 40 # Expandir si es necesario
    
    for r in range(1, radio_busqueda, 2): # Anillos
        for dx in range(-r, r+1):
            for dy in range(-r, r+1):
                # Solo borde del anillo
                if abs(dx) != r and abs(dy) != r: continue
                
                nx, ny = centro_x + dx, centro_y + dy
                if 0 <= nx < config.COLUMNAS and 0 <= ny < config.FILAS: # Usar límites de config
                    if mundo.mapa_logico[ny][nx]["tipo"] == "agua":
                        return (nx, ny)
    return None
