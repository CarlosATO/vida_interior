// --- CONFIGURACIÓN THREE.JS ---
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x87CEEB); // Cielo azul por defecto
scene.fog = new THREE.Fog(0x87CEEB, 10, 50);

const camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 1000);
const renderer = new THREE.WebGLRenderer({ canvas: document.getElementById('gameCanvas'), antialias: true });
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;

// Loader
const gltfLoader = new THREE.GLTFLoader();
const fbxLoader = new THREE.FBXLoader();

// Controles de Cámara (Orbit)
const controls = new THREE.OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.05;
controls.maxPolarAngle = Math.PI / 2 - 0.1; // No bajar del suelo
controls.minDistance = 5;
controls.maxDistance = 50;

// Raycaster
const raycaster = new THREE.Raycaster();
const mouse = new THREE.Vector2();
let followTargetName = null;

window.addEventListener('pointerdown', (event) => {
    mouse.x = (event.clientX / window.innerWidth) * 2 - 1;
    mouse.y = -(event.clientY / window.innerHeight) * 2 + 1;

    raycaster.setFromCamera(mouse, camera);

    const intersects = raycaster.intersectObjects(entitiesGroup.children, true); // Recursive for groups

    if (intersects.length > 0) {
        // Find the root entity group/mesh
        let obj = intersects[0].object;
        while (obj.parent && obj.parent !== entitiesGroup) {
            obj = obj.parent;
        }

        // Find which logical entity this is
        for (const [name, ent] of entities) {
            if (ent.mesh === obj) {
                followTargetName = name;
                console.log("Following:", name);
                break;
            }
        }
    } else {
        // Click on terrain -> stop following (optional, or maybe move there?)
        followTargetName = null;
    }
});

// --- ILUMINACIÓN ---
const hemiLight = new THREE.HemisphereLight(0xffffff, 0x444444, 0.6);
scene.add(hemiLight);

const dirLight = new THREE.DirectionalLight(0xffffff, 0.8);
dirLight.position.set(10, 20, 10);
dirLight.castShadow = true;
dirLight.shadow.camera.top = 20;
dirLight.shadow.camera.bottom = -20;
dirLight.shadow.camera.left = -20;
dirLight.shadow.camera.right = 20;
dirLight.shadow.mapSize.width = 2048;
dirLight.shadow.mapSize.height = 2048;
scene.add(dirLight);

// --- ESTADO DEL JUEGO ---
let mapa = null;
let estado = null;
let lastFetch = 0;
const FETCH_INTERVAL = 100;
const TILE_SIZE = 1;

// Grupos para objetos
const terrainGroup = new THREE.Group();
const entitiesGroup = new THREE.Group();
const propsGroup = new THREE.Group(); // Arboles, rocas, edificios
scene.add(terrainGroup);
scene.add(entitiesGroup);
scene.add(propsGroup);

// Cache de Modelos 
const models = {};
const loadModel = (name, path, scale = 1.0) => {
    const ext = path.split('.').pop().toLowerCase();
    const loader = (ext === 'fbx') ? fbxLoader : gltfLoader;

    loader.load(path, (obj) => {
        // GLTF returns { scene: ... }, FBX returns Group directly
        const model = (ext === 'glb' || ext === 'gltf') ? obj.scene : obj;

        model.traverse(c => {
            if (c.isMesh) {
                c.castShadow = true;
                c.receiveShadow = true;
            }
        });

        model.scale.set(scale, scale, scale);

        // Fix FBX rotation if needed (often needed)
        // if(ext === 'fbx') model.rotation.y = Math.PI;

        models[name] = model;
        console.log(`Loaded ${name}`);
    }, undefined, (err) => console.log(`Failed to load ${name} (${path}):`, err));
};

// Intentar cargar modelos
loadModel('tree', '/assets/models/tree.glb');
loadModel('rock', '/assets/models/rock.glb');
loadModel('human', '/assets/models/human.fbx', 0.015); // Adjust scale for FBX (Kenney chars roughly ~1-2m but units vary)
loadModel('house', '/assets/models/house.glb');

// Modelos Interp
const entities = new Map(); // Mapa de instancias de Entidad3D

// --- CLASES ---
class Entidad3D {
    constructor(data) {
        this.mesh = this.createMesh(data);
        this.mesh.castShadow = true;
        entitiesGroup.add(this.mesh);

        this.update(data, true);
    }

