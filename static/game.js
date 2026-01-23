const canvas = document.getElementById('gameCanvas');
const ctx = canvas.getContext('2d');

// Configuración
const TILE_WIDTH = 64;
const TILE_HEIGHT = 32;
let OFFSET_X = window.innerWidth / 2;
let OFFSET_Y = 100;
let ZOOM_LEVEL = 1.2;

// Estado del Juego
let mapa = null; // {filas, columnas, mapa[][], edificios[]}
let estado = null; // {habitantes, animales, recursos_mapa, tiempo...}
let lastFetch = 0;
const FETCH_INTERVAL = 100; // ms

// Assets
const images = {};
const assetList = [
    'bloque_pasto', 'bloque_agua', 'bloque_arena', 'bloque_piedra', 'bloque_pared',
    'recurso_arbol', 'recurso_roca', 'recurso_fruta', 'recurso_animal', 'recurso_vegetal',
    'edificio_centro'
];

// Cargar imágenes
let assetsLoaded = 0;
assetList.forEach(name => {
    const img = new Image();
    img.src = `../assets/tiles/${name}.png`; // Asumiendo estructura /assets servida o movida a static?
    // FastAPI no sirve ../assets por defecto si solo montamos static.
    // Hack: Asumiremos que el backend sirve assets en /static/assets o moveremos la carpeta.
    // Por ahora, intentaremos cargar de una ruta relativa si configuramos el backend para servir assets también.
    // MEJOR: Mover assets dentro de static/assets en el backend setup O montar /assets en FastAPI.
    // Asumiré que montaremos /assets en el main.py también.
    img.src = `/assets/tiles/${name}.png`;
    img.onload = () => { assetsLoaded++; };
    images[name] = img;
});

// Input de Cámara
let isDragging = false;
let lastMouseX = 0;
let lastMouseY = 0;

canvas.width = window.innerWidth;
canvas.height = window.innerHeight;

window.addEventListener('resize', () => {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
});

canvas.addEventListener('mousedown', e => {
    e.preventDefault(); // Prevent text selection/drag behavior
    isDragging = true;
    lastMouseX = e.clientX;
    lastMouseY = e.clientY;
    canvas.style.cursor = 'grabbing';
});

window.addEventListener('mouseup', () => {
    isDragging = false;
    canvas.style.cursor = 'default';
});

// Disable right click context menu to allow right-click interactions if needed later
canvas.addEventListener('contextmenu', e => e.preventDefault());

canvas.addEventListener('mousemove', e => {
    if (isDragging) {
        OFFSET_X += e.clientX - lastMouseX;
        OFFSET_Y += e.clientY - lastMouseY;
        lastMouseX = e.clientX;
        lastMouseY = e.clientY;
    }

    // Calcular hover
    // Inverso de gridToIso approx (más complejo por isometría)
    // Simple Raycast visual: iterar tiles y ver cual esta cerca del mouse
    // Optimización: Solo chequear si no arrastramos
    mouseHover = null;
    if (!isDragging && mapDataCache) {
        // Busqueda aproximada
        // isoX = (col - fila) * Tw/2 + offX
        // isoY = (col + fila) * Th/2 + offY
        // Despejando...

        const adjX = e.clientX - OFFSET_X;
        const adjY = e.clientY - OFFSET_Y;
        const Tw = TILE_WIDTH * ZOOM_LEVEL;
        const Th = TILE_HEIGHT * ZOOM_LEVEL;

        // col = (adjX / (Tw/2) + adjY / (Th/2)) / 2
        // fila = (adjY / (Th/2) - adjX / (Tw/2)) / 2

        const colApprox = Math.floor((adjX / (Tw / 2) + adjY / (Th / 2)) / 2);
        const rowApprox = Math.floor((adjY / (Th / 2) - adjX / (Tw / 2)) / 2);

        if (mapDataCache.mapa[rowApprox] && mapDataCache.mapa[rowApprox][colApprox]) {
            mouseHover = { c: colApprox, f: rowApprox };
        }
    }
});

let mouseHover = null;
let mapDataCache = null;

