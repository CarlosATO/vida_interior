const canvas = document.getElementById('gameCanvas');
const ctx = canvas.getContext('2d');

// Configuración
const TILE_WIDTH = 64;
const TILE_HEIGHT = 32;
let OFFSET_X = window.innerWidth / 2;
let OFFSET_Y = 100;
let ZOOM_LEVEL = 1.0;

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
    isDragging = true;
    lastMouseX = e.clientX;
    lastMouseY = e.clientY;
});

window.addEventListener('mouseup', () => isDragging = false);

canvas.addEventListener('mousemove', e => {
    if (isDragging) {
        OFFSET_X += e.clientX - lastMouseX;
        OFFSET_Y += e.clientY - lastMouseY;
        lastMouseX = e.clientX;
        lastMouseY = e.clientY;
    }
});

canvas.addEventListener('wheel', e => {
    e.preventDefault();
    const zoomSpeed = 0.001;
    ZOOM_LEVEL -= e.deltaY * zoomSpeed;
    if (ZOOM_LEVEL < 0.2) ZOOM_LEVEL = 0.2;
    if (ZOOM_LEVEL > 3.0) ZOOM_LEVEL = 3.0;
});

// --- FUNCIONES ISOMÉTRICAS ---
function gridToIso(col, fila) {
    const x = (col - fila) * (TILE_WIDTH * ZOOM_LEVEL / 2) + OFFSET_X;
    const y = (col + fila) * (TILE_HEIGHT * ZOOM_LEVEL / 2) + OFFSET_Y;
    return { x, y };
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
    document.getElementById('fecha').innerText = `Año ${data.tiempo.anio} | Mes ${data.tiempo.mes} | Día ${data.tiempo.dia}`;
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

            // Culling básico
            if (pos.x < -200 || pos.x > canvas.width + 200 || pos.y < -200 || pos.y > canvas.height + 200) continue;

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

            // Cuerpo
            const w = 14 * ZOOM_LEVEL;
            const height = 35 * ZOOM_LEVEL;
            ctx.fillStyle = h.color;
            ctx.fillRect(pos.x - w / 2, topY - height, w, height);

            // Nombre
            if (ZOOM_LEVEL > 0.8) {
                ctx.fillStyle = 'white';
                ctx.font = `${10 * ZOOM_LEVEL}px Arial`;
                ctx.textAlign = 'center';
                ctx.fillText(h.nombre, pos.x, topY - height - 5);
            }

            // Bocadillo
            if (h.mensaje) {
                ctx.fillStyle = 'white';
                ctx.fillRect(pos.x - 15, topY - height - 30, 30, 20);
                ctx.fillStyle = 'black';
                ctx.font = '12px Arial';
                ctx.fillText(h.mensaje, pos.x, topY - height - 16);
            }
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
        loop(0);
    });