    createMesh(data) {
        // 1. Try GLTF
        if (models['human']) {
            const clone = models['human'].clone();
            // Colorize if possible (mesh name specific) or just scale
            return clone;
        }

        // 2. Fallback Procedural
        const group = new THREE.Group();

        // Cuerpo
        const geometry = new THREE.CapsuleGeometry(0.25, 0.7, 4, 8);
        const material = new THREE.MeshStandardMaterial({ color: data.color_cuerpo || 0xffffff });
        const body = new THREE.Mesh(geometry, material);
        body.position.y = 0.5;
        body.castShadow = true;
        group.add(body);

        // Cabeza
        const headGeo = new THREE.SphereGeometry(0.2, 8, 8);
        const headMat = new THREE.MeshStandardMaterial({ color: 0xffccaa });
        const head = new THREE.Mesh(headGeo, headMat);
        head.position.y = 1.0;
        head.castShadow = true;
        group.add(head);

        // Brazos (Simples)
        const armGeo = new THREE.BoxGeometry(0.1, 0.4, 0.1);
        const armMat = new THREE.MeshStandardMaterial({ color: data.color_cuerpo || 0xffffff });
        const leftArm = new THREE.Mesh(armGeo, armMat);
        leftArm.position.set(-0.3, 0.6, 0);
        group.add(leftArm);
        const rightArm = new THREE.Mesh(armGeo, armMat);
        rightArm.position.set(0.3, 0.6, 0);
        group.add(rightArm);

        return group;
    }

    update(data, instant = false) {
        this.data = data;
        this.targetX = data.x * TILE_SIZE;
        this.targetZ = data.y * TILE_SIZE; // Y en 2D es Z en 3D

        // Altura del terreno en esa posición
        this.targetY = getTerrainHeight(data.x, data.y);

        if (instant) {
            this.mesh.position.set(this.targetX, this.targetY + 0.7, this.targetZ);
        }
    }

    lerp() {
        if (!this.mesh) return;
        const speed = 0.1;
        this.mesh.position.x += (this.targetX - this.mesh.position.x) * speed;
        this.mesh.position.z += (this.targetZ - this.mesh.position.z) * speed;
        this.mesh.position.y += (this.targetY + 0.7 - this.mesh.position.y) * speed;

        // Rotación hacia el movimiento
        const dx = this.targetX - this.mesh.position.x;
        const dz = this.targetZ - this.mesh.position.z;
        if (Math.abs(dx) > 0.01 || Math.abs(dz) > 0.01) {
            this.mesh.rotation.y = Math.atan2(dx, dz);
        }

        // Acciones visuales (Dormir)
        if (this.data.accion === "DORMIR") {
            this.mesh.rotation.x = -Math.PI / 2;
            this.mesh.position.y = this.targetY + 0.2;
        } else {
            this.mesh.rotation.x = 0;
        }
    }

    dispose() {
        entitiesGroup.remove(this.mesh);
    }
}

// --- FUNCIONES ---
function getTerrainHeight(col, fila) {
    if (!mapa) return 0;
    // Simple lookup integer, interpolación bilineal idealmente
    const c = Math.round(col);
    const f = Math.round(fila);
    if (mapa.mapa[f] && mapa.mapa[f][c]) {
        // Altura base del tile logicamente es mapa[f][c].altura
        // Asumimos altura visual = altura logica * step
        return mapa.mapa[f][c].altura * 0.5;
    }
    return 0;
}