canvas.addEventListener('wheel', e => {
    e.preventDefault();

    if (e.ctrlKey || e.metaKey) {
        // ZOOM (Pinch gesture often sends ctrlKey on trackpads)
        const zoomSpeed = 0.001;
        ZOOM_LEVEL -= e.deltaY * zoomSpeed;
        if (ZOOM_LEVEL < 0.2) ZOOM_LEVEL = 0.2;
        if (ZOOM_LEVEL > 3.0) ZOOM_LEVEL = 3.0;
    } else {
        // PAN (Trackpad scroll or Mouse wheel without Ctrl)
        OFFSET_X -= e.deltaX;
        OFFSET_Y -= e.deltaY;
    }
});

// --- FUNCIONES ISOMÉTRICAS ---
function gridToIso(col, fila) {
    const x = (col - fila) * (TILE_WIDTH * ZOOM_LEVEL / 2) + OFFSET_X;
    const y = (col + fila) * (TILE_HEIGHT * ZOOM_LEVEL / 2) + OFFSET_Y;
    return { x, y };
}

// --- RENDERIZADO DE AVATARES ---
function drawAvatar(ctx, x, y, habitante, zoom) {
    const scale = zoom * 0.8;
    const time = Date.now() * 0.005; // Velocidad animación

    // Si se mueve, animar piernas
    const isMoving = habitante.accion === "CAMINAR" || habitante.accion === "BUSCANDO" || habitante.accion === "BEBIENDO";
    const legOffset = isMoving ? Math.sin(time) * 3 : 0;

    ctx.save();
    ctx.translate(x, y);
    ctx.scale(scale, scale);

    // Sombra
    ctx.fillStyle = "rgba(0,0,0,0.3)";
    ctx.beginPath();
    ctx.ellipse(0, 0, 8, 4, 0, 0, Math.PI * 2);
    ctx.fill();

    // Piernas (Pantalón oscuro)
    ctx.fillStyle = "#333";
    // Pierna Izq
    ctx.fillRect(-4, -10 + legOffset, 3, 10);
    // Pierna Der
    ctx.fillRect(1, -10 - legOffset, 3, 10);

    // Cuerpo (Camiseta color habitante)
    ctx.fillStyle = habitante.color;
    ctx.fillRect(-5, -22, 10, 14);

    // Brazos
    ctx.fillStyle = "#F5D0A9"; // Piel
    if (habitante.accion === "RECOLECTAR") {
        // Brazo levantado trabajando
        const armWave = Math.sin(time * 3) * 5;
        ctx.fillRect(5, -22 + armWave, 3, 10);
        ctx.fillRect(-8, -20, 3, 10);
    } else {
        // Brazos normales
        ctx.fillRect(5, -22, 3, 10);
        ctx.fillRect(-8, -22, 3, 10);
    }

    // Cabeza
    ctx.fillStyle = "#F5D0A9"; // Piel
    ctx.fillRect(-4, -30, 8, 8);

    // Pelo (Estilo random basado en el nombre/hash o género simple)
    ctx.fillStyle = (habitante.genero === "Femenino") ? "#5E3A18" : "#281706";
    if (habitante.genero === "Femenino") {
        ctx.fillRect(-5, -32, 10, 4); // Top
        ctx.fillRect(-5, -32, 2, 10); // Largo
        ctx.fillRect(3, -32, 2, 10);
    } else {
        ctx.fillRect(-4, -32, 8, 3); // Corto
    }

    // Ojos
    ctx.fillStyle = "black";
    ctx.fillRect(-2, -27, 1, 1);
    ctx.fillRect(1, -27, 1, 1);

    // BUBBLES de ACCIÓN
    if (habitante.mensaje) {
        // Globo de chat
        ctx.fillStyle = "white";
        ctx.strokeStyle = "black";
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.roundRect(-15, -55, 30, 20, 5);
        ctx.fill();
        ctx.stroke();

        ctx.fillStyle = "black";
        ctx.font = "bold 12px Arial";
        ctx.textAlign = "center";
        // Si es emoji usalo, si no texto
        ctx.fillText(habitante.mensaje, 0, -41);
    } else if (habitante.accion === "BEBIENDO") {
        ctx.font = "16px Arial";
        ctx.fillText("💧", 0, -40);
    } else if (habitante.accion === "COMER") {
        ctx.font = "16px Arial";
        ctx.fillText("🍔", 0, -40);
    } else if (habitante.accion === "SOCIALIZAR") {
        ctx.font = "16px Arial";
        ctx.fillText("💬", 0, -40);
    } else if (habitante.accion === "DORMIR") {
        ctx.font = "16px Arial";
        ctx.fillText("💤", 0, -40);
    }

    // Nombre
    if (zoom > 0.6) {
        ctx.fillStyle = "white";
        ctx.font = "10px sans-serif";
        ctx.textAlign = "center";

        // Stroke para leer mejor
        ctx.strokeStyle = 'black';
        ctx.lineWidth = 2;
        ctx.strokeText(habitante.nombre, 0, -5);
        ctx.fillText(habitante.nombre, 0, -5);
    }

    ctx.restore();
}

