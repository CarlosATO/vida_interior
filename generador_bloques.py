import pygame
import os

# Configuración básica
ANCHO = 64
ALTO = 32
ALTURA_BLOQUE = 20

# --- COLORES ---
COLORES_TERRENO = {
    "pasto": {"arriba": (100, 200, 50), "lado_izq": (80, 160, 40), "lado_der": (60, 130, 30)},
    "agua": {"arriba": (60, 150, 255), "lado_izq": (50, 120, 200), "lado_der": (40, 100, 180)},
    "arena": {"arriba": (240, 230, 140), "lado_izq": (220, 210, 120), "lado_der": (200, 190, 100)},
    "piedra": {"arriba": (150, 150, 150), "lado_izq": (120, 120, 120), "lado_der": (100, 100, 100)},
    "pared": {"arriba": (200, 200, 200), "lado_izq": (180, 180, 180), "lado_der": (160, 160, 160)}
}

# --- FUNCIONES DE DIBUJO ---
def dibujar_cubo_isometrico(superficie, color_info, x, y):
    c_arriba = color_info["arriba"]
    c_izq = color_info["lado_izq"]
    c_der = color_info["lado_der"]
    p1 = (x, y); p2 = (x + ANCHO // 2, y + ALTO // 2)
    p3 = (x, y + ALTO); p4 = (x - ANCHO // 2, y + ALTO // 2)
    p2_b = (p2[0], p2[1] + ALTURA_BLOQUE); p3_b = (p3[0], p3[1] + ALTURA_BLOQUE)
    p4_b = (p4[0], p4[1] + ALTURA_BLOQUE)
    pygame.draw.polygon(superficie, c_izq, [p4, p3, p3_b, p4_b])
    pygame.draw.polygon(superficie, c_der, [p3, p2, p2_b, p3_b])
    pygame.draw.polygon(superficie, c_arriba, [p1, p2, p3, p4])

def dibujar_casa(superficie, x, y):
    # Base (Paredes)
    pygame.draw.polygon(superficie, (160, 150, 140), [(x, y+20), (x-20, y+10), (x-20, y-15), (x, y-5)]) # Izq
    pygame.draw.polygon(superficie, (200, 190, 180), [(x, y+20), (x+20, y+10), (x+20, y-15), (x, y-5)]) # Der
    # Techo
    pygame.draw.polygon(superficie, (200, 60, 60), [(x, y-35), (x+25, y-10), (x, y-5), (x-25, y-10)])
    # Puerta
    pygame.draw.rect(superficie, (100, 50, 20), (x+5, y, 10, 15))

def dibujar_animal(superficie, x, y):
    # Una vaca/cerdo genérico (bloque marrón con patas)
    # Cuerpo
    pygame.draw.ellipse(superficie, (160, 82, 45), (x-15, y+10, 30, 20)) 
    # Cabeza
    pygame.draw.ellipse(superficie, (180, 100, 60), (x+5, y+5, 15, 15))
    # Patas (simples líneas)
    pygame.draw.line(superficie, (100, 50, 20), (x-5, y+25), (x-5, y+35), 3)
    pygame.draw.line(superficie, (100, 50, 20), (x+5, y+25), (x+5, y+35), 3)

def dibujar_vegetal(superficie, x, y):
    # Cultivo (tierra arada con brotes verdes)
    # Mancha de tierra
    pygame.draw.ellipse(superficie, (100, 70, 20), (x-20, y+15, 40, 20))
    # Brotes (zanahorias/lechugas)
    for i in range(3):
        offset = i * 10 - 10
        pygame.draw.polygon(superficie, (50, 200, 50), [(x+offset, y+15), (x+offset-5, y+25), (x+offset+5, y+25)])

def dibujar_fruta(superficie, x, y):
    # Arbusto de bayas
    # Arbusto verde
    pygame.draw.circle(superficie, (30, 120, 30), (x, y+20), 15)
    pygame.draw.circle(superficie, (40, 140, 40), (x-8, y+15), 12)
    pygame.draw.circle(superficie, (30, 120, 30), (x+8, y+18), 12)
    # Frutos rojos
    pygame.draw.circle(superficie, (220, 50, 50), (x, y+15), 4)
    pygame.draw.circle(superficie, (220, 50, 50), (x-10, y+20), 3)
    pygame.draw.circle(superficie, (220, 50, 50), (x+5, y+25), 4)

def main():
    pygame.init()
    base_dir = os.path.dirname(os.path.abspath(__file__))
    ruta_tiles = os.path.join(base_dir, "assets", "tiles")
    if not os.path.exists(ruta_tiles):
        os.makedirs(ruta_tiles)

    # 1. GENERAR TERRENOS
    lienzo = pygame.Surface((ANCHO, ALTO + ALTURA_BLOQUE + 5), pygame.SRCALPHA)
    for nombre, colores in COLORES_TERRENO.items():
        lienzo.fill((0,0,0,0))
        dibujar_cubo_isometrico(lienzo, colores, ANCHO//2, 0)
        pygame.image.save(lienzo, os.path.join(ruta_tiles, f"bloque_{nombre}.png"))
        print(f"Generado: bloque_{nombre}.png")

    # 2. GENERAR EDIFICIOS Y RECURSOS
    # Usamos un lienzo más alto para cosas que sobresalen
    lienzo_alto = pygame.Surface((ANCHO, 100), pygame.SRCALPHA)
    centro_x = ANCHO // 2
    centro_y = 50 # Punto base para dibujar

    # A) La Casa (Centro Urbano)
    lienzo_alto.fill((0,0,0,0))
    dibujar_casa(lienzo_alto, centro_x, centro_y)
    pygame.image.save(lienzo_alto, os.path.join(ruta_tiles, "edificio_centro.png"))
    print("Generado: edificio_centro.png")

    # B) Recursos Existentes (Árbol, Roca - Versiones simples)
    # Árbol
    lienzo_alto.fill((0,0,0,0))
    pygame.draw.rect(lienzo_alto, (100, 60, 20), (centro_x-5, centro_y, 10, 20))
    pygame.draw.polygon(lienzo_alto, (20, 180, 20), [(centro_x, centro_y-30), (centro_x-15, centro_y+5), (centro_x+15, centro_y+5)])
    pygame.image.save(lienzo_alto, os.path.join(ruta_tiles, "recurso_arbol.png"))
    
    # Roca
    lienzo_alto.fill((0,0,0,0))
    pygame.draw.circle(lienzo_alto, (160, 160, 160), (centro_x, centro_y+15), 10)
    pygame.image.save(lienzo_alto, os.path.join(ruta_tiles, "recurso_roca.png"))

    # C) NUEVOS RECURSOS DE COMIDA
    # Animal
    lienzo_alto.fill((0,0,0,0))
    dibujar_animal(lienzo_alto, centro_x, centro_y)
    pygame.image.save(lienzo_alto, os.path.join(ruta_tiles, "recurso_animal.png"))
    print("Generado: recurso_animal.png")
    
    # Vegetal
    lienzo_alto.fill((0,0,0,0))
    dibujar_vegetal(lienzo_alto, centro_x, centro_y)
    pygame.image.save(lienzo_alto, os.path.join(ruta_tiles, "recurso_vegetal.png"))
    print("Generado: recurso_vegetal.png")

    # Fruta
    lienzo_alto.fill((0,0,0,0))
    dibujar_fruta(lienzo_alto, centro_x, centro_y)
    pygame.image.save(lienzo_alto, os.path.join(ruta_tiles, "recurso_fruta.png"))
    print("Generado: recurso_fruta.png")

    pygame.quit()
    print("¡TODO GENERADO! Ejecuta main.py ahora.")

if __name__ == "__main__":
    main()