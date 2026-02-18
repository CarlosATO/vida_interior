from mundo import Mundo
from habitante import Habitante
from cerebro import Cerebro
import config
import traceback
import random

config.COLUMNAS = 20
config.FILAS = 20

def test_explorar_execution():
    print("--- Test 1: Habitante executes EXPLORAR order ---")
    m = Mundo()
    
    # Find a valid spot (center of map usually has land)
    valid_pos = (10, 10)
    for pos, tipo in m.edificios.items():
        if tipo == "centro":
            valid_pos = pos
            break
            
    # Ensure it's transitable
    if not m.mapa_logico[valid_pos[1]][valid_pos[0]]["transitable"]:
        print(f"Forcing transitable at {valid_pos}")
        m.mapa_logico[valid_pos[1]][valid_pos[0]]["transitable"] = True
    
    print(f"Spawning at {valid_pos}")
    h = Habitante(valid_pos[0], valid_pos[1], "Tester", "Masculino")
    
    # Mock brain to force EXPLORAR to a neighbor
    # Find a valid neighbor
    target = None
    for dx in range(-3, 4):
        for dy in range(-3, 4):
             if dx==0 and dy==0: continue
             nx, ny = valid_pos[0]+dx, valid_pos[1]+dy
             if 0 <= nx < config.COLUMNAS and 0 <= ny < config.FILAS:
                 if m.mapa_logico[ny][nx]["transitable"]:
                     target = (nx, ny)
                     break
        if target: break
        
    if not target:
        print("Could not find valid target neighbor, forcing one.")
        target = (valid_pos[0] + 1, valid_pos[1])
        if target[0] < config.COLUMNAS:
             m.mapa_logico[target[1]][target[0]]["transitable"] = True
    
    print(f"Going to {target}")

    def mock_pensar(cuerpo, mundo, habitantes):
        return "EXPLORAR", target
    
    h.cerebro.pensar = mock_pensar
    
    h.ejecutar_ordenes(m, [])
    
    print(f"Action: {h.accion_actual}")
    print(f"Moving: {h.moviendose}")
    print(f"Path: {h.camino}")
    
    if h.accion_actual == "EXPLORAR" and h.moviendose and len(h.camino) > 0:
        print("✅ PASS: Habitante accepted EXPLORAR order and calculated path.")
    else:
        print("❌ FAIL: Habitante did not execute EXPLORAR order.")

def test_cerebro_fallback():
    print("\n--- Test 2: Cerebro fallback returns valid coordinates ---")
    c = Cerebro()
    m = Mundo()
    
    # Find valid spawn
    valid_pos = (10, 10)
    for pos, tipo in m.edificios.items():
        if tipo == "centro":
            valid_pos = pos
            break
            
    h = Habitante(valid_pos[0], valid_pos[1], "Tester", "Masculino")
    
    # Zero needs but full energy/social to avoid other goals
    h.necesidades = {k: 0 for k in h.necesidades}
    h.necesidades["energia"] = 100 
    h.necesidades["social"] = 100 
    h.inventario = {} 
    h.conocimientos = []
    
    try:
        orden, datos = c.pensar(h, m, [])
        print(f"Orden: {orden}, Datos: {datos}")
        
        if orden == "EXPLORAR" and datos is not None and isinstance(datos, tuple):
             print("✅ PASS: Cerebro returned valid coordinates for EXPLORAR.")
        elif orden == "ESPERAR":
             print("⚠️ WARNING: Returned ESPERAR.")
        else:
             print(f"❌ FAIL: Returned {orden} with {datos}")
    except Exception:
        traceback.print_exc()

if __name__ == "__main__":
    try:
        test_explorar_execution()
        test_cerebro_fallback()
    except Exception:
        traceback.print_exc()