// --- GAME LOOP ---
function loop(timestamp) {
    update(timestamp);
    draw();
    requestAnimationFrame(loop);
}

function update(timestamp) {
    if (timestamp - lastFetch > FETCH_INTERVAL) {
        fetch('/estado')
            .then(res => res.json())
            .then(data => {
                estado = data;
                updateUI(data);
            })
            .catch(err => console.error("Error fetching estado:", err));
        lastFetch = timestamp;
    }
}

function updateUI(data) {
    // Calcular hora (0.0 - 1.0 -> 00:00 - 24:00)
    let hora_dec = data.tiempo.hora_global * 24;
    let hora = Math.floor(hora_dec);
    let min = Math.floor((hora_dec - hora) * 60);
    // Formato HH:MM
    let hh = hora.toString().padStart(2, '0');
    let mm = min.toString().padStart(2, '0');

    document.getElementById('fecha').innerText = `Año ${data.tiempo.anio} | Mes ${data.tiempo.mes} | Día ${data.tiempo.dia} | 🕒 ${hh}:${mm}`;
    document.getElementById('stats').innerText = `Población: ${data.stats.poblacion}`;
    const r = data.stats.recursos;
    document.getElementById('recursos').innerText = `🌲 ${r.madera} | 🪨 ${r.piedra} | 🍎 ${r.comida}`;
}

