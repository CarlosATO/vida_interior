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

// --- SISTEMA DE ANIMACIÓN ---
const entities = new Map(); // Mapa de instancias de Inhabitant interp
const particles = [];
class Particle {
    constructor(x, y, color, type = 'smoke') {
        this.x = x; this.y = y;
        this.vx = (Math.random() - 0.5) * 2;
        this.vy = -(Math.random() * 2);
        this.life = 1.0;
        this.color = color;
        this.type = type;
    }
    update() {
        this.x += this.vx; this.y += this.vy;
        this.life -= 0.02;
    }
    draw(ctx) {
        ctx.globalAlpha = this.life;
        ctx.fillStyle = this.color;
        if (this.type === 'zzz') {
            ctx.font = "bold 14px Arial";
            ctx.fillText("Z", this.x, this.y);
        } else if (this.type === 'heart') {
            ctx.fillText("❤️", this.x, this.y);
        } else {
            ctx.beginPath();
            ctx.arc(this.x, this.y, 3 * this.life, 0, Math.PI * 2);
            ctx.fill();
        }
        ctx.globalAlpha = 1.0;
    }
}

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
let followTarget = null; // habitante.nombre to follow

canvas.addEventListener('wheel', e => {
    e.preventDefault();
    followTarget = null; // Un-follow on manual pan/zoom

    if (e.ctrlKey || e.metaKey) {
        const zoomSpeed = 0.001;
        ZOOM_LEVEL -= e.deltaY * zoomSpeed;
        if (ZOOM_LEVEL < 0.2) ZOOM_LEVEL = 0.2;
        if (ZOOM_LEVEL > 3.0) ZOOM_LEVEL = 3.0;
    } else {
        OFFSET_X -= e.deltaX;
        OFFSET_Y -= e.deltaY;
    }
});

