import * as THREE from 'https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js';
import { OrbitControls } from 'https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/controls/OrbitControls.js';

const container = document.getElementById('canvas-container');
const countEl   = document.getElementById('count');
const durEl     = document.getElementById('duration');
const statusEl  = document.getElementById('status');
const runBtn    = document.getElementById('run-btn');

// Scene
const scene    = new THREE.Scene();
scene.background = new THREE.Color(0x08080f);

const camera = new THREE.PerspectiveCamera(55, window.innerWidth / window.innerHeight, 0.001, 500);
camera.position.set(3, 2, 5);

const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setPixelRatio(window.devicePixelRatio);
renderer.setSize(window.innerWidth, window.innerHeight);
container.appendChild(renderer.domElement);

const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.06;

window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
});

// Faint reference grid
scene.add(new THREE.GridHelper(10, 20, 0x111133, 0x111133));

// Trajectory
let trajLine = null;

function buildTrajectory(data) {
    if (trajLine) {
        scene.remove(trajLine);
        trajLine.geometry.dispose();
        trajLine.material.dispose();
    }

    const pts = data.points;
    const positions = new Float32Array(pts.length * 3);
    const colors    = new Float32Array(pts.length * 3);

    let maxTilt = 0;
    for (const p of pts) maxTilt = Math.max(maxTilt, Math.hypot(p.a, p.b));

    for (let i = 0; i < pts.length; i++) {
        const p = pts[i];
        positions[i * 3]     = p.x;
        positions[i * 3 + 1] = p.y;
        positions[i * 3 + 2] = p.z;
        const t = maxTilt > 0 ? Math.hypot(p.a, p.b) / maxTilt : 0;
        colors[i * 3]     = t;          // R: high tilt → red
        colors[i * 3 + 1] = 0.1;
        colors[i * 3 + 2] = 1.0 - t;   // B: low tilt → blue
    }

    const geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    geo.setAttribute('color',    new THREE.BufferAttribute(colors, 3));
    const mat = new THREE.LineBasicMaterial({ vertexColors: true });
    trajLine = new THREE.Line(geo, mat);
    scene.add(trajLine);

    countEl.textContent = data.meta.count.toLocaleString();
    durEl.textContent   = data.meta.duration_us.toLocaleString();
}

async function loadTrajectory() {
    try {
        const res = await fetch('/api/trajectory');
        if (!res.ok) {
            statusEl.textContent = 'No trajectory — click RUN ENGINE';
            return;
        }
        buildTrajectory(await res.json());
        statusEl.textContent = '';
    } catch (e) {
        statusEl.textContent = 'Load error: ' + e.message;
    }
}

runBtn.addEventListener('click', async () => {
    runBtn.disabled = true;
    statusEl.textContent = 'Running engine…';
    try {
        const res = await fetch('/api/run', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ input: 'data/sample_path.csv', density: 100 }),
        });
        if (!res.ok) {
            const err = await res.json();
            statusEl.textContent = 'Engine error: ' + (err.detail ?? res.status);
        } else {
            await loadTrajectory();
        }
    } catch (e) {
        statusEl.textContent = 'Request failed: ' + e.message;
    } finally {
        runBtn.disabled = false;
    }
});

(function animate() {
    requestAnimationFrame(animate);
    controls.update();
    renderer.render(scene, camera);
})();

loadTrajectory();