function draw() {
    // Fondo Ocean
    ctx.fillStyle = '#141432';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    if (!mapa) return; // Esperando mapa

    const zoomTW = TILE_WIDTH * ZOOM_LEVEL;
    const zoomTH = TILE_HEIGHT * ZOOM_LEVEL;

    // 1. Dibujar Mapa
    // Optimización: Solo dibujar lo visible (Culling simple)
    // Por ahora dibujamos todo por simplicidad.
    for (let f = 0; f < mapa.filas; f++) {
        for (let c = 0; c < mapa.columnas; c++) {
            const tile = mapa.mapa[f][c];
            const pos = gridToIso(c, f);

            // Culling básico DESACTIVADO por problemas de visualización en algunos dispositivos
            // if (pos.x < -200 || pos.x > canvas.width + 200 || pos.y < -200 || pos.y > canvas.height + 200) continue;

            const tipo = tile.tipo;
            const altura = tile.altura;
            const capas = (tipo === 'agua') ? 1 : Math.max(1, altura);

            // Dibujar bloque
            const imgName = `bloque_${tipo}`;
            if (images[imgName]) {
                const img = images[imgName];
                // Escalar imagen
                const w = img.width * ZOOM_LEVEL;
                const h = img.height * ZOOM_LEVEL;
                const offX = -zoomTW / 2;

                // Apilar bloques para altura
                const layerOffset = 15 * ZOOM_LEVEL;

                let drawY = pos.y;
                for (let i = 0; i < capas; i++) {
                    ctx.drawImage(img, pos.x + offX, pos.y - (i * layerOffset), w, h);
                    drawY = pos.y - (i * layerOffset);
                }

                // Guardar la Y superior para dibujar objetos encima
                tile._topY = drawY;
                tile._screenX = pos.x;

                // DRAW HOVER
                if (mouseHover && mouseHover.c === c && mouseHover.f === f) {
                    const topOffset = (capas - 1) * layerOffset; // Use highest layer

                    ctx.save();
                    ctx.globalCompositeOperation = 'overlay';
                    ctx.fillStyle = 'rgba(255, 255, 255, 0.3)';
                    // Dibujar rombo aproximado
                    ctx.beginPath();
                    ctx.moveTo(pos.x, pos.y - topOffset); // Top
                    ctx.lineTo(pos.x + zoomTW / 2, pos.y + zoomTH / 2 - topOffset); // Right
                    ctx.lineTo(pos.x, pos.y + zoomTH - topOffset); // Bottom
                    ctx.lineTo(pos.x - zoomTW / 2, pos.y + zoomTH / 2 - topOffset); // Left
                    ctx.closePath();
                    ctx.fill();

                    // Borde
                    ctx.strokeStyle = '#FFFFFF';
                    ctx.lineWidth = 2;
                    ctx.stroke();
                    ctx.restore();
                }
            }
        }
    }

    // 2. Dibujar Recursos (Usamos datos del estado si existen, fallback al mapa estático)
    // El backend envía 'recursos_mapa' en /estado con lo actual.
    if (estado && estado.recursos_mapa) {
        estado.recursos_mapa.forEach(r => {
            const tile = mapa.mapa[r.f][r.c];
            if (!tile) return;

            const imgName = `recurso_${r.tipo}`;
            if (images[imgName]) {
                const img = images[imgName];
                const w = img.width * ZOOM_LEVEL;
                const h = img.height * ZOOM_LEVEL;
                // Centrar
                const x = tile._screenX - w / 2;
                const y = tile._topY - (h * 0.8); // Ajuste visual
                ctx.drawImage(img, x, y, w, h);
            }
        });
    }

    // 3. Dibujar Edificios
    mapa.edificios.forEach(ed => {
        const tile = mapa.mapa[ed.f][ed.c];
        const imgName = `edificio_${ed.tipo}`;
        if (images[imgName] && tile) {
            const img = images[imgName];
            const w = img.width * ZOOM_LEVEL;
            const h = img.height * ZOOM_LEVEL;
            ctx.drawImage(img, tile._screenX - w / 2, tile._topY - h + (10 * ZOOM_LEVEL), w, h);
        }
    });

    // 4. Dibujar Entidades (Habitantes + Animales)
    if (estado) {
        // Animales
        estado.animales.forEach(a => {
            const pos = gridToIso(a.x, a.y);
            // Altura aproximada (lerp de tile actual?)
            // Por ahora usamos la altura del tile int
            const f = Math.round(a.y);
            const c = Math.round(a.x);
            let topY = pos.y;
            if (mapa.mapa[f] && mapa.mapa[f][c]) {
                topY = mapa.mapa[f][c]._topY || pos.y;
            }

            ctx.fillStyle = (a.tipo === 'gallina') ? '#DDAA00' : '#FFFFFF';
            const size = 6 * ZOOM_LEVEL;
            ctx.beginPath();
            ctx.arc(pos.x, topY - size, size, 0, Math.PI * 2);
            ctx.fill();
        });

        // Habitantes
        estado.habitantes.forEach(h => {
            const pos = gridToIso(h.x, h.y);
            const f = Math.round(h.y);
            const c = Math.round(h.x);
            let topY = pos.y;
            if (mapa.mapa[f] && mapa.mapa[f][c]) {
                topY = mapa.mapa[f][c]._topY || pos.y;
            }

            // Renderizar Avatar
            // Coordenada Z aproximada: Los pies están en pos.x, topY.
            // drawAvatar dibuja centrado en X, con Y siendo los pies.

            drawAvatar(ctx, pos.x, topY, h, ZOOM_LEVEL);
        });

        // 5. Overlay Ambiente (Día/Noche)
        // Usamos tiempo.hora_global (0.0 a 1.0)
        const t = estado.tiempo.hora_global;
        let alpha = 0;
        let color = "0,0,0"; // rgb

        if (t < 0.2) { // Amanecer
            alpha = 0.8 * (1 - t / 0.2);
            color = "20,20,40";
        } else if (t > 0.7 && t < 0.8) { // Atardecer
            alpha = 0.3 * ((t - 0.7) / 0.1);
            color = "255,100,0";
        } else if (t >= 0.8) { // Noche
            alpha = 0.85;
            color = "0,0,10";
        }

        if (alpha > 0) {
            ctx.fillStyle = `rgba(${color}, ${alpha})`;
            ctx.fillRect(0, 0, canvas.width, canvas.height);
        }
    }
}

// Iniciar
fetch('/mapa')
    .then(res => res.json())
    .then(data => {
        mapa = data;
        mapDataCache = data;
        loop(0);
    });
