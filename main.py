import pygame
import sys
import random
import json
import os
from config import *
from habitante import Habitante
from mundo import Mundo

# --- CONFIGURACIÓN HEADLESS (RAILWAY) ---
HEADLESS = os.environ.get('RAILWAY_ENVIRONMENT') or os.environ.get('HEADLESS')

if HEADLESS:
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    print("🖥️ MODO HEADLESS ACTIVADO: Sin ventana gráfica.")
else:
    print("🖥️ MODO GRÁFICO ACTIVADO: Ventana normal.")

pygame.init()

if HEADLESS:
    # En modo headless, set_mode funciona con driver dummy para dar contexto a convert_alpha
    pantalla = pygame.display.set_mode((ANCHO_PANTALLA, ALTO_PANTALLA))
else:
    pantalla = pygame.display.set_mode((ANCHO_PANTALLA, ALTO_PANTALLA))
    pygame.display.set_caption("Ciudad Isométrica - GIGANTE")

reloj = pygame.time.Clock()

def guardar_historia(mundo, habitantes):
    archivo = "historia_mundo.json"
    
    # Calcular stats
    # Tecnologías: Set de todos los conocimientos únicos
    techs_totales = set()
    h_felicidad_total = 0
    heroes = []
    
    for h in habitantes:
        techs_totales.update(h.conocimientos)
        h_felicidad_total += h.necesidades["diversion"] # Usamos diversión como proxy a felicidad
        if h.es_heroe:
            heroes.append({"nombre": h.nombre, "inventos": h.conocimientos})
            
    promedio_felicidad = h_felicidad_total / len(habitantes) if habitantes else 0
    
    nuevo_registro = {
        "dia": mundo.dia,
        "poblacion": len(habitantes),
        "recursos": mundo.recursos_totales.copy(),
        "tecnologias": list(techs_totales),
        "felicidad_promedio": round(promedio_felicidad, 2),
        "heroes": heroes
    }
    
    datos_completos = []
    
    # Leer historial existente
    if os.path.exists(archivo):
        try:
            with open(archivo, "r") as f:
                datos_completos = json.load(f)
        except:
             pass # Si falla, empezamos de cero
             
    datos_completos.append(nuevo_registro)
    
    # Guardar atómicamente (simple write por ahora)
    with open(archivo, "w") as f:
        json.dump(datos_completos, f, indent=4)
        
    print(f"💾 Día {mundo.dia} registrado. Historia guardada.")

