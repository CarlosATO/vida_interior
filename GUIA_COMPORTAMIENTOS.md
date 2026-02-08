# Guía Completa de Comportamientos - Vida Interior

## 📖 Introducción

Los habitantes de Vida Interior son agentes autónomos con inteligencia artificial que toman decisiones en tiempo real basándose en sus necesidades, personalidad, conocimientos y relaciones sociales. Este documento describe todo lo que pueden hacer.

---

## 🧠 Sistema de Necesidades

Cada habitante tiene 5 necesidades que suben o bajan continuamente:

### Necesidades Básicas (0-100)
- **Hambre** (0 = lleno, 100 = muerte)
  - Sube: 0.05/tick × factor glotón
  - Baja: Comiendo frutas (-50), vegetales (-50), animales (-80)
  
- **Sed** (0 = hidratado, 100 = muerte)
  - Sube: 0.005/tick (muy lento, 30-40 min para morir)
  - Baja: Bebiendo agua (se pone en 0)
  
- **Energía** (0 = agotado, 100 = descansado)
  - Baja: 0.02/tick × factor trabajador + acciones físicas
  - Sube: Durmiendo (+0.5/tick), comiendo (+5 a +20)
  
- **Social** (0 = solo, 100 = feliz)
  - Baja: 0.02/tick × factor sociable
  - Sube: Interactuando (+10 a +30), enseñando hijos (+20)
  
- **Diversión** (0 = aburrido, 100 = entretenido)
  - Baja: Lentamente con el tiempo
  - Sube: Descubriendo cosas, socializando

---

## 🎭 Personalidad

Cada habitante tiene 4 rasgos de personalidad (valores: 0.5 a 2.0):

| Rasgo | Efecto | Comportamiento |
|-------|--------|----------------|
| **Trabajador** | Multiplica pérdida de energía | Valores altos = más recolección, menos descanso |
| **Sociable** | Multiplica pérdida social | Valores altos = busca más interacciones, forma parejas fácilmente |
| **Glotón** | Multiplica aumento de hambre | Valores altos = come más frecuentemente |
| **Curioso** | Probabilidad de descubrimiento | Valores altos = más experimentación, descubre tecnologías |

### Herencia Genética
Los bebés heredan personalidad de sus padres:
- Promedio de ambos padres + mutación (-0.1 a +0.1)
- Sin pareja: herencia del padre/madre + mutación mayor (-0.2 a +0.2)
- Límites: siempre entre 0.5 y 2.0

---

## 👨‍👩‍👧‍👦 Sistema de Familia

### Reproducción
**Condiciones:**
- Tener pareja
- Sed social > 80
- Energía > 70
- Estar cerca uno del otro (< 2 unidades)

**Proceso:**
- Probabilidad 5% por tick cuando están en estado "CORAZÓN"
- Costo: -30 energía, -100 social para ambos padres

### Nacimiento
**Bebés reciben:**
- Nombre único del banco (19 masculinos, 18 femeninos)
- Género aleatorio
- Personalidad heredada con mutación genética
- 2 conocimientos aleatorios de cada padre (herencia cultural)
- Referencias a padre y madre
- Color de cuerpo según género

### Relaciones Familiares
- **Padres → Hijos**: Lista de descendientes, instinto de enseñanza
- **Hijos → Padres**: Referencias a madre y padre
- **Edad**: Contador en ticks (futuro: madurez sexual, envejecimiento)

---

## 🧪 Sistema de Conocimientos

### Descubrimientos
Los habitantes pueden descubrir tecnologías experimentando:

| Tecnología | Ingredientes | Probabilidad |
|------------|-------------|--------------|
| Fuego | 1 madera + 1 piedra | 2% × curiosidad |
| Herramientas | 1 madera | 2% × curiosidad |
| Refugio | 2 maderas + 2 piedras | 2% × curiosidad |
| Casa | 5 maderas + 5 piedras | 2% × curiosidad |
| Rueda | 2 maderas + 1 piedra | 2% × curiosidad |

**Proceso:**
1. Tener los ingredientes en inventario
2. Acción "EXPERIMENTAR" (requiere energía > 60, hambre < 20)
3. Si tiene éxito: "💡 ¡EUREKA! [Nombre] descubrió: [Tecnología]"
4. Se convierte en "héroe" temporalmente

