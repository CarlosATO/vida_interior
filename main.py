from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import os
import random
from mundo import Mundo
from habitante import Habitante
from config import *

app = FastAPI()

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Servir archivos estáticos (Frontend)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Servir Assets (Imágenes del juego) - Mapea /assets a la carpeta raíz/assets
app.mount("/assets", StaticFiles(directory="assets"), name="assets")

# Variable Global del Mundo
el_mundo = None
habitantes = []

def inicializar_mundo():
    global el_mundo, habitantes
    el_mundo = Mundo()
    habitantes = []
    
    # --- FUNDAR CIUDAD ---
    centro_c = COLUMNAS // 2
    centro_f = FILAS // 2
    
    # Buscar un lugar plano cerca del centro para la base
    print("Buscando lugar para el Centro Urbano...")
    base_x, base_y = centro_c, centro_f
    encontrado = False
    for radio in range(0, 10):
        for dc in range(-radio, radio+1):
            for df in range(-radio, radio+1):
                check_c, check_f = centro_c + dc, centro_f + df
                if 0 <= check_c < COLUMNAS and 0 <= check_f < FILAS:
                    tile = el_mundo.mapa_logico[check_f][check_c]
                    if tile["tipo"] != "agua" and tile["tipo"] != "piedra":
                        base_x, base_y = check_c, check_f
                        el_mundo.colocar_edificio(base_x, base_y, "centro")
                        encontrado = True
                        break
            if encontrado: break
        if encontrado: break
    
    # Crear habitantes ALREDEDOR de la base
    nombres = [("Emilia", "Femenino"), ("Sofia", "Femenino"), ("Mateo", "Masculino")]
    for nombre, genero in nombres:
        # Nacen al lado de la casa
        c = base_x + random.randint(-2, 2)
        f = base_y + random.randint(-2, 2)
        habitantes.append(Habitante(c, f, nombre, genero))

# Inicializar al arranque
inicializar_mundo()

# --- BUCLE DE SIMULACIÓN ---
async def bucle_simulacion():
    print("🚀 Iniciando simulación en background...")
    while True:
        try:
            # 1. TIEMPO & NATURALEZA
            nuevo_dia = el_mundo.actualizar_tiempo()
            el_mundo.actualizar_naturaleza()
            
            # 2. ANIMALES
            for animal in el_mundo.animales:
                animal.update(el_mundo)
                
            # 3. HABITANTES
            nuevos_habitantes = []
            for h in habitantes:
                h.ejecutar_ordenes(el_mundo, habitantes)
                
                # --- SALUD Y MUERTE ---
                if h.necesidades["hambre"] >= 100:
                    print(f"💀 {h.nombre} ha muerto de hambre.")
                    habitantes.remove(h)
                    continue
                    
                # --- NACIMIENTOS ---
                if h.accion_actual == "CORAZÓN":
                    # Spawheo de hijos (Simplificado para API)
                     if random.random() < 0.05:
                        print(f"👶 ¡Un bebé ha nacido! Familia de {h.nombre}")
                        bebe = Habitante(h.col, h.fila, f"Hijo de {h.nombre}", random.choice(["Masculino", "Femenino"]))
                        bebe.personalidad["sociable"] = h.personalidad["sociable"]
                        nuevos_habitantes.append(bebe)
                        h.accion_actual = "ESPERAR"
                        if h.pareja: h.pareja.accion_actual = "ESPERAR"
            
            habitantes.extend(nuevos_habitantes)
            
            # 10 TICK/s
            await asyncio.sleep(0.1) 
            
        except Exception as e:
            print(f"Error en loop sims: {e}")
            await asyncio.sleep(1)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(bucle_simulacion())

# --- API ENDPOINTS ---

@app.get("/estado")
async def get_estado():
    # Serializar Habitantes
    data_habitantes = []
    for h in habitantes:
        data_habitantes.append({
            "nombre": h.nombre,
            "x": h.col,
            "y": h.fila,
            "genero": h.genero,
            "color": h.color_cuerpo, # Hex string
            "accion": h.accion_actual,
            "mensaje": h.mensaje_actual if h.tiempo_bocadillo > 0 else None,
            "energia": h.necesidades["energia"]
        })
        
    # Serializar Animales
    data_animales = []
    for a in el_mundo.animales:
        data_animales.append({
            "x": a.col,
            "y": a.fila,
            "tipo": a.tipo
        })
        
    # Serializar Recursos y Mapa visible??
    # El mapa es muy grande para mandarlo cada frame (50x50 = 2500 tiles).
    # Mandaremos solo los cambios o mandamos todo si es pequeño.
    # Para fluidez en canvas, mandamos el mapa completo en otro endpoint "inicial" y solo updates aquí?
    # Por simplicidad ahora: No mandamos el mapa en /estado, solo entidades.
    # El frontend pedirá el mapa una vez al inicio.
    
    # Recursos dinámicos si cambian mucho... Por ahora el frontend asume el mapa estático + recursos
    # Mandamos lista de recursos actuales para dibujar
    data_recursos = []
    for f in range(FILAS):
        for c in range(COLUMNAS):
            tile = el_mundo.mapa_logico[f][c]
            if tile["recurso"]:
                data_recursos.append({
                    "c": c, "f": f, 
                    "tipo": tile["recurso"]
                })
    
    return {
        "tiempo": {
            "dia": el_mundo.dia,
            "mes": el_mundo.mes,
            "anio": el_mundo.anio,
            "hora_global": el_mundo.tiempo
        },
        "stats": {
            "poblacion": len(habitantes),
            "recursos": el_mundo.recursos_totales
        },
        "habitantes": data_habitantes,
        "animales": data_animales,
        "recursos_mapa": data_recursos
    }

@app.get("/mapa")
async def get_mapa():
    # Endpoint pesado, se llama una vez al cargar
    return {
        "filas": FILAS,
        "columnas": COLUMNAS,
        "mapa": el_mundo.mapa_logico, # JSON gigante con tipo, altura, color
        "edificios": [{"c": k[0], "f": k[1], "tipo": v} for k,v in el_mundo.edificios.items()]
    }

@app.get("/")
async def root():
    return {"message": "Vida Interior API Running. Go to /static/index.html"}