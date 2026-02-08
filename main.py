from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import asyncio
import os
import random
from mundo import Mundo
from habitante import Habitante
from config import *

# App se define abajo con lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Iniciar mundo y loop
    inicializar_mundo()
    task = asyncio.create_task(bucle_simulacion())
    yield
    # Shutdown (si fuera necesario cancelar task)
    task.cancel()

app = FastAPI(lifespan=lifespan)

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
poblacion_historia = []  # Lista de (tiempo, poblacion)

# Banco de nombres para bebés
NOMBRES_MASCULINOS = ["Leo", "Liam", "Noah", "Oliver", "Elias", "Theo", "Max", "Felix", "Oscar", "Hugo", 
                      "Gabriel", "Rafael", "Daniel", "Samuel", "David", "Miguel", "Adrian", "Bruno", "Aaron"]
NOMBRES_FEMENINOS = ["Valentina", "Camila", "Lucia", "Martina", "Victoria", "Emma", "Olivia", "Ava", "Zoe",
                     "Helena", "Julia", "Catalina", "Natalia", "Andrea", "Sara", "Elena", "Paula", "Laura"]
nombres_usados = set()

def inicializar_mundo():
    global el_mundo, habitantes, poblacion_historia, nombres_usados
    el_mundo = Mundo()
    habitantes = []
    poblacion_historia = []
    nombres_usados = set()  # Resetear nombres usados
    
    # --- SPAWN HABITANTES ---
    # Usar la ubicación del Centro Urbano determinada por el generador de Mundo
    base_x, base_y = COLUMNAS // 2, FILAS // 2 # Default fallback
    
    # Buscar el edificio centro
    for pos, tipo in el_mundo.edificios.items():
        if tipo == "centro":
            base_x, base_y = pos
            break
            
    # Crear habitantes ALREDEDOR de la base - 10 habitantes con personalidades variadas
    nombres = [
        # Mujeres
        ("Emma", "Femenino"),
        ("Sofia", "Femenino"),
        ("Isabella", "Femenino"),
        ("Mia", "Femenino"),
        ("Luna", "Femenino"),
        # Hombres
        ("Mateo", "Masculino"),
        ("Lucas", "Masculino"),
        ("Diego", "Masculino"),
        ("Santiago", "Masculino"),
        ("Sebastian", "Masculino")
    ]
    
    for nombre, genero in nombres:
        # Nacen al lado de la casa con distribución más amplia
        c = base_x + random.randint(-4, 4)
        f = base_y + random.randint(-4, 4)
        # Asegurar que caigan en tierra
        if el_mundo.es_transitable(c, f):
            hab = Habitante(c, f, nombre, genero)
        else:
            hab = Habitante(base_x, base_y, nombre, genero)
        
        # Personalidades variadas para cada habitante
        if nombre == "Emma":
            # Muy social y curiosa
            hab.personalidad["sociable"] = 1.5
            hab.personalidad["curioso"] = 1.4
            hab.personalidad["trabajador"] = 0.9
            hab.personalidad["gloton"] = 0.8
        elif nombre == "Sofia":
            # Trabajadora incansable
            hab.personalidad["trabajador"] = 1.6
            hab.personalidad["gloton"] = 1.2
            hab.personalidad["sociable"] = 0.7
            hab.personalidad["curioso"] = 0.9
        elif nombre == "Isabella":
            # Exploradora curiosa
            hab.personalidad["curioso"] = 1.7
            hab.personalidad["trabajador"] = 1.1
            hab.personalidad["sociable"] = 1.0
            hab.personalidad["gloton"] = 0.7
        elif nombre == "Mia":
            # Equilibrada
            hab.personalidad["sociable"] = 1.0
            hab.personalidad["trabajador"] = 1.0
            hab.personalidad["curioso"] = 1.0
            hab.personalidad["gloton"] = 1.0
        elif nombre == "Luna":
            # Introvertida y reflexiva
            hab.personalidad["sociable"] = 0.6
            hab.personalidad["curioso"] = 1.3
            hab.personalidad["trabajador"] = 0.8
            hab.personalidad["gloton"] = 0.9
        elif nombre == "Mateo":
            # Líder nato, sociable y trabajador
            hab.personalidad["sociable"] = 1.4
            hab.personalidad["trabajador"] = 1.3
            hab.personalidad["curioso"] = 1.1
            hab.personalidad["gloton"] = 0.9
        elif nombre == "Lucas":
            # Innovador curioso
            hab.personalidad["curioso"] = 1.8
            hab.personalidad["trabajador"] = 1.2
            hab.personalidad["sociable"] = 0.9
            hab.personalidad["gloton"] = 0.8
        elif nombre == "Diego":
            # Superviviente pragmático
            hab.personalidad["gloton"] = 1.5
            hab.personalidad["trabajador"] = 1.4
            hab.personalidad["sociable"] = 0.8
            hab.personalidad["curioso"] = 0.7
        elif nombre == "Santiago":
            # Carismático social
            hab.personalidad["sociable"] = 1.7
            hab.personalidad["curioso"] = 1.2
            hab.personalidad["trabajador"] = 0.8
            hab.personalidad["gloton"] = 0.9
        elif nombre == "Sebastian":
            # Solitario eficiente
            hab.personalidad["trabajador"] = 1.5
            hab.personalidad["sociable"] = 0.6
            hab.personalidad["curioso"] = 1.0
            hab.personalidad["gloton"] = 1.1
        
        habitantes.append(hab)
        nombres_usados.add(nombre)  # Registrar nombre usado

