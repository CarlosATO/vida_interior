# config.py - MODO ISOMÉTRICO

# Dimensiones Pantalla
ANCHO_PANTALLA = 1200
ALTO_PANTALLA = 800
FPS = 60

# Configuración Isométrica (El tamaño de nuestros nuevos bloques)
ANCHO_TILE = 64
ALTO_TILE = 32  # Esto da el ángulo de visión
OFFSET_X = ANCHO_PANTALLA // 2  # Para centrar el mapa en pantalla
OFFSET_Y = 100                  # Bajar un poco el mapa

# Mapa Lógico (Cuadrícula)
# Haremos un mapa más pequeño pero detallado para empezar
COLUMNAS = 80
FILAS = 80

# Velocidad de la cámara (cuántos pixeles se mueve al presionar flechas)
VELOCIDAD_CAMARA = 15 

# Configuración Habitantes
VELOCIDAD_BASE = 0.05  # Ahora nos movemos por "casillas", no pixeles (0.05 casillas por frame)

# --- SISTEMA DE TIEMPO
DURACION_DIA_SEGUNDOS = 20  # ¡SÚPER RÁPIDO! Un día completo dura 20 segundos reales.
COLOR_NOCHE = (5, 5, 25)    # Azul oscuro profundo para la noche
MAX_OSCURIDAD = 180         # 0 = Transparente, 255 = Negro total (180 deja ver un poco)

# Colores de Animales
COLOR_GALLINA = (255, 255, 200) # Blanco amarillento
COLOR_CABRA = (200, 180, 160)   # Marrón claro
COLOR_FRUTA = (255, 50, 50)     # Rojo manzana