# PLAN.md - Hoja de Ruta para MVP: "Vida Interior"

Este documento define la estrategia técnica para transformar el prototipo actual en una simulación de vida autónoma funcional, orientada a la recolección de datos de comportamiento.

---

## 1. Lógica y IA (Cerebro y Comportamiento)
El objetivo es dotar a los habitantes ('Emilia' y otros) de autonomia real, comportamiento humano complejo y capacidad de supervivencia a largo plazo.

### 1.1 Sistema de Pathfinding (Navegación)
*   **Problema Actual:** Movimiento en línea recta que atraviesa obstáculos (agua, montañas).
*   **Solución Técnica:** Implementar algoritmo **A* (A-Star)** en `mundo.py`.
    *   Crear función `obtener_camino(origen, destino)` que retorne una lista de coordenadas `[(x1,y1), (x2,y2)...]`.
    *   Integrar en `habitante.py`: El movimiento debe seguir la lista de nodos paso a paso.

### 1.2 Sistema Complejo de Necesidades
*   **Estado Actual:** Solo existe `energia` y `inventario`.
*   **Expansión:** Implementar Modelo de Necesidades en `Habitante`.
    *   **Hambre:** Decae con el tiempo. Si llega a 0, pierde salud. Se recupera comiendo recursos ("comida").
    *   **Sueño/Energía:** Ya existe, pero debe vincularse al ciclo día/noche.
    *   **Salud:** Si baja de 100, requiere descanso prolongado.
*   **Mecánica de Muerte:** Si Salud = 0, el habitante muere (se elimina de la lista o queda como "cuerpo").

### 1.3 Reproducción y Ciclo Vital (NUEVO)
*   **Mecánica:** Los habitantes podrán reproducirse si cumplen condiciones (Energía alta, pareja cercana, casa disponible).
*   **Herencia:** Los descendientes podrían heredar parámetros (velocidad, inteligencia) de los padres.
*   **Crecimiento:** De niño a adulto.

### 1.4 Sistema Social y Emocional (NUEVO)
*   **Memoria Social:** Capacidad de recordar interacciones pasadas con otros habitantes (positivas o negativas).
*   **Mecánica de "Perdón":** Los habitantes pueden cometer "errores" (ej. chocar, robar recurso accidentalmente). El afectado decidirá si perdonar o guardar rencor en función de su personalidad y relación previa.
*   **Toma de Decisiones Compleja:** Evaluar acciones no solo por utilidad inmediata sino por consecuencias sociales (ej. "No talaré este árbol porque está cerca de la casa de X y se molestará").

### 1.5 Máquina de Estados Finitos (FSM) Mejorada
*   **Refactorizar `cerebro.py`:** Estructura de estados clara.
    *   `STATE_IDLE`: Explorar o esperar.
    *   `STATE_SURVIVAL`: Buscar comida/dormir.
    *   `STATE_WORK`: Recolección eficiente.
    *   `STATE_SOCIAL`: Interactuar, buscar pareja, dialogar.

---

## 2. Mundo y Entorno
El mundo debe ser un ecosistema dinámico y **visualmente impactante**.

### 2.1 Regeneración de Recursos
*   **Dinámica:** Crecimiento de flora con el tiempo. `Mundo.tick_ecosistema()`.

### 2.2 Ciclo Día/Noche Funcional
*   **Efecto:** Variación de luz y comportamiento (dormir de noche).

### 2.3 Estética Premium del Paisaje y Edificios (NUEVO)
*   **Objetivo:** El paisaje y las casas deben destacar visualmente. "Wow factor".
*   **Mejora de Casas:** Diseños modulares o detallados que reflejen el estatus o personalidad del dueño.
*   **Entorno:** Mejorar tiles de agua, montañas y vegetación para que sean agradables a la vista.

---

## 3. Gráficos y UI (Visualización)

### 3.1 Reemplazo de Avatares (NUEVO)
*   **Acción Inmediata:** Eliminar los avatares actuales.
*   **Reemplazo:** Usar formas geométricas estilizadas (ej. cápsulas minimalistas con colores distintivos) o un nuevo estilo artístico procedimental temporal, hasta tener los diseños finales mejorados.

### 3.2 UI de Inspección y Debug
*   **Inspector:** Ver stats detallados, emociones y relaciones al hacer clic.
*   **Logs y Debug:** Visualizar rutas y eventos sociales.

---

## 4. Pasos de Ejecución Inmediata
1.  **Refactor Main Loop:** Separar lógica de dibujo para permitir aceleración del tiempo (para entrenar/ver datos rápido).
2.  **Pathfinding:** Implementar A* (Prioridad Máxima para evitar comportamiento errático).
3.  **Sistema de Necesidades:** Implementar Hambre y consumo de items.
4.  **UI de Inspección:** Para verificar que las decisiones sean lógicas.