# Inicializar al arranque
inicializar_mundo()



# --- BUCLE DE SIMULACIÓN ---
async def bucle_simulacion():
    print("🚀 Iniciando simulación en background...")
    while True:
        try:
            # 1. TIEMPO & NATURALEZA
            if el_mundo:
                nuevo_dia = el_mundo.actualizar_tiempo()
                el_mundo.actualizar_naturaleza()
                
                # Registrar población histórica
                if len(poblacion_historia) == 0 or el_mundo.tiempo - poblacion_historia[-1][0] >= 0.01:
                    poblacion_historia.append((round(el_mundo.tiempo, 2), len(habitantes)))
                    if len(poblacion_historia) > 1000:
                        poblacion_historia.pop(0)
                
                # 2. ANIMALES
                for animal in el_mundo.animales:
                    animal.update(el_mundo)
                    
                # 3. HABITANTES
                nuevos_habitantes = []
                for h in habitantes:
                    h.ejecutar_ordenes(el_mundo, habitantes)
                    
                    # --- SALUD Y MUERTE ---
                    if h.necesidades["hambre"] >= 100:
                        el_mundo.registrar_evento(f"💀 {h.nombre} murió de hambre.", "muerte")
                        habitantes.remove(h)
                        continue
                    
                    if h.necesidades["sed"] >= 100:
                        el_mundo.registrar_evento(f"💀 {h.nombre} murió de sed.", "muerte")
                        habitantes.remove(h)
                        continue
                        
                    # --- NACIMIENTOS ---
                    if h.accion_actual == "CORAZÓN":
                         if random.random() < 0.05:
                            # Determinar género del bebé
                            genero_bebe = random.choice(["Masculino", "Femenino"])
                            
                            # Seleccionar nombre único
                            banco = NOMBRES_MASCULINOS if genero_bebe == "Masculino" else NOMBRES_FEMENINOS
                            nombres_disponibles = [n for n in banco if n not in nombres_usados]
                            
                            if len(nombres_disponibles) == 0:
                                # Generar nombre con sufijo si se agotaron nombres
                                nombre_bebe = f"{'Hijo' if genero_bebe == 'Masculino' else 'Hija'}{len(habitantes)}"
                            else:
                                nombre_bebe = random.choice(nombres_disponibles)
                                nombres_usados.add(nombre_bebe)
                            
                            # Crear bebé con herencia genética
                            bebe = Habitante(h.col, h.fila, nombre_bebe, genero_bebe)
                            
                            # Establecer relaciones familiares
                            if h.genero == "Femenino":
                                bebe.madre = h
                                bebe.padre = h.pareja if h.pareja else None
                            else:
                                bebe.padre = h
                                bebe.madre = h.pareja if h.pareja else None
                            
                            # Agregar hijo a los padres
                            h.hijos.append(bebe)
                            if h.pareja:
                                h.pareja.hijos.append(bebe)
                            
                            # Herencia genética: promedio de ambos padres con mutación
                            if h.pareja:
                                for trait in bebe.personalidad.keys():
                                    herencia = (h.personalidad[trait] + h.pareja.personalidad[trait]) / 2
                                    mutacion = random.uniform(-0.1, 0.1)
                                    bebe.personalidad[trait] = max(0.5, min(2.0, herencia + mutacion))
                            else:
                                # Solo un padre: heredar con más mutación
                                for trait in bebe.personalidad.keys():
                                    herencia = h.personalidad[trait]
                                    mutacion = random.uniform(-0.2, 0.2)
                                    bebe.personalidad[trait] = max(0.5, min(2.0, herencia + mutacion))
                            
                            # Heredar conocimientos de los padres (transferencia cultural)
                            if h.conocimientos:
                                # Bebé aprende algunos conocimientos de los padres
                                conocimientos_heredados = random.sample(h.conocimientos, min(len(h.conocimientos), 2))
                                bebe.conocimientos.extend(conocimientos_heredados)
                            
                            if h.pareja and h.pareja.conocimientos:
                                conocimientos_pareja = random.sample(h.pareja.conocimientos, min(len(h.pareja.conocimientos), 2))
                                bebe.conocimientos.extend([c for c in conocimientos_pareja if c not in bebe.conocimientos])
                            
                            nuevos_habitantes.append(bebe)
                            el_mundo.registrar_evento(f"👶 ¡{nombre_bebe} ha nacido! Padres: {h.nombre} y {h.pareja.nombre if h.pareja else 'desconocido'}", "nacimiento")
                            print(f"👶 ¡{nombre_bebe} ({genero_bebe}) ha nacido! Familia de {h.nombre}")
                            
                            h.accion_actual = "ESPERAR"
                            if h.pareja: 
                                h.pareja.accion_actual = "ESPERAR"
                
                habitantes.extend(nuevos_habitantes)
            
            # 10 TICK/s
            await asyncio.sleep(0.1) 
            
        except Exception as e:
            print(f"Error en loop sims: {e}")
            await asyncio.sleep(1)