function generateTerrain(data) {
    // Limpiar anterior
    while (terrainGroup.children.length > 0) {
        terrainGroup.remove(terrainGroup.children[0]);
    }
    while (propsGroup.children.length > 0) {
        propsGroup.remove(propsGroup.children[0]);
    }

    // Geometría instanciada sería mejor, pero por simplicidad usaremos cubos/planos simples
    data.mapa.forEach((fila, f) => {
        fila.forEach((tile, c) => {
            const h = tile.altura * 0.5;
            const geometry = new THREE.BoxGeometry(TILE_SIZE, Math.max(0.1, h + 1), TILE_SIZE); // +1 base

            let color = 0x228822; // Pasto
            if (tile.tipo === 'agua') color = 0x2244aa;
            else if (tile.tipo === 'arena') color = 0xeedd88;
            else if (tile.tipo === 'piedra') color = 0x888888;

            const material = new THREE.MeshStandardMaterial({ color: color });
            const mesh = new THREE.Mesh(geometry, material);

            mesh.position.set(c * TILE_SIZE, h / 2, f * TILE_SIZE); // Centrado
            mesh.receiveShadow = true;

            terrainGroup.add(mesh);

            // --- PROPS PROCEDURALES ---
            // Recursos estáticos visuales (Solo visual por ahora, idealmente vendrían del backend)
            // Usamos ruido determinista
            const seed = (c * 13 + f * 37) % 100;

            if (tile.tipo === 'pasto' && seed < 15) {
                // Árbol con variación
                createTree(c * TILE_SIZE, h + 0.5, f * TILE_SIZE);
            } else if (tile.tipo === 'piedra' && seed < 20) {
                // Roca
                createRock(c * TILE_SIZE, h + 0.5, f * TILE_SIZE);
            }
        });
    });

    // Edificios
    if (data.edificios) {
        data.edificios.forEach(edificio => {
            const h = getTerrainHeight(edificio.c, edificio.f); // Altura suelo
            createBuilding(edificio.c * TILE_SIZE, h + 0.5, edificio.f * TILE_SIZE, edificio.tipo);
        });
    }

    // Ajustar cámara
    camera.position.set(data.columnas / 2, 20, data.filas + 10);
    controls.target.set(data.columnas / 2, 0, data.filas / 2);
}

function createTree(x, y, z) {
    if (models['tree']) {
        const clone = models['tree'].clone();
        // Randomize placement slightly
        const offsetX = (Math.random() - 0.5) * 0.5;
        const offsetZ = (Math.random() - 0.5) * 0.5;
        const scale = 0.8 + Math.random() * 0.4;

        clone.position.set(x + offsetX, y, z + offsetZ);
        clone.rotation.y = Math.random() * Math.PI * 2;
        clone.scale.set(scale, scale, scale);

        propsGroup.add(clone);
        return;
    }

    // Procedural Tree
    const trunkGeo = new THREE.CylinderGeometry(0.1, 0.15, 0.8, 6);
    const trunkMat = new THREE.MeshStandardMaterial({ color: 0x553311 });
    const trunk = new THREE.Mesh(trunkGeo, trunkMat);
    trunk.position.set(x, y, z);
    trunk.castShadow = true;
    propsGroup.add(trunk);

    const leavesGeo = new THREE.ConeGeometry(0.6, 1.5, 6);
    const leavesMat = new THREE.MeshStandardMaterial({ color: 0x228822 });
    const leaves = new THREE.Mesh(leavesGeo, leavesMat);
    leaves.position.set(x, y + 0.8, z);
    leaves.castShadow = true;
    propsGroup.add(leaves);
}

function createRock(x, y, z) {
    if (models['rock']) {
        const clone = models['rock'].clone();
        // Force scale down in case it's huge
        clone.scale.set(0.3, 0.3, 0.3);
        clone.rotation.y = Math.random() * Math.PI;
        clone.position.set(x, y, z);
        propsGroup.add(clone);
        return;
    }

    const geo = new THREE.DodecahedronGeometry(0.3, 0);
    const mat = new THREE.MeshStandardMaterial({ color: 0x777777 });
    const rock = new THREE.Mesh(geo, mat);
    rock.position.set(x, y - 0.1, z);
    rock.castShadow = true;
    propsGroup.add(rock);
}

function createBuilding(x, y, z, type) {
    if (models['house']) {
        const clone = models['house'].clone();
        clone.position.set(x, y, z);
        propsGroup.add(clone);
        return;
    }

    // Fallback House
    const geo = new THREE.BoxGeometry(1, 1, 1);
    const mat = new THREE.MeshStandardMaterial({ color: 0x885522 });
    const house = new THREE.Mesh(geo, mat);
    house.position.set(x, y + 0.5, z);

    const roofGeo = new THREE.ConeGeometry(0.8, 0.5, 4);
    const roofMat = new THREE.MeshStandardMaterial({ color: 0xaa2222 });
    const roof = new THREE.Mesh(roofGeo, roofMat);
    roof.position.y = 0.75;
    roof.rotation.y = Math.PI / 4;
    house.add(roof);

    house.castShadow = true;
    propsGroup.add(house);
}

