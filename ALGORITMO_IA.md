# Arquitectura de IA: Vida Interior

El sistema de toma de decisiones de los habitantes utiliza un enfoque híbrido avanzado que combina tres pilares fundamentales de la IA para simulación:

## 1. Utility-Based AI (IA de Utilidad)
Ubicada principalmente en el método `pensar()` de `cerebro.py`.

*   **Concepto:** Cada necesidad del habitante (hambre, sed, energía, social) compite por atención.
*   **Funcionamiento:** El cerebro evalúa el estado interno y asigna una "prioridad" (utilidad) a diferentes objetivos.
    *   Si la `sed` supera un umbral (ej: 30), el objetivo "hidratado" gana prioridad sobre otros como "trabajar" o "socializar".
*   **Personalidad:** Los rasgos de cada habitante actúan como multiplicadores. Un habitante "Glotón" dará más prioridad al hambre que uno normal.

## 2. GOAP (Goal-Oriented Action Planning)
Implementado a través del sistema de **Planes** en `cerebro.py`.

*   **Concepto:** En lugar de tener comportamientos fijos (si A entonces B), el habitante recibe un **Objetivo** (ej: `saciado`) y debe encontrar la mejor secuencia de acciones para alcanzarlo.
*   **Implementación:** El método `construir_plan` genera una lista de acciones (`Accion`). 
    *   Ejemplo para el objetivo `descansado`: `[CAMINAR(casa), DORMIR]`.
*   **Flexibilidad:** Permite que el habitante use diferentes métodos para resolver la misma necesidad según lo que tenga disponible en su memoria.

## 3. Pathfinding A* (A-Estrella)
Utilizado para la navegación física en el mundo.

*   **Concepto:** Algoritmo óptimo para encontrar el camino más corto esquivando obstáculos.
*   **Uso:** Cuando un plan requiere moverse a una ubicación (ej: una fuente de agua o un árbol), el habitante solicita una ruta al mundo usando A*. La lista de coordenadas resultante se almacena en `self.camino`.

## Resumen del Ciclo de Vida (Loop)
1.  **Percibir:** El cerebro escanea el entorno y actualiza la `memoria` (recursos, edificios, animales).
2.  **Evaluar:** El sistema de Utilidad elige el **Objetivo** más urgente.
3.  **Planificar:** El GOAP construye una lista de **Acciones** para ese objetivo.
4.  **Actuar:** El cuerpo ejecuta el plan paso a paso hasta completarlo o hasta que una emergencia (como hambre crítica) obligue a replanificar.

## 4. Instinto de Supervivencia (Survival Instinct)
Incorporado en el GOAP para situaciones críticas.

*   **Concepto:** Cuando la sed supera el 30% (antes era 50%), el habitante ignora su memoria limitada y activa un "olfato" omnisciente que busca agua en todo el mapa.
*   **Funcionamiento:** En `buscar_agua_instinto()`, escanea el mapa completo para encontrar la fuente de agua más cercana, actualizando la memoria mágicamente.
*   **Propósito:** Previene extinciones masivas por sed, simulando instinto animal real. Reduce la velocidad de sed a 0.005 por tick para dar tiempo al cerebro.

## 5. Sistema de Captura de Datos y Análisis (Data Science Integration)
Implementado para monitoreo y análisis científico.

*   **Captura Rica de Decisiones:** Cada decisión se registra en `historia_decisiones` con metadatos completos: necesidades, posición, inventario, personalidad, pareja, etc.
*   **Endpoints de Estadísticas:**
    *   `/analisis`: Devuelve decisiones históricas para gráficos en tiempo real.
    *   `/estadisticas`: Agregados como población, muertes por causa, evolución poblacional, agrupaciones por proximidad, y "delitos" (decisiones negativas como inactividad con hambre alta).
    *   `/exportar_datos`: JSON completo para análisis offline con Pandas/Python.
*   **Visualizaciones en Vivo:** Pantalla `/analisis` con gráficos Chart.js: evolución de necesidades, distribución de acciones, muertes por causa, decisiones por tipo, evolución poblacional lineal.
*   **Agrupaciones por Nodos:** Detecta clusters de habitantes cercanos (<5 unidades) para analizar comunidades y reproducción.
*   **Tracking Poblacional:** Registra población cada 0.01 unidades de tiempo, mostrando ciclos de nacimientos/muertes.
*   **Delitos y Decisiones Negativas:** Identifica comportamientos riesgosos para estudiar causas de mortalidad.

## 6. Mejoras en la Simulación
*   **Velocidad de Necesidades Ajustada:** Sed sube más lento para permitir decisiones lógicas.
*   **Interacciones Sociales:** Métodos `interactuar` y `hablar` permiten enseñanza de conocimientos y formación de parejas.
*   **Reinicio y Persistencia:** Endpoint `/reiniciar` para resetear el mundo, manteniendo datos históricos.

## Arquitectura Técnica
- **Backend:** FastAPI con asyncio para simulación en background (10 ticks/seg).
- **Frontend:** HTML/JS con Chart.js para dashboards; Canvas para visualización del mundo.
- **Despliegue:** Railway para hosting continuo, permitiendo monitoreo remoto.
- **Análisis Offline:** Exportación JSON para ciencia de datos (correlaciones, predicciones, clustering).

Esta arquitectura permite simular sociedades emergentes con IA realista, optimizable vía datos científicos.
