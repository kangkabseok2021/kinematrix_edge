# Kinematrix-Edge: 5-Axis Trajectory Interpolator — Design Spec

**Date:** 2026-05-15  
**Status:** Approved

---

## 1. Overview

A lightweight, headless C++ engine that ingests a CSV of 3D Cartesian points, produces a time-optimized smooth kinematic trajectory via cubic spline interpolation, derives 5-axis tool orientations from path tangents, maps the result to motor steps via inverse kinematics, and writes a JSON output file. A Python/FastAPI dashboard serves a Three.js 3D preview of the trajectory on the local network.

**Primary audience:** Portfolio demonstration targeting industrial motion-control companies (e.g. Bystronic). The key proof point is that the math pipeline processes 10,000 interpolated points in single-digit milliseconds on ARM hardware (QEMU-emulated).

---

## 2. Axes & Machine Model

**5 axes:** X, Y, Z (linear gantry drives) + A (head tilt around X-axis) + B (head tilt around Y-axis).

**CSV input:** 3 columns only — `X, Y, Z`. A and B are **computed** by the IK solver from the spline tangent at each interpolated point. The laser head is assumed to align its tool axis with the path tangent direction.

**Machine home:** Tool axis points in −Z. Rotations follow right-hand convention:
- `B = atan2(tx, tz)` — tilt around Y toward X
- `A = atan2(−ty, hypot(tx, tz))` — tilt around X

---

## 3. Repository Layout

```
kinematrix_edge/
├── CMakeLists.txt                  # root: C++17, options, subdirs
├── cmake/
│   └── toolchain-arm.cmake         # ARM cross-compile toolchain (QEMU target)
├── lib/                            # libkinematrix (static)
│   ├── CMakeLists.txt
│   ├── include/kinematrix/
│   │   ├── types.hpp               # Point3, Point5, MotorPoint, MachineConfig
│   │   ├── spline.hpp              # CubicSpline
│   │   └── ik.hpp                  # IKSolver
│   └── src/
│       ├── spline.cpp
│       └── ik.cpp
├── cli/                            # kinematrix_cli executable
│   ├── CMakeLists.txt
│   ├── main.cpp
│   └── csv_parser.cpp/hpp
├── benchmark/                      # kinematrix_bench executable
│   ├── CMakeLists.txt
│   └── bench_main.cpp
├── dashboard/                      # Python FastAPI + Three.js
│   ├── main.py
│   ├── requirements.txt
│   └── static/
│       ├── index.html
│       └── app.js
├── data/
│   └── sample_path.csv             # bundled 100-point example
└── output/                         # gitignored; engine writes here
    └── trajectory.json
```

---

## 4. CMake Structure

**Build system:** CMake 3.20+, C++17.

| Target | Type | Links |
|---|---|---|
| `kinematrix` | Static library | — |
| `kinematrix_cli` | Executable | `kinematrix` |
| `kinematrix_bench` | Executable | `kinematrix` |

**Options:**
- `BUILD_BENCHMARK` (default ON) — controls whether `kinematrix_bench` is built
- Cross-compile: `cmake -DCMAKE_TOOLCHAIN_FILE=cmake/toolchain-arm.cmake`

The toolchain file targets `arm-linux-gnueabihf` for QEMU ARM emulation. Native and cross builds share the same CMakeLists with no ifdefs required in source.

---

## 5. C++ Core Library (`libkinematrix`)

### 5.1 Types (`types.hpp`)

```cpp
struct Point3  { double x, y, z; };
struct Point5  { double x, y, z, a, b; };
struct MotorPoint { long m1, m2, m3, m4, m5; };
struct MachineConfig {
    double lead_x, lead_y, lead_z;  // mm per motor revolution
    double gear_a, gear_b;          // degrees per motor revolution
    long   steps_per_rev;           // common to all axes
};
```

### 5.2 CubicSpline

Natural cubic spline over `Point3` control points. Each axis (X, Y, Z) is interpolated independently using the Thomas algorithm (tridiagonal solve, O(N)).

```cpp
struct SplinePoint { Point3 pos; Point3 tangent; };

CubicSpline(std::span<const Point3> ctrl_pts);
std::vector<SplinePoint> interpolate(int points_per_segment) const;
```

`interpolate(N)` produces `(ctrl_pts.size() − 1) × N` output points, each bundled with its analytic tangent (exact first derivative from spline coefficients — no finite differences). Tangent and position are always computed together to avoid a separate parameterisation pass.

### 5.3 IKSolver

Computes motor steps from a world position and its tangent vector.

```cpp
IKSolver(const MachineConfig& cfg);
MotorPoint solve(const Point3& pos, const Point3& tangent) const;
```