// --- LOOP ---
function update() {
    requestAnimationFrame(update);

    const now = Date.now();
    controls.update();

    // Fetch Estado
    if (now - lastFetch > FETCH_INTERVAL) {
        fetch('/estado')
            .then(res => res.json())
            .then(data => {
                estado = data;
                updateUI(data);

                // Sync Habitantes
                const currentNames = new Set(data.habitantes.map(h => h.nombre));

                // Update or Create
                data.habitantes.forEach(h => {
                    if (entities.has(h.nombre)) {
                        entities.get(h.nombre).update(h);
                    } else {
                        entities.set(h.nombre, new Entidad3D(h));
                    }
                });

                // Remove dead
                for (const [name, ent] of entities) {
                    if (!currentNames.has(name)) {
                        ent.dispose();
                        entities.delete(name);
                    }
                }

                // Ciclo Día/Noche visual
                const time = data.tiempo.hora_global; // 0.0 - 1.0
                // Sol rota alrededor Z
                const angle = (time - 0.25) * Math.PI * 2; // Amanecer a las 6
                dirLight.position.set(Math.cos(angle) * 20, Math.sin(angle) * 20, 10);

                // Color cielo
                if (time < 0.2 || time > 0.8) scene.background.setHex(0x050510);
                else scene.background.setHex(0x87CEEB);
                scene.fog.color.copy(scene.background);

            })
            .catch(err => console.error(err));
        lastFetch = now;
    }

    // Interpolate
    entities.forEach(ent => ent.lerp());

    // Follow Camera
    if (followTargetName && entities.has(followTargetName)) {
        const ent = entities.get(followTargetName);
        if (ent.mesh) {
            const targetPos = ent.mesh.position;

            // Move camera to keep relative offset? Or just lookAt?
            // "RTS style follow": Update controls.target
            const offset = new THREE.Vector3().subVectors(camera.position, controls.target);
            controls.target.copy(targetPos);
            camera.position.addVectors(targetPos, offset);
        }
    } else {
        followTargetName = null;
    }

    renderer.render(scene, camera);
}

function updateUI(data) {
    if (!data) return;
    // Calcular hora (0.0 - 1.0 -> 00:00 - 24:00)
    let hora_dec = data.tiempo.hora_global * 24;
    let hora = Math.floor(hora_dec);
    let min = Math.floor((hora_dec - hora) * 60);
    let hh = hora.toString().padStart(2, '0');
    let mm = min.toString().padStart(2, '0');

    document.getElementById('fecha').innerText = `Año ${data.tiempo.anio} | Mes ${data.tiempo.mes} | Día ${data.tiempo.dia} | 🕒 ${hh}:${mm}`;
    document.getElementById('stats').innerText = `Población: ${data.stats.poblacion}`;
    const r = data.stats.recursos;
    document.getElementById('recursos').innerText = `🌲 ${r.madera} | 🪨 ${r.piedra} | 🍎 ${r.comida}`;
}

// --- DEBUG UI ---
function showError(msg) {
    console.error(msg);
    const errDiv = document.createElement('div');
    errDiv.style.position = 'absolute';
    errDiv.style.top = '50%';
    errDiv.style.left = '50%';
    errDiv.style.transform = 'translate(-50%, -50%)';
    errDiv.style.backgroundColor = 'rgba(255, 0, 0, 0.8)';
    errDiv.style.color = 'white';
    errDiv.style.padding = '20px';
    errDiv.style.borderRadius = '10px';
    errDiv.style.zIndex = '9999';
    errDiv.style.maxWidth = '80%';
    errDiv.innerText = "ERROR: " + msg;
    document.body.appendChild(errDiv);
}

// Init
try {
    fetch('/mapa')
        .then(res => {
            if (!res.ok) throw new Error(`HTTP ${res.status} - ${res.statusText}`);
            return res.json();
        })
        .then(data => {
            mapa = data;
            try {
                generateTerrain(data);
                update();
            } catch (e) {
                showError("Terrain Gen Error: " + e.message);
            }
        })
        .catch(err => {
            showError("Map Fetch Error: " + err.message);
        });

    window.addEventListener('resize', () => {
        camera.aspect = window.innerWidth / window.innerHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(window.innerWidth, window.innerHeight);
    });
} catch (e) {
    showError("Global Init Error: " + e.message);
}