### Transferencia de Conocimientos

#### Entre Adultos (Socialización)
- Probabilidad 50% × sociabilidad al interactuar
- Si uno tiene conocimiento que el otro no:
  - Receptor lo aprende instantáneamente
  - Emisor muestra "💬", receptor muestra "💡"

#### De Padres a Hijos (Enseñanza)
- **Al nacer**: Bebé hereda 2 conocimientos aleatorios de cada padre
- **Durante vida**: Padres buscan activamente a sus hijos si:
  - Hijo tiene menos conocimientos
  - Padre tiene energía suficiente
  - Están a menos de 30 unidades de distancia
- **Beneficio**: +20 necesidad social para ambos
- **Mensaje**: "👨‍👧 [Padre] enseñó [Tecnología] a su hijo/a [Hijo]"

---

## 🎯 Acciones Disponibles

### Supervivencia Básica

#### BEBER
- **Cuándo**: Sed > 30 (crítico: > 50 activa instinto)
- **Proceso**: 
  1. Buscar agua en memoria
  2. Si no hay: Instinto de supervivencia (escanea todo el mapa)
  3. Caminar hacia agua
  4. Beber (sed = 0, energía +5)
- **Instinto**: A sed > 30, "huele" agua en un radio de 40 unidades

#### COMER
- **Cuándo**: Hambre > 30
- **Opciones**:
  - Frutas/vegetales: -50 hambre, +10 energía
  - Animales cazados: -80 hambre, +20 energía
- **Memoria**: Recuerda ubicación de comida vista

#### DORMIR
- **Cuándo**: Energía < 20 (urgente) o < 60 (mantenimiento)
- **Lugares**: Casa, centro urbano, o en el suelo
- **Efecto**: +0.5 energía/tick hasta llegar a 100

### Trabajo y Recolección

#### RECOLECTAR
- **Recursos**: Árboles (madera) y Rocas (piedra)
- **Tiempo**: 60 ticks de trabajo continuo
- **Costo**: -0.5 energía/tick mientras trabaja
- **Resultado**: +1 recurso al inventario
- **Memoria**: Guarda ubicación de recursos

#### CONSTRUIR
- **Requisitos**: Tener recursos + conocimiento de la tecnología
- **Tipos**:
  - Centro: Punto de encuentro nocturno
  - Casa: Para dormir mejor
  - Refugio: Protección básica
- **Efecto**: Crea edificio en el mundo, todos pueden usarlo

### Exploración

#### CAMINAR
- **Motivos**:
  - Ir a recursos conocidos
  - Explorar áreas nuevas
  - Acercarse a otros habitantes
  - Ir al centro urbano de noche (tiempo > 0.82)
- **Pathfinding**: Usa A* para evitar agua y obstáculos
- **Memoria**: Actualiza mapa mental mientras camina

#### EXPLORAR
- **Cuándo**: Sin objetivos urgentes, curiosidad
- **Radio**: Hasta 15 unidades aleatorias
- **Efecto**: Descubre nuevos recursos, expande memoria

### Interacción Social

#### SOCIALIZAR
- **Cuándo**: Sed social baja o encuentro con otros
- **Efectos**:
  - +10 a +30 necesidad social para ambos
  - Aumenta compatibilidad entre habitantes
  - Posible transferencia de conocimientos
- **Noche**: Se juntan en el centro urbano automáticamente

#### REPRODUCIR
- **Requisitos**: Pareja + social > 80 + energía > 70 + proximidad < 2
- **Costo**: -30 energía, social = 0
- **Resultado**: Bebé con herencia genética y cultural
- **Cooldown**: Ambos padres quedan en "ESPERAR"

#### ENSEÑAR (Nuevo)
- **Objetivo**: Padres → Hijos
- **Prioridad**: 12 (muy alta, solo superada por supervivencia)
- **Proceso**:
  1. Padre identifica hijo con menos conocimientos
  2. Camina hacia el hijo si está lejos
  3. Transfiere 1-2 conocimientos nuevos
  4. +20 social para ambos
- **Visuals**: Padre "📚", Hijo "✨"

#### FORMAR PAREJA
- **Compatibilidad**: Se calcula al interactuar (0-100)
- **Condiciones**: 
  - Compatibilidad > 80
  - Ambos sin pareja
  - Sed social > 90
  - Proximidad < 4 unidades