def dibujar_interfaz(pantalla, mundo):
    # Fondo semitransparente superior
    s = pygame.Surface((ANCHO_PANTALLA, 40))
    s.set_alpha(200)
    s.fill((0,0,0))
    pantalla.blit(s, (0,0))
    
    # Texto Fecha
    font = pygame.font.SysFont("Arial", 20, bold=True)
    texto_fecha = f"📅 Año {mundo.anio} | Mes {mundo.mes} | Día {mundo.dia}"
    img_fecha = font.render(texto_fecha, True, (255, 255, 255))
    
    # Centrar fecha
    rect_fecha = img_fecha.get_rect(center=(ANCHO_PANTALLA//2, 20))
    pantalla.blit(img_fecha, rect_fecha)
    
    # Hint Dashboard
    font_small = pygame.font.SysFont("Arial", 14)
    hint = "📊 Estadísticas: ejecuta 'streamlit run dashboard.py'"
    img_hint = font_small.render(hint, True, (200, 200, 200))
    pantalla.blit(img_hint, (10, 12))

def main():
    if not pygame.get_init():
        pygame.init()
        pygame.font.init()
        
    el_mundo = Mundo()
    
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
                    if el_mundo.mapa_logico[check_f][check_c]["tipo"] != "agua":
                        base_x, base_y = check_c, check_f
                        el_mundo.colocar_edificio(base_x, base_y, "centro")
                        encontrado = True
                        break
            if encontrado:
                break
        if encontrado:
            break

    # Centrar la cámara en la base
    start_iso_x, start_iso_y = el_mundo.grid_to_iso(base_x, base_y)
    camara_x = start_iso_x - (ANCHO_PANTALLA // 2)
    camara_y = start_iso_y - (ALTO_PANTALLA // 2)

    # Crear habitantes ALREDEDOR de la base
    habitantes = []
    nombres = [("Emilia", "Femenino"), ("Sofia", "Femenino"), ("Mateo", "Masculino")]
    for nombre, genero in nombres:
        # Nacen al lado de la casa
        c = base_x + random.randint(-2, 2)
        f = base_y + random.randint(-2, 2)
        habitantes.append(Habitante(c, f, nombre, genero))

    ejecutando = True
    while ejecutando:
        
        # --- INPUT (Solo si no es Headless) ---
        if not HEADLESS:
            for evento in pygame.event.get():
                if evento.type == pygame.QUIT:
                    ejecutando = False
                
                # --- CONTROLES INTELIGENTES (AUTO-DETECT) ---
                if evento.type == pygame.MOUSEWHEEL:
                    # Detectar modifier keys (CMD en Mac, CTRL en Win)
                    mods = pygame.key.get_mods()
                    is_zoom_mode = (mods & pygame.KMOD_META) or (mods & pygame.KMOD_CTRL)
                    
                    if is_zoom_mode:
                        # MODO ZOOM (Suavizado para Trackpad)
                        factor = 0.05 # Menor sensibilidad
                        if evento.y > 0: el_mundo.cambiar_zoom(factor)
                        elif evento.y < 0: el_mundo.cambiar_zoom(-factor)
                    else:
                        # MODO PANEO (Desplazamiento natural con dos dedos)
                        # Multiplicador más alto para que se sienta reactivo
                        pan_speed = 15 
                        camara_x -= evento.x * pan_speed 
                        camara_y -= evento.y * pan_speed 
                
                # --- RESET ---
                if evento.type == pygame.KEYDOWN and evento.key == pygame.K_r:
                    el_mundo = Mundo()
        else:
             # En headless debemos procesar eventos internos para evitar que se congele pygame?
             pygame.event.pump() 

        # --- CONTROL DE CÁMARA (Solo Input manual si hay GUI) ---
        if not HEADLESS:
            # 1. Teclado (Flechas)
            teclas = pygame.key.get_pressed()
            if teclas[pygame.K_LEFT]: camara_x -= VELOCIDAD_CAMARA
            if teclas[pygame.K_RIGHT]: camara_x += VELOCIDAD_CAMARA
            if teclas[pygame.K_UP]: camara_y -= VELOCIDAD_CAMARA
            if teclas[pygame.K_DOWN]: camara_y += VELOCIDAD_CAMARA
            
            # 2. Mouse (Arrastrar con clic derecho)
            mouse_botones = pygame.mouse.get_pressed()
            if mouse_botones[2]: # Clic derecho
                rel_x, rel_y = pygame.mouse.get_rel()
                camara_x -= rel_x
                camara_y -= rel_y
            else:
                pygame.mouse.get_rel() # Limpiar el delta si no arrastra

        # 1. LÓGICA (CEREBROS Y TIEMPO)
        nuevo_dia = el_mundo.actualizar_tiempo()
        if nuevo_dia:
             guardar_historia(el_mundo, habitantes)

        el_mundo.actualizar_naturaleza()
        
        # Actualizar Animales
        for animal in el_mundo.animales:
            animal.update(el_mundo)
        
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
                # Solo el "padre" o "madre" spawnea el hijo para evitar duplicados en el mismo frame
                # Usamos una probabilidad pequeña para que no sea instantáneo
                if pygame.time.get_ticks() % 100 < 5: # Hack temporal para tasa de nacimientos
                    print(f"👶 ¡Un bebé ha nacido! Familia de {h.nombre}")
                    # Heredar posición
                    bebe = Habitante(h.col, h.fila, f"Hijo de {h.nombre}", random.choice(["Masculino", "Femenino"]))
                    bebe.personalidad["sociable"] = h.personalidad["sociable"] # Hereda rasgos
                    nuevos_habitantes.append(bebe)
                    h.accion_actual = "ESPERAR" # Reset acción
                    if h.pareja: h.pareja.accion_actual = "ESPERAR"

        habitantes.extend(nuevos_habitantes)

        # 2. DIBUJO
        pantalla.fill((20, 20, 50)) # Océano profundo 
        
        # Dibujamos mundo (Pasamos la cámara)
        el_mundo.dibujar(pantalla, camara_x, camara_y)
        
        # Ordenar TODO por profundidad visual (Habitantes + Animales)
        entidades = habitantes + el_mundo.animales
        entidades.sort(key=lambda e: e.fila + e.col)
        
        # Dibujamos entidades
        for e in entidades:
            e.dibujar(pantalla, el_mundo, camara_x, camara_y)

        # 3. UI
        dibujar_interfaz(pantalla, el_mundo)
            
        # --- CAPA DE AMBIENTE (DÍA/NOCHE) ---
        overlay = pygame.Surface((ANCHO_PANTALLA, ALTO_PANTALLA), pygame.SRCALPHA)
        overlay.fill(el_mundo.color_ambiente)
        pantalla.blit(overlay, (0,0))

        # UI: Instrucciones
        font = pygame.font.SysFont("Arial", 16)
        txt = font.render("Trackpad: Dos dedos mueven, CMD+Scroll Zoom | Mouse: Click Der mover", True, (255, 255, 255))
        pantalla.blit(txt, (10, 10))

        # E. Panel de Recursos (ACTUALIZADO)
        madera = el_mundo.recursos_totales.get("madera", 0)
        piedra = el_mundo.recursos_totales.get("piedra", 0)
        comida = el_mundo.recursos_totales.get("comida", 0)
        
        font_ui = pygame.font.SysFont("Consolas", 18, bold=True)
        texto_madera = font_ui.render(f"Madera: {madera}", True, (200, 255, 200))
        texto_piedra = font_ui.render(f"Piedra: {piedra}", True, (200, 200, 200))
        texto_comida = font_ui.render(f"Comida: {comida}", True, (255, 200, 100))
        
        # Fondo semitransparente más alto para que quepa todo
        ancho_panel = 160
        alto_panel = 125
        x_panel = ANCHO_PANTALLA - ancho_panel - 10
        pygame.draw.rect(pantalla, (0, 0, 0), (x_panel, 10, ancho_panel, alto_panel))
        pygame.draw.rect(pantalla, (255, 255, 255), (x_panel, 10, ancho_panel, alto_panel), 2)
        
        pantalla.blit(texto_madera, (x_panel + 10, 20))
        pantalla.blit(texto_piedra, (x_panel + 10, 45))
        pantalla.blit(texto_comida, (x_panel + 10, 70))
        
        # Reloj
        hora = int(el_mundo.tiempo * 24)
        minuto = int((el_mundo.tiempo * 24 - hora) * 60)
        fase = "DÍA"
        if el_mundo.tiempo > 0.8 or el_mundo.tiempo < 0.2: fase = "NOCHE"
        elif el_mundo.tiempo > 0.7: fase = "ATARDECER"
        
        txt_reloj = font_ui.render(f"{fase} {hora:02d}:{minuto:02d}", True, (255, 255, 255))
        pantalla.blit(txt_reloj, (x_panel + 10, 95)) # Debajo de recursos (ajustar panel fondo)

        pygame.display.flip()
        
        # --- HEADLESS SNAPSHOT ---
        if HEADLESS:
             # Guardamos el estado visual para que el dashboard lo vea
             # Hacemos esto cada frame (o cada N frames si es muy lento)
             # HEADLESS SNAPSHOT (ATÓMICO)
             # Guardamos en un temporal y renombramos para evitar que el dashboard lea un archivo a medio escribir
             temp_file = "estado_visual_temp.png"
             final_file = "estado_visual.png"
             
             try:
                 pygame.image.save(pantalla, temp_file)
                 os.replace(temp_file, final_file) # Atomic replace en POSIX
             except Exception as e:
                 print(f"Error guardando snapshot: {e}")
             
        reloj.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()