import * as THREE from 'three';
import { OrbitControls }   from 'three/addons/controls/OrbitControls.js';
import { EffectComposer }  from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass }      from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';

// ── DOM refs ────────────────────────────────────────────────────────────────
const container = document.getElementById('canvas-container');
const countEl   = document.getElementById('count');
const durEl     = document.getElementById('duration');
const statusEl  = document.getElementById('status');
const runBtn    = document.getElementById('run-btn');
const fillA     = document.getElementById('fill-a');
const fillB     = document.getElementById('fill-b');
const valA      = document.getElementById('val-a');
const valB      = document.getElementById('val-b');
const mEls      = [1,2,3,4,5].map(i => document.getElementById('m'+i));

// ── Renderer ────────────────────────────────────────────────────────────────
const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setPixelRatio(window.devicePixelRatio);
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.0;
container.appendChild(renderer.domElement);

// ── Scene & camera ──────────────────────────────────────────────────────────
const scene  = new THREE.Scene();
scene.background = new THREE.Color(0x050508);
scene.fog = new THREE.Fog(0x050508, 12, 30);

const camera = new THREE.PerspectiveCamera(50, window.innerWidth / window.innerHeight, 0.01, 100);
camera.position.set(4.5, 3.5, 3.5);

// ── Controls ────────────────────────────────────────────────────────────────
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping  = true;
controls.dampingFactor  = 0.05;
controls.autoRotate     = true;
controls.autoRotateSpeed = 0.6;

// ── Post-processing: bloom ──────────────────────────────────────────────────
const composer = new EffectComposer(renderer);
composer.addPass(new RenderPass(scene, camera));
const bloom = new UnrealBloomPass(
    new THREE.Vector2(window.innerWidth, window.innerHeight),
    1.6,   // strength
    0.5,   // radius
    0.04   // threshold — very low so vivid colours bloom
);
composer.addPass(bloom);

// ── Resize ──────────────────────────────────────────────────────────────────
window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
    composer.setSize(window.innerWidth, window.innerHeight);
});

// ── Grid ────────────────────────────────────────────────────────────────────
const grid = new THREE.GridHelper(14, 28, 0x0a0a20, 0x0a0a20);
grid.position.y = -0.5;
scene.add(grid);

// ── Axes helper (small) ──────────────────────────────────────────────────────
const axes = new THREE.AxesHelper(0.4);
axes.position.set(-0.1, -0.48, -0.1);
scene.add(axes);

// ── State ────────────────────────────────────────────────────────────────────
let allPoints  = [];
let maxA = 1, maxB = 1;
let trajMesh   = null;
let scanIndex  = 0;

// Scanner dot
const dotGeo  = new THREE.SphereGeometry(0.035, 12, 12);
const dotMat  = new THREE.MeshBasicMaterial({ color: 0xffffff });
const dot     = new THREE.Mesh(dotGeo, dotMat);
const dotLight = new THREE.PointLight(0xffffff, 3, 1.2);
dot.add(dotLight);
scene.add(dot);
dot.visible = false;

// ── Colour helper: cyan (#00e5ff) → magenta (#ff00aa) ───────────────────────
function tiltColor(t) {
    // t in [0,1]: 0 = low tilt (cyan), 1 = high tilt (magenta)
    return [
        t,                    // R: 0→1
        0.05 * (1 - t),       // G: near zero
        1.0 - t               // B: 1→0
    ];
    // Results in colours that bloom vividly: cyan at low tilt, magenta at high
}

// ── Build trajectory geometry ────────────────────────────────────────────────
function buildTrajectory(data) {
    if (trajMesh) {
        scene.remove(trajMesh);
        trajMesh.geometry.dispose();
        trajMesh.material.dispose();
    }

    const pts = data.points;
    allPoints  = pts;

    const positions = new Float32Array(pts.length * 3);
    const colors    = new Float32Array(pts.length * 3);

    maxA = 1; maxB = 1;
    for (const p of pts) { maxA = Math.max(maxA, Math.abs(p.a)); maxB = Math.max(maxB, Math.abs(p.b)); }
    const maxTilt = Math.max(1, ...pts.map(p => Math.hypot(p.a, p.b)));

    for (let i = 0; i < pts.length; i++) {
        const p = pts[i];
        positions[i * 3]     = p.x;
        positions[i * 3 + 1] = p.y;
        positions[i * 3 + 2] = p.z;
        const t = Math.hypot(p.a, p.b) / maxTilt;
        const [r, g, b] = tiltColor(t);
        colors[i * 3]     = r;
        colors[i * 3 + 1] = g;
        colors[i * 3 + 2] = b;
    }

    const geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    geo.setAttribute('color',    new THREE.BufferAttribute(colors, 3));
    trajMesh = new THREE.Line(geo, new THREE.LineBasicMaterial({ vertexColors: true }));
    scene.add(trajMesh);

    dot.visible = true;
    scanIndex   = 0;

    countEl.textContent = data.meta.count.toLocaleString();
    durEl.textContent   = data.meta.duration_us.toLocaleString();
}

// ── Update panel with current scan point ────────────────────────────────────
function updatePanel(p) {
    valA.textContent = p.a.toFixed(1) + '°';
    valB.textContent = p.b.toFixed(1) + '°';
    fillA.style.width = Math.min(100, Math.abs(p.a) / maxA * 100) + '%';
    fillB.style.width = Math.min(100, Math.abs(p.b) / maxB * 100) + '%';
    mEls[0].textContent = p.m1;
    mEls[1].textContent = p.m2;
    mEls[2].textContent = p.m3;
    mEls[3].textContent = p.m4;
    mEls[4].textContent = p.m5;
}

// ── Load trajectory ──────────────────────────────────────────────────────────
async function loadTrajectory() {
    try {
        const res = await fetch('/api/trajectory');
        if (!res.ok) { statusEl.textContent = 'AWAITING ENGINE RUN'; return; }
        buildTrajectory(await res.json());
        statusEl.textContent = '';
    } catch (e) {
        statusEl.textContent = 'ERROR: ' + e.message;
    }
}

runBtn.addEventListener('click', async () => {
    runBtn.disabled = true;
    statusEl.textContent = 'COMPUTING…';
    try {
        const res = await fetch('/api/run', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ input: 'data/sample_path.csv', density: 100 }),
        });
        if (!res.ok) {
            const err = await res.json();
            statusEl.textContent = 'ERR: ' + (err.detail ?? res.status);
        } else {
            await loadTrajectory();
        }
    } catch (e) {
        statusEl.textContent = 'ERR: ' + e.message;
    } finally {
        runBtn.disabled = false;
    }
});

// ── Render loop ──────────────────────────────────────────────────────────────
(function animate() {
    requestAnimationFrame(animate);
    controls.update();

    if (allPoints.length > 0) {
        scanIndex = (scanIndex + 4) % allPoints.length;
        const p   = allPoints[scanIndex];
        dot.position.set(p.x, p.y, p.z);
        updatePanel(p);
    }

    composer.render();
})();

loadTrajectory();