- **Probabilidad**: 5% por tick de interacción
- **Efecto**: Quedan vinculados, pueden reproducirse

### Innovación

#### EXPERIMENTAR
- **Cuándo**: Energía > 60, hambre < 20, tiene recursos
- **Personalidad**: Multiplicado por factor "curioso"
- **Probabilidad base**: 2% por tick
- **Éxito**: Descubre tecnología si tiene ingredientes
- **Mensaje**: "💡 ¡EUREKA! [Nombre] descubrió: [Tecnología]"
- **Beneficio**: Se vuelve "héroe", puede enseñar a otros

---

## 🧠 Sistema de Decisiones (IA)

### Prioridades (GOAP + Utility-Based AI)

Orden descendente de prioridad:

1. **Supervivencia Inmediata** (Prioridad: 10-50)
   - Sed > 50: Prioridad 50 (PÁNICO)
   - Sed > 30: Prioridad 10
   - Hambre > 30: Prioridad 10
   - Energía < 20: Prioridad 10

2. **Protección Familiar** (Prioridad: 12)
   - Enseñar a hijos con menos conocimientos
   - Solo si hijo está vivo y a < 30 unidades

3. **Reproducción** (Prioridad: 15)
   - Si tiene pareja + social > 80 + energía > 70

4. **Crafting** (Prioridad: 8)
   - Si tiene recursos suficientes para receta

5. **Mantenimiento** (Prioridad: 5)
   - Energía < 60: Buscar descanso

6. **Ambición/Curiosidad** (Prioridad: 2)
   - Hambre < 20 + energía > 60
   - Descubrir tecnologías (sabio: 2)
   - Acumular recursos (rico: 1)

7. **Default** (Prioridad: 1)
   - Recolectar recursos
   - Explorar aleatoriamente

### Replanificación Automática
- Si hambre > 90: Aborta plan actual, busca comida
- Si sed > 50: Aborta plan, busca agua (instinto)
- Si plan falla: Replanifica en siguiente tick

---

## 🌍 Comportamientos Emergentes

### Comportamiento Nocturno (tiempo > 0.82)
- Todos van al centro urbano
- Se socializan en grupo (radio 4 unidades)
- Forman parejas más frecuentemente
- Enseñan conocimientos entre ellos

### Memoria y Aprendizaje
- **Radio de visión**: 8 unidades
- **Memoriza**: Recursos, agua, edificios, animales
- **Límite**: Últimos 1000 registros (no se olvida nada importante)
- **Actualización**: Cada tick mientras percibe

### Compatibilidad Social
- Se calcula dinámicamente al interactuar
- Factores: Proximidad de personalidad, tiempo juntos
- > 80: Posible pareja
- > 90: Alta probabilidad de reproducción

### Death & Legacy
**Causas de muerte:**
- Hambre >= 100
- Sed >= 100

**Bitácora registra:**
- "💀 [Nombre] murió de [causa]"
- Hijos quedan huérfanos pero con conocimientos heredados
- Inventario se pierde (no hay herencia material aún)

---

## 📊 Sistema de Tracking (Data Science)

### Datos Capturados por Decisión
- Tiempo del mundo (t)
- Necesidades completas (hambre, sed, energía, social, diversión)
- Decisión tomada (acción ejecutada)
- Razón de la decisión (objetivo GOAP)
- Posición (col, fila)
- Inventario completo
- Personalidad (4 rasgos)
- Acción actual
- Es héroe (bool)
- Pareja (si tiene)

### Estadísticas Agregadas
- Habitantes vivos
- Total de decisiones tomadas
- Decisiones por tipo (conteo)
- Muertes por causa (hambre/sed)
- Necesidades promedio
- Evolución poblacional (tiempo vs habitantes)
- Agrupaciones por nodos (clusters de proximidad)
- Delitos/decisiones negativas

### Exportación
- Endpoint `/api/exportar_datos`
- Formato JSON con:
  - Todas las decisiones históricas
  - Bitácora completa de eventos
  - Historia poblacional (tiempo, población)
- Análisis offline: Pandas, correlaciones, predicciones

---

## 🎮 Dinámicas de Juego

### Ciclo Día/Noche
- **Día** (tiempo 0.0 - 0.82): Trabajo, recolección, exploración
- **Noche** (tiempo > 0.82): Socialización en centro, reproducción