canvas.addEventListener('click', e => {
    // Si cliqueamos a alguien, lo seguimos
    if (mouseHover && estado) {
        const clickedHab = estado.habitantes.find(h => Math.round(h.x) === mouseHover.c && Math.round(h.y) === mouseHover.f);
        if (clickedHab) {
            followTarget = clickedHab.nombre;
            console.log("Following:", followTarget);
        }
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

function spawnParticles(x, y, type) {
    if (type === 'smoke') {
        for (let i = 0; i < 2; i++) particles.push(new Particle(x, y - 10, '#888'));
    } else if (type === 'zzz') {
        if (Math.random() < 0.05) particles.push(new Particle(x + 5, y - 20, '#fff', 'zzz'));
    } else if (type === 'heart') {
        if (Math.random() < 0.1) particles.push(new Particle(x, y - 25, '#f44', 'heart'));
    } else if (type === 'spark') {
        for (let i = 0; i < 3; i++) particles.push(new Particle(x, y - 15, '#ff0', 'spark'));
    }
}

class InhabitantInterp {
    constructor(data) {
        this.update(data);
        this.renderX = data.x;
        this.renderY = data.y;
    }
    update(data) {
        this.targetX = data.x;
        this.targetY = data.y;
        this.data = data;
    }
    lerp() {
        const speed = 0.15; // Velocidad de interpolación
        this.renderX += (this.targetX - this.renderX) * speed;
        this.renderY += (this.targetY - this.renderY) * speed;

        // Efectos por estado
        if (this.data.accion === "DORMIR") spawnParticles(...this.getScreenCoords(), 'zzz');
        if (this.data.accion === "CONSTRUIR" || this.data.accion === "COCINAR") spawnParticles(...this.getScreenCoords(), 'smoke');
        if (this.data.mensaje === "❤️") spawnParticles(...this.getScreenCoords(), 'heart');
    }
    getScreenCoords() {
        const iso = gridToIso(this.renderX, this.renderY);
        // Ajuste de altura por tile
        const f = Math.round(this.renderY);
        const c = Math.round(this.renderX);
        let y = iso.y;
        if (mapa && mapa.mapa[f] && mapa.mapa[f][c]) y = mapa.mapa[f][c]._topY || iso.y;
        return [iso.x, y];
    }
    draw(ctx) {
        const [x, y] = this.getScreenCoords();

        ctx.save();
        if (this.data.accion === "DORMIR") {
            ctx.translate(x, y);
            ctx.rotate(Math.PI / 2); // Tumbado
            drawAvatar(ctx, 0, 0, this.data, ZOOM_LEVEL);
        } else {
            drawAvatar(ctx, x, y, this.data, ZOOM_LEVEL);
        }
        ctx.restore();
    }
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

                // Actualizar entidades interp
                data.habitantes.forEach(h => {
                    if (!entities.has(h.nombre)) entities.set(h.nombre, new InhabitantInterp(h));
                    else entities.get(h.nombre).update(h);
                });
                // Limpiar muertos
                for (let [name, _] of entities) {
                    if (!data.habitantes.find(h => h.nombre === name)) entities.delete(name);
                }

                // FOLLOW CAMERA
                if (followTarget && entities.has(followTarget)) {
                    const h = entities.get(followTarget);
                    const iso = gridToIso(h.renderX, h.renderY);
                    // Queremos que iso.x sea CW/2 y iso.y sea CH/2
                    // iso.x = valX + OFFSET_X -> OFFSET_X = CW/2 - valX
                    const zoomTW = TILE_WIDTH * ZOOM_LEVEL;
                    const zoomTH = TILE_HEIGHT * ZOOM_LEVEL;
                    const valX = (h.renderX - h.renderY) * (zoomTW / 2);
                    const valY = (h.renderX + h.renderY) * (zoomTH / 2);

                    OFFSET_X += ((canvas.width / 2 - valX) - OFFSET_X) * 0.1;
                    OFFSET_Y += ((canvas.height / 2 - valY) - OFFSET_Y) * 0.1;
                }
            })
            .catch(err => console.error("Error fetching estado:", err));
        lastFetch = timestamp;
    }

    // Update particles
    for (let i = particles.length - 1; i >= 0; i--) {
        particles[i].update();
        if (particles[i].life <= 0) particles.splice(i, 1);
    }
    // Update interp
    for (let h of entities.values()) h.lerp();

    // Check bitacora update
    if (typeof checkBitacora === "function") {
        checkBitacora(timestamp);
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

                // DIBUJAR RUIDO AMBIENTAL (Césped, piedras deterministas)
                if (tipo === 'pasto' || tipo === 'arena') {
                    const seed = (c * 7 + f * 13) % 100;
                    if (seed < 30) {
                        ctx.fillStyle = tipo === 'pasto' ? "rgba(20,50,20,0.15)" : "rgba(50,50,40,0.1)";
                        ctx.beginPath();
                        const noiseX = pos.x + (seed % 10 - 5) * ZOOM_LEVEL;
                        const noiseY = drawY + zoomTH / 2 + (seed % 5 - 2) * ZOOM_LEVEL;
                        ctx.arc(noiseX, noiseY, (seed % 3 + 1) * ZOOM_LEVEL, 0, Math.PI * 2);
                        ctx.fill();
                    }
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

        if (alpha > 0) {
            ctx.fillStyle = `rgba(${color}, ${alpha})`;
            ctx.fillRect(0, 0, canvas.width, canvas.height);
        }

        // 6. DIBUJAR ENTIDADES INTERPOLADAS
        for (let h of entities.values()) h.draw(ctx);

        // 7. DIBUJAR PARTÍCULAS
        particles.forEach(p => p.draw(ctx));

        // 8. EFECTO VIÑETA & POST (Vibrancia)
        const grd = ctx.createRadialGradient(canvas.width / 2, canvas.height / 2, 0, canvas.width / 2, canvas.height / 2, canvas.width * 0.8);
        grd.addColorStop(0, "rgba(0,0,0,0)");
        grd.addColorStop(1, "rgba(0,0,0,0.4)");
        ctx.fillStyle = grd;
        ctx.fillRect(0, 0, canvas.width, canvas.height);
    }
}

// Iniciar
fetch('/mapa')
    .then(res => res.json())
    .then(data => {
        mapa = data;
        mapDataCache = data;

        // Auto-focus camera
        centerCameraOnEntity();

        loop(0);
    });

function centerCameraOnEntity() {
    // 1. Try to find the "centro" building
    let targetX = 0;
    let targetY = 0;
    let found = false;

    // Search in buildings
    if (mapa && mapa.edificios) {
        for (const ed of mapa.edificios) {
            if (ed.tipo === 'centro') {
                targetX = ed.c;
                targetY = ed.f;
                found = true;
                break;
            }
        }
    }

    // 2. If no center, try first inhabitant (if state is loaded, but map loads first usually)
    // Since map loads before state loop, we might need to rely on map.edificios or wait for first state update.
    // Ensure we have a valid target from map first.

    if (found) {
        const iso = gridToIso(targetX, targetY);
        // Center screen: Width/2, Height/2
        // iso.x = (c-f)*W/2 + OFFX
        // iso.y = (c+f)*H/2 + OFFY
        // We want iso.x, iso.y to be somewhere specific? No, we want the drawing to end up at center.
        // render x = iso.x
        // render y = iso.y

        // We want iso.x = CanvasWidth / 2
        // We want iso.y = CanvasHeight / 2

        // current_iso_x = val + OFFX
        // target_iso_x = val + NEW_OFFX = CW/2
        // NEW_OFFX = CW/2 - val

        // Calculate "val" (isometric position without offset)
        const zoomTW = TILE_WIDTH * ZOOM_LEVEL;
        const zoomTH = TILE_HEIGHT * ZOOM_LEVEL;

        const valX = (targetX - targetY) * (zoomTW / 2);
        const valY = (targetX + targetY) * (zoomTH / 2);

        OFFSET_X = (canvas.width / 2) - valX;
        OFFSET_Y = (canvas.height / 2) - valY;

        console.log(`Camera centered on ${targetX}, ${targetY}`);
    }
}
// --- BITÁCORA LOGIC ---
let showingBitacora = false;
let lastBitacoraFetch = 0;

window.toggleBitacora = function () {
    showingBitacora = !showingBitacora;
    const panel = document.getElementById("bitacora-panel");
    panel.style.display = showingBitacora ? "block" : "none";

    if (showingBitacora) {
        fetchBitacora();
    }
}

function fetchBitacora() {
    fetch('/bitacora')
        .then(res => res.json())
        .then(data => {
            renderBitacora(data);
        })
        .catch(err => console.error("Error bitacora:", err));
}

function renderBitacora(logs) {
    const list = document.getElementById("log-list");
    if (!logs || logs.length === 0) {
        list.innerHTML = "<div style='color:#666'>Sin eventos recientes.</div>";
        return;
    }

    let html = "";
    for (let log of logs) {
        // Safe check for type
        let typeClass = log.tipo ? `type-${log.tipo}` : 'type-info';
        html += `
            <div class="log-entry ${typeClass}">
                <div class="log-fecha">${log.fecha}</div>
                <div class="log-msg">${log.mensaje}</div>
            </div>
        `;
    }
    list.innerHTML = html;
}

// Hook into update loop
// We need to call checkBitacora(timestamp) inside update()
function checkBitacora(timestamp) {
    if (showingBitacora && timestamp - lastBitacoraFetch > 2000) { // Update every 2s
        fetchBitacora();
        lastBitacoraFetch = timestamp;
    }
}