# Configurar CORS

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
    
@app.get("/bitacora")
async def get_bitacora():
    return el_mundo.bitacora

@app.get("/analisis")
async def analisis_dashboard():
    return FileResponse("static/analisis.html")

@app.get("/api/analisis")
async def get_analisis():
    # Consolidar datos de todos los habitantes vivos
    data = []
    for h in habitantes:
        # Añadir metadatos del habitante a cada registro
        for record in h.historia_decisiones:
            r = record.copy()
            r["nombre"] = h.nombre
            r["genero"] = h.genero
            data.append(r)
    return data

@app.get("/api/estadisticas")
async def get_estadisticas():
    # Estadísticas agregadas
    total_decisiones = 0
    decisiones_por_tipo = {}
    muertes_por_causa = {"hambre": 0, "sed": 0}
    necesidades_promedio = {"hambre": 0, "sed": 0, "energia": 0, "social": 0}
    habitantes_vivos = len(habitantes)
    
    # Procesar bitácora para muertes
    for evento in el_mundo.bitacora:
        if "murió de hambre" in evento["mensaje"]:
            muertes_por_causa["hambre"] += 1
        elif "murió de sed" in evento["mensaje"]:
            muertes_por_causa["sed"] += 1
    
    # Procesar decisiones
    for h in habitantes:
        total_decisiones += len(h.historia_decisiones)
        for record in h.historia_decisiones:
            tipo = record["decision"]
            decisiones_por_tipo[tipo] = decisiones_por_tipo.get(tipo, 0) + 1
            for nec in necesidades_promedio:
                necesidades_promedio[nec] += record.get(nec, 0)
    
    # Promedios
    if total_decisiones > 0:
        for nec in necesidades_promedio:
            necesidades_promedio[nec] /= total_decisiones
    
    # Evolución poblacional
    evolucion_poblacion = poblacion_historia
    
    # Agrupaciones: Clusters simples por proximidad
    grupos = []
    visitados = set()
    for h in habitantes:
        if h.nombre in visitados: continue
        grupo = [h.nombre]
        visitados.add(h.nombre)
        for otro in habitantes:
            if otro.nombre not in visitados:
                dist = ((h.col - otro.col)**2 + (h.fila - otro.fila)**2)**0.5
                if dist < 5:  # Radio de agrupación
                    grupo.append(otro.nombre)
                    visitados.add(otro.nombre)
        if len(grupo) > 1:
            grupos.append(grupo)
    
    # Delitos: Decisiones negativas (ej. esperar por inactividad, o si hambre alta y no come)
    delitos = []
    for h in habitantes:
        for record in h.historia_decisiones[-10:]:  # Últimas 10
            if record["decision"] == "ESPERAR" and record["hambre"] > 80:
                delitos.append({"habitante": h.nombre, "delito": "Inactividad con hambre alta", "tiempo": record["t"]})
    
    return {
        "habitantes_vivos": habitantes_vivos,
        "total_decisiones": total_decisiones,
        "decisiones_por_tipo": decisiones_por_tipo,
        "muertes_por_causa": muertes_por_causa,
        "necesidades_promedio": necesidades_promedio,
        "evolucion_poblacion": evolucion_poblacion,
        "agrupaciones": grupos,
        "delitos": delitos,
        "tiempo_actual": el_mundo.tiempo
    }

@app.get("/api/exportar_datos")
async def exportar_datos():
    # Exportar todo el dataset para análisis offline
    data = []
    for h in habitantes:
        for record in h.historia_decisiones:
            r = record.copy()
            r["habitante"] = h.nombre
            data.append(r)
    return {"data": data, "bitacora": el_mundo.bitacora, "poblacion_historia": poblacion_historia}

@app.get("/mapa")
async def get_mapa():
    # Endpoint pesado, se llama una vez al cargar
    return {
        "filas": FILAS,
        "columnas": COLUMNAS,
        "mapa": el_mundo.mapa_logico,
        "edificios": [{"c": k[0], "f": k[1], "tipo": v} for k,v in el_mundo.edificios.items()]
    }

@app.post("/reiniciar")
async def reiniciar():
    print("🔁 Reiniciando mundo...")
    inicializar_mundo()
    return {"mensaje": "Mundo reiniciado correctamente con 10 habitantes"}

@app.get("/")
async def root():
    return FileResponse("static/index.html")
if __name__ == "__main__":
    import uvicorn
    # Hot reload para desarrollo local
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