### Formación de Comunidades
- Habitantes sociables forman núcleo central
- Solitarios trabajan en periferia
- Padres enseñan a hijos → conocimiento se propaga
- Parejas cuidan a sus descendientes

### Evolución Generacional
- **Gen 1 (fundadores)**: Descubren tecnologías básicas
- **Gen 2 (hijos)**: Heredan conocimientos + descubren nuevas
- **Gen 3+**: Conocimientos acumulados, sociedad avanzada
- **Linajes**: Familias con personalidades definidas

### Estrategias de Supervivencia
- **Trabajadores**: Acumulan recursos, construyen
- **Curiosos**: Descubren tecnologías, enseñan
- **Sociables**: Forman parejas, reproducen, expanden población
- **Solitarios**: Eficientes pero menos reproducción

---

## 🔧 Configuraciones Clave

### Velocidades de Necesidades
```python
hambre += 0.05 * gloton
sed += 0.005
energia -= 0.02 * trabajador
social -= 0.02 * sociable
```

### Umbrales Críticos
```python
hambre_critica = 90 (aborta plan)
sed_critica = 30 (instinto) / 50 (pánico)
energia_critica = 20
social_pareja = 80
energia_reproduccion = 70
```

### Herencia Genética
```python
rasgo_hijo = (padre + madre) / 2 + random(-0.1, 0.1)
# Límites: max(0.5, min(2.0, rasgo_hijo))
```

### Probabilidades
```python
descubrimiento = 0.02 * curioso (por tick)
reproduccion = 0.05 (si condiciones se cumplen)
enseñanza_social = 0.5 * sociable
formar_pareja = 0.05 (si compatibilidad > 80)
```

---

## 🚀 Casos de Uso Especiales

### Extinción Masiva
**Prevención:**
- Instinto de supervivencia a sed > 30
- Olfato de agua en radio 40 unidades
- Velocidad de sed reducida (0.005)

### Población Cero
**Recuperación:**
- Endpoint `/reiniciar` crea 10 fundadores
- Nombres únicos del banco
- Personalidades variadas predefinidas

### Explosión Poblacional
**Límites naturales:**
- Recursos limitados → hambre
- Espacio limitado → competencia
- Energía de reproducción alta (-30)

### Estancamiento Tecnológico
**Solución:**
- Hijos heredan conocimientos de padres
- Sociables comparten descubrimientos
- Curiosos siguen experimentando

---

## 📚 Resumen de Comportamientos Implementados

✅ **Supervivencia Autónoma**: Comen, beben, duermen sin intervención  
✅ **Instinto de Supervivencia**: Encuentran agua aunque no la hayan visto  
✅ **Recolección y Construcción**: Juntan recursos, construyen casas  
✅ **Descubrimiento de Tecnologías**: Experimentan e inventan  
✅ **Socialización**: Hablan, forman amistades, calculan compatibilidad  
✅ **Reproducción**: Forman parejas, tienen bebés con nombres propios  
✅ **Herencia Genética**: Personalidad de padres con mutación  
✅ **Herencia Cultural**: Conocimientos de padres a hijos  
✅ **Protección Parental**: Padres enseñan activamente a descendientes  
✅ **Memoria Espacial**: Recuerdan recursos, agua, edificios  
✅ **Pathfinding Inteligente**: A* para evitar obstáculos  
✅ **Comportamiento Nocturno**: Se juntan en centro urbano  
✅ **Toma de Decisiones GOAP**: Planificación por objetivos  
✅ **Utility-Based AI**: Priorizacion por necesidades  
✅ **Tracking Completo**: Todas las decisiones registradas  
✅ **Evolución Generacional**: Linajes y dinastías  

---

## 🎯 Futuras Expansiones Posibles

- **Envejecimiento**: Edad máxima, fertilidad por edad
- **Economía**: Comercio de recursos entre habitantes
- **Conflictos**: Competencia por recursos, territorios
- **Especialización**: Roles (cazador, constructor, maestro)
- **Cultura**: Creencias, rituales, jerarquías
- **Agricultura**: Cultivar en lugar de recolectar
- **Domesticación**: Criar animales
- **Medicina**: Curar enfermedades, aumentar esperanza de vida

---

**Documento creado para referencia pública de Vida Interior**  
*Última actualización: 7 de febrero de 2026*