**Internal steps:**
1. Normalize tangent → unit vector `T = (tx, ty, tz)`
2. `B = atan2(tx, tz)`, `A = atan2(−ty, hypot(tx, tz))`
3. Linear motor mapping:
   - `m1 = round(pos.x / cfg.lead_x * cfg.steps_per_rev)`
   - Same pattern for Y→m2, Z→m3
   - `m4 = round(A_deg / cfg.gear_a * cfg.steps_per_rev)`
   - `m5 = round(B_deg / cfg.gear_b * cfg.steps_per_rev)`

No external math dependencies beyond `<cmath>`.

---

## 6. CLI Binary (`kinematrix_cli`)

```
kinematrix_cli <input.csv> <output.json> [--density N]
```

`--density N` sets interpolated points per spline segment (default 100). A 100-row CSV at density 100 → ~10,000 output points.

**Pipeline:**
1. Parse CSV → `std::vector<Point3>`
2. Build `CubicSpline`
3. `interpolate(density)` → dense positions + tangents
4. `IKSolver::solve(pos, tangent)` per point
5. Write JSON (steps 2–4 are timed with `std::chrono::high_resolution_clock`)

**JSON output schema:**
```json
{
  "meta": { "count": 9900, "duration_us": 847 },
  "points": [
    { "x": 1.2, "y": 3.4, "z": 0.0, "a": -2.1, "b": 0.8,
      "m1": 240, "m2": 680, "m3": 0, "m4": -42, "m5": 16 }
  ]
}
```

**Error handling:** Non-zero exit on bad file path, malformed CSV row, or fewer than 2 input points. Error messages go to stderr; JSON is only written on success.

---

## 7. Benchmark Binary (`kinematrix_bench`)

Links `libkinematrix` only. No CSV parser, no JSON writer in the hot path.

**Protocol:**
1. Generate a synthetic 100-point helix as `Point3[]` in code
2. Run full spline + IK pipeline 1000 times
3. Record min / median / max latency per run (each run = 10,000 points)
4. Print structured results table to stdout
5. Exit code 1 if median exceeds threshold (default 10 ms) — CI-able

Provides credible, isolated timing numbers unaffected by I/O.

---

## 8. Python Dashboard

### 8.1 FastAPI (`dashboard/main.py`)

Three endpoints:

| Endpoint | Method | Behaviour |
|---|---|---|
| `/` | GET | Serves `static/index.html` |
| `/api/trajectory` | GET | Returns `output/trajectory.json` |
| `/api/run` | POST | Runs `kinematrix_cli` as subprocess, returns `{duration_us, count}` |

`POST /api/run` body: `{ "input": "data/sample_path.csv", "density": 100 }`.

**Dependencies:** `fastapi`, `uvicorn[standard]` only. No numpy, no pandas.

### 8.2 Three.js Frontend (`static/app.js`)

On page load:
1. `GET /api/trajectory` → parse JSON
2. Build `THREE.BufferGeometry` line from `(x, y, z)` positions
3. Color each vertex blue→red by A/B tilt magnitude (shows IK output visually)
4. `OrbitControls` for pan/rotate/zoom

Side panel shows `meta.count` and `meta.duration_us`. "Run" button calls `POST /api/run` and reloads the scene.

No build step, no bundler. Plain ES modules via CDN (`three.module.js`, `OrbitControls.js`).

---

## 9. Data Flow

```
data/sample_path.csv  (X,Y,Z per row)
         │
         ▼
   kinematrix_cli
         │
         ├─ CubicSpline         → dense Point3[] + tangents
         ├─ IKSolver            → A,B angles + MotorPoint[]
         └─ JSON writer         → output/trajectory.json
                                          │
                                          ▼
                                  FastAPI /api/trajectory
                                          │
                                          ▼
                              Three.js scene (browser)
                          (orbit view, tilt color gradient)
```

---

## 10. Error Handling

| Layer | Failure mode | Response |
|---|---|---|
| CSV parser | Bad row / missing columns | stderr + exit 1 |
| CubicSpline | Fewer than 2 control points | `std::invalid_argument` |
| IKSolver | Near-zero tangent (degenerate) | Clamp to previous A/B; no crash |
| FastAPI `/api/trajectory` | File missing | HTTP 404 |
| FastAPI `/api/run` | CLI exits non-zero | HTTP 500 with stderr in body |

---

## 11. Testing Strategy

- **Unit tests** (optional, CTest): synthetic inputs to `CubicSpline` and `IKSolver` with known expected outputs (straight line → zero curvature, zero tilt angles)
- **Integration smoke test:** run `kinematrix_cli data/sample_path.csv /tmp/out.json` and assert exit 0 + valid JSON
- **Benchmark gate:** `kinematrix_bench` exits 1 if median > 10 ms — wires into CI

---

## 12. Out of Scope

- G-code input parsing
- Real-time streaming / socket IPC
- Actual Raspberry Pi deployment (QEMU emulation used instead)
- Collision detection or workspace limit enforcement
- User authentication on the dashboard
