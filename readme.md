1. FILOSOFÍA DEL SISTEMA
Los Habitantes no son meros recolectores de recursos. Son entidades con "vida interior".

Principio de Humanidad: "No solo de pan vive el hombre". El ocio y la socialización son vitales.

Principio de Falibilidad: Los Habitantes cometen errores (roban, agreden) basados en impulsos o necesidad.

Principio de Redención: Existe la mecánica de "Arrepentimiento y Perdón". El perdón restaura la paz, pero la memoria histórica ("Cicatriz") permanece, alterando la confianza futura.

Principio de Diversidad: Nadie es igual a otro. La genética y la personalidad definen el comportamiento.

2. EL MUNDO (ENTORNO)
Un espacio continuo (no cuadrícula) que simula un "paraíso terrenal" con recursos finitos pero renovables.

Física: Espacio 2D con coordenadas flotantes (x, y). Movimiento fluido (360°).

Ciclo Día/Noche:

Día: Alta visibilidad, gasto de energía normal. Actividades productivas.

Noche: Baja visibilidad, peligro de frío (baja salud si no hay refugio/fuego). Incentiva el sueño y la agrupación.

Recursos:

Primarios: Comida (Arbustos/Fruta), Agua.

Secundarios: Materiales (Madera/Piedra) -> Requieren trabajo para convertirse en "Refugio" o "Juguetes".

3. EL HABITANTE (ARQUITECTURA DEL AGENTE)
3.1. Atributos Biológicos (Cuerpo)
Variables que fluctúan constantemente:

Energía (0-100): Combustible para moverse. Si llega a 0 -> Desmayo.

Salud (0-100): Integridad física. Baja por hambre extrema, enfermedad o combate. Si llega a 0 -> Muerte.

Edad (Time Steps): Contador de vida. Afecta la probabilidad de muerte natural.

Apariencia (Genética Visual):

Sprite base (Dibujo personalizado).

Color/Tinte (Heredado de padres).

Escala (Crece de Niño a Adulto).

3.2. Atributos Psicológicos (Mente)
Estado de Ánimo (Felicidad): Afecta la voluntad de trabajar o cooperar.

Vector de Personalidad (Inmutable/Genético): Valores de 0.0 a 1.0.

Laboriosidad: Tendencia a trabajar vs. Ocio.

Sociabilidad: Necesidad de estar con otros vs. Soledad.

Agresividad: Tendencia a usar la violencia para resolver conflictos.

Conciencia/Moral: Probabilidad de sentir "Culpa" tras una mala acción.

Rencor: Dificultad para perdonar una ofensa.

3.3. Memoria y Relaciones
Cada Habitante tiene una base de datos interna de "Conocidos":

JSON

{
  "ID_Habitante_B": {
    "Confianza_Actual": 50,  // Sube y baja rápido
    "Historial_Agravios": ["Robo día 4", "Insulto día 10"], // No se borra
    "Ultima_Interaccion": "Dia 12"
  }
}
4. SISTEMAS DE COMPORTAMIENTO (LOOPS)
4.1. Loop de Decisión (Cerebro)
En cada "tick" del reloj, el Habitante evalúa:

Input: Estado interno (Hambre, Soledad) + Entorno (¿Qué veo?).

Filtro: Personalidad (¿Soy flojo? ¿Soy agresivo?).

Output (Acción):

BUSCAR_COMIDA

TRABAJAR (Procesar recursos)

SOCIALIZAR (Buscar a otro)

DESCANSAR

HUIR (Si hay amenaza)

PEDIR_PERDON (Si Conciencia > Orgullo)

4.2. Sistema de Justicia Emocional
La Ofensa: A roba a B.

La Reacción: B registra la ofensa. Baja la confianza a 0. B puede atacar o huir.

El Remordimiento: A (si tiene moral alta) siente bajar su Felicidad por "Culpa".

La Redención: A busca a B para Accion: Disculparse.

El Juicio: B evalúa (Gravedad_Ofensa * Rencor_Personal) vs (Afecto_Previo).

Resultado Positivo: "Te perdono, pero te vigilo". Confianza sube un poco.

Resultado Negativo: "Lárgate". Confianza se mantiene en 0.

4.3. Reproducción
Requisitos:

Dos habitantes compatibles (Disposición > 50).

Ambos con Energía y Salud alta.

Resultado: Nuevo Habitante con mezcla de vectores de personalidad + Mutación aleatoria pequeña.

5. VISUALIZACIÓN
Motor: PyGame (para control total de píxeles y rendimiento).

Estética:

Fondo: Mapa orgánico (verde, agua, rocas).

Personajes: Sprites animados basados en arte manual (dibujos digitalizados).

Indicadores: Barras pequeñas sobre la cabeza (Salud/Estado).

Efectos: Emojis o burbujas que aparecen al interactuar (💔, 🤝, 😡, 🍖).

python main.py

## Procesamiento de personajes (quitar fondo de papel)

Cuando digitalizas un personaje dibujado en papel, el fondo del papel suele quedar alrededor del sprite.
La técnica usada en este proyecto convierte ese fondo en transparente automáticamente usando estos pasos:

- Cargar la imagen con `convert_alpha()` para preservar el canal alfa.
- Calcular el color de fondo aproximado tomando el promedio de las 4 esquinas de la imagen.
- Hacer un "flood-fill" (recorrido 4-direccional) desde las 4 esquinas. Si un píxel está suficientemente cerca
  del color de fondo (distancia de color <= `tol`) se convierte en totalmente transparente.
- Realizar un pase global adicional que convierte a transparentes los píxeles cercanos al color de fondo
  con una tolerancia `tol_global` (esto elimina bordes o rectángulos residuales).

Parámetros a ajustar en `scripts/process_personaje.py` (valores por defecto usados aquí):
- `tol` = 90.0 (flood-fill)
- `tol_global` = 80.0 (pase global)

Cómo usarlo:

1. Coloca la foto original en la raíz del proyecto con nombre `personaje.png` (o cópiala a `assets/`).
2. Activa tu entorno virtual y asegúrate de tener `pygame` instalado:

```bash
# ejemplo usando el venv del proyecto
/Users/carlosalegria/Desktop/Aplicaciones\ Carlos\ Alegria/Vida\ interior/.venv/bin/python -m pip install pygame
/Users/carlosalegria/Desktop/Aplicaciones\ Carlos\ Alegria/Vida\ interior/.venv/bin/python scripts/process_personaje.py
```

3. El script procesará la imagen y guardará la versión final en `assets/personaje.png`.
4. Ejecuta `python main.py` para ver el sprite sin fondo de papel.

Limpieza de archivos temporales:

Si quieres mantener el proyecto limpio, puedes eliminar los archivos temporales generados durante pruebas:

```bash
rm personaje.png personaje_trans.png scripts/check_personaje.py
```

Recomendación: guarda siempre una copia del original si quieres mantener la fuente (por ejemplo `assets/personaje_original.png`).

Si prefieres, puedo añadir una opción al script para que haga automáticamente un backup del original antes de procesar.
