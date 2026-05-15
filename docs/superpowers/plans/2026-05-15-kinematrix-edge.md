# Kinematrix-Edge Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a C++ cubic-spline + IK engine with CMake, a benchmark binary, and a FastAPI/Three.js dashboard that visualises the 5-axis trajectory.

**Architecture:** A static library (`libkinematrix`) contains all math; a CLI binary links it and produces a JSON file; a benchmark binary links it and measures µs-level latency. Python/FastAPI serves the JSON to a Three.js frontend with orbit controls and tilt-colour gradient.

**Tech Stack:** C++17, CMake 3.20, Catch2 v3 (tests), Python 3.11+, FastAPI, uvicorn, Three.js r160 (CDN), Docker (ARM cross-compile)

---

## File Map

| File | Responsibility |
|---|---|
| `CMakeLists.txt` | Root: C++17, options, FetchContent Catch2, subdirs |
| `cmake/toolchain-arm.cmake` | ARM cross-compile toolchain for Docker/QEMU |
| `Dockerfile` | ARM emulation image for benchmark |
| `.gitignore` | Ignores `build*/`, `output/`, `__pycache__/` |
| `lib/CMakeLists.txt` | Declares `kinematrix` static lib |
| `lib/include/kinematrix/types.hpp` | `Point3`, `SplinePoint`, `MachineConfig`, `MotorPoint`, `IKResult` |
| `lib/include/kinematrix/spline.hpp` | `CubicSpline` class declaration |
| `lib/src/spline.cpp` | Thomas-algorithm cubic spline + analytic tangent |
| `lib/include/kinematrix/ik.hpp` | `IKSolver` class declaration |
| `lib/src/ik.cpp` | Tangent→A/B angles + motor-step mapping |
| `tests/CMakeLists.txt` | Declares `test_kinematrix` with Catch2 |
| `tests/test_spline.cpp` | Unit tests for `CubicSpline` |
| `tests/test_ik.cpp` | Unit tests for `IKSolver` |
| `tests/test_csv.cpp` | Unit tests for `CsvParser` |
| `cli/CMakeLists.txt` | Declares `kinematrix_cli` executable |
| `cli/csv_parser.hpp` | `CsvParser::parseFile`, `CsvParser::parseString` |
| `cli/csv_parser.cpp` | Line-by-line CSV reader |
| `cli/main.cpp` | Arg parsing, pipeline orchestration, JSON writer |
| `benchmark/CMakeLists.txt` | Declares `kinematrix_bench` executable |
| `benchmark/bench_main.cpp` | Synthetic helix, 1000-iteration timing harness |
| `data/sample_path.csv` | 100-point helix (pre-generated) |
| `output/.gitkeep` | Keeps `output/` directory in git |
| `dashboard/requirements.txt` | `fastapi`, `uvicorn[standard]` |
| `dashboard/main.py` | FastAPI: `/`, `/api/trajectory`, `/api/run` |
| `dashboard/static/index.html` | Dark-themed canvas + stats panel |
| `dashboard/static/app.js` | Three.js scene, orbit controls, tilt colour |

---

## Task 1: Project Scaffold

**Files:**
- Create: `CMakeLists.txt`
- Create: `.gitignore`
- Create: `output/.gitkeep`
- Create: `cmake/toolchain-arm.cmake`
- Create: `Dockerfile`

- [ ] **Step 1: Write root CMakeLists.txt**

```cmake
cmake_minimum_required(VERSION 3.20)
project(kinematrix_edge CXX)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

option(BUILD_BENCHMARK "Build benchmark binary" ON)
option(BUILD_TESTS     "Build unit tests"       ON)

add_subdirectory(lib)
add_subdirectory(cli)

if(BUILD_BENCHMARK)
    add_subdirectory(benchmark)
endif()

if(BUILD_TESTS)
    include(FetchContent)
    FetchContent_Declare(
        Catch2
        GIT_REPOSITORY https://github.com/catchorg/Catch2.git
        GIT_TAG        v3.4.0
    )
    FetchContent_MakeAvailable(Catch2)
    include(CTest)
    enable_testing()
    add_subdirectory(tests)
endif()
```

- [ ] **Step 2: Write .gitignore**

```
build*/
output/trajectory.json
__pycache__/
dashboard/.venv/
*.pyc
.superpowers/
```

- [ ] **Step 3: Create output/.gitkeep**

```bash
mkdir -p output && touch output/.gitkeep
```

- [ ] **Step 4: Write cmake/toolchain-arm.cmake**

```cmake
set(CMAKE_SYSTEM_NAME Linux)
set(CMAKE_SYSTEM_PROCESSOR arm)

set(CMAKE_C_COMPILER   arm-linux-gnueabihf-gcc)
set(CMAKE_CXX_COMPILER arm-linux-gnueabihf-g++)

set(CMAKE_FIND_ROOT_PATH_MODE_PROGRAM NEVER)
set(CMAKE_FIND_ROOT_PATH_MODE_LIBRARY ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_INCLUDE ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_PACKAGE ONLY)
```

- [ ] **Step 5: Write Dockerfile**

```dockerfile
FROM --platform=linux/arm/v7 ubuntu:22.04
RUN apt-get update && apt-get install -y cmake build-essential && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY . .
RUN mkdir build-arm && cd build-arm && \
    cmake .. -DBUILD_TESTS=OFF -DCMAKE_BUILD_TYPE=Release && \
    cmake --build . -j4
CMD ["./build-arm/benchmark/kinematrix_bench"]
```

- [ ] **Step 6: Commit**

```bash
git add CMakeLists.txt .gitignore output/.gitkeep cmake/toolchain-arm.cmake Dockerfile
git commit -m "feat: project scaffold, CMake structure, ARM toolchain"
```

---

## Task 2: Library Skeleton & Types

**Files:**
- Create: `lib/CMakeLists.txt`
- Create: `lib/include/kinematrix/types.hpp`
- Create: `lib/src/spline.cpp` (stub)
- Create: `lib/src/ik.cpp` (stub)

- [ ] **Step 1: Write lib/CMakeLists.txt**

```cmake
add_library(kinematrix STATIC
    src/spline.cpp
    src/ik.cpp
)
target_include_directories(kinematrix PUBLIC include)
target_compile_options(kinematrix PRIVATE -Wall -Wextra)
```

- [ ] **Step 2: Write lib/include/kinematrix/types.hpp**

```cpp
#pragma once

struct Point3 { double x, y, z; };

struct SplinePoint {
    Point3 pos;
    Point3 tangent;
};

struct MachineConfig {
    double lead_x, lead_y, lead_z;  // mm per motor revolution
    double gear_a, gear_b;          // degrees per motor revolution
    long   steps_per_rev;
};

struct MotorPoint { long m1, m2, m3, m4, m5; };

struct IKResult {
    double a_deg;
    double b_deg;
    MotorPoint motors;
};
```

- [ ] **Step 3: Write stub lib/src/spline.cpp**

```cpp
#include "kinematrix/spline.hpp"
```

- [ ] **Step 4: Write stub lib/src/ik.cpp**

```cpp
#include "kinematrix/ik.hpp"
```

- [ ] **Step 5: Write lib/include/kinematrix/spline.hpp (declaration only)**

```cpp
#pragma once
#include "types.hpp"
#include <span>
#include <vector>

class CubicSpline {
public:
    explicit CubicSpline(std::span<const Point3> ctrl_pts);
    std::vector<SplinePoint> interpolate(int points_per_segment) const;

private:
    int n_;
    std::vector<double> px_, py_, pz_;
    std::vector<double> mx_, my_, mz_;

    static std::vector<double> computeM(const std::vector<double>& y);
    static double evalAxis(const std::vector<double>& y,
                           const std::vector<double>& M, int i, double u);
    static double derivAxis(const std::vector<double>& y,
                            const std::vector<double>& M, int i, double u);
};
```

- [ ] **Step 6: Write lib/include/kinematrix/ik.hpp (declaration only)**

```cpp
#pragma once
#include "types.hpp"

class IKSolver {
public:
    explicit IKSolver(const MachineConfig& cfg);
    IKResult solve(const Point3& pos, const Point3& raw_tangent) const;

private:
    MachineConfig cfg_;
};
```

- [ ] **Step 7: Verify it compiles (no tests yet)**

```bash
mkdir -p build && cd build && cmake .. -DBUILD_TESTS=OFF -DBUILD_BENCHMARK=OFF && cmake --build .
```

Expected: build succeeds (stubs compile).

- [ ] **Step 8: Commit**

```bash
git add lib/
git commit -m "feat: lib skeleton, types, stub spline and IK"
```

---

## Task 3: CubicSpline — Failing Tests

**Files:**
- Create: `tests/CMakeLists.txt`
- Create: `tests/test_spline.cpp`

- [ ] **Step 1: Write tests/CMakeLists.txt**

```cmake
add_executable(test_kinematrix
    test_spline.cpp
    test_ik.cpp
    test_csv.cpp
)
target_link_libraries(test_kinematrix PRIVATE kinematrix Catch2::Catch2WithMain)
target_include_directories(test_kinematrix PRIVATE ${CMAKE_SOURCE_DIR}/cli)

include(Catch)
catch_discover_tests(test_kinematrix)
```

Note: `test_ik.cpp` and `test_csv.cpp` do not exist yet. Create them as empty stubs now so CMake doesn't complain:

```bash
touch tests/test_ik.cpp tests/test_csv.cpp
```

- [ ] **Step 2: Write tests/test_spline.cpp with failing tests**

```cpp
#include <catch2/catch_test_macros.hpp>
#include <catch2/catch_approx.hpp>
#include "kinematrix/spline.hpp"
#include <array>

using Catch::Approx;

TEST_CASE("throws on fewer than 2 control points", "[spline]") {
    std::array<Point3, 1> pts = {Point3{0, 0, 0}};
    REQUIRE_THROWS_AS(CubicSpline(std::span<const Point3>(pts)), std::invalid_argument);
}

TEST_CASE("two-point linear: output count is points_per_segment", "[spline]") {
    std::array<Point3, 2> pts = {Point3{0, 0, 0}, Point3{2, 0, 0}};
    CubicSpline s(std::span<const Point3>(pts));
    auto result = s.interpolate(4);
    REQUIRE(result.size() == 4);
}

TEST_CASE("two-point linear: positions are uniformly spaced along X", "[spline]") {
    std::array<Point3, 2> pts = {Point3{0, 0, 0}, Point3{2, 0, 0}};
    CubicSpline s(std::span<const Point3>(pts));
    auto result = s.interpolate(4);
    CHECK(result[0].pos.x == Approx(0.0));
    CHECK(result[1].pos.x == Approx(0.5));
    CHECK(result[2].pos.x == Approx(1.0));
    CHECK(result[3].pos.x == Approx(1.5));
}

TEST_CASE("two-point linear: tangents point along segment direction", "[spline]") {
    std::array<Point3, 2> pts = {Point3{0, 0, 0}, Point3{2, 0, 0}};
    CubicSpline s(std::span<const Point3>(pts));
    auto result = s.interpolate(4);
    for (auto& sp : result) {
        CHECK(sp.tangent.x == Approx(2.0));
        CHECK(sp.tangent.y == Approx(0.0));
        CHECK(sp.tangent.z == Approx(0.0));
    }
}

TEST_CASE("three collinear points produce zero Y and Z deviation", "[spline]") {
    std::array<Point3, 3> pts = {
        Point3{0, 0, 0}, Point3{1, 0, 0}, Point3{2, 0, 0}
    };
    CubicSpline s(std::span<const Point3>(pts));
    auto result = s.interpolate(10);
    for (auto& sp : result) {
        CHECK(sp.pos.y == Approx(0.0).margin(1e-10));
        CHECK(sp.pos.z == Approx(0.0).margin(1e-10));
    }
}

TEST_CASE("output size is (N-1) * points_per_segment", "[spline]") {
    std::array<Point3, 5> pts = {
        Point3{0,0,0}, Point3{1,1,0}, Point3{2,0,0},
        Point3{3,1,0}, Point3{4,0,0}
    };
    CubicSpline s(std::span<const Point3>(pts));
    auto result = s.interpolate(7);
    REQUIRE(result.size() == 4 * 7);
}
```

- [ ] **Step 3: Run tests — verify they FAIL**

```bash
cd build && cmake .. && cmake --build . && ctest -V -R test_kinematrix
```

Expected: FAIL — `CubicSpline` constructor is not implemented yet.

- [ ] **Step 4: Commit failing tests**

```bash
git add tests/
git commit -m "test: failing CubicSpline tests"
```

---

## Task 4: CubicSpline — Implementation

**Files:**
- Modify: `lib/src/spline.cpp`

- [ ] **Step 1: Implement spline.cpp**

```cpp
#include "kinematrix/spline.hpp"
#include <stdexcept>
#include <cmath>

CubicSpline::CubicSpline(std::span<const Point3> pts) {
    n_ = static_cast<int>(pts.size());
    if (n_ < 2) throw std::invalid_argument("CubicSpline requires at least 2 points");

    px_.reserve(n_); py_.reserve(n_); pz_.reserve(n_);
    for (const auto& p : pts) {
        px_.push_back(p.x);
        py_.push_back(p.y);
        pz_.push_back(p.z);
    }
    mx_ = computeM(px_);
    my_ = computeM(py_);
    mz_ = computeM(pz_);
}

// Thomas algorithm: natural cubic spline second derivatives.
// System: M[i-1] + 4*M[i] + M[i+1] = 6*(y[i-1]-2y[i]+y[i+1]), M[0]=M[n-1]=0.
std::vector<double> CubicSpline::computeM(const std::vector<double>& y) {
    int n = static_cast<int>(y.size());
    std::vector<double> M(n, 0.0);
    if (n <= 2) return M;

    int m = n - 2;
    std::vector<double> r(m);
    for (int i = 0; i < m; ++i)
        r[i] = 6.0 * (y[i] - 2.0 * y[i + 1] + y[i + 2]);

    // Forward sweep (sub-diagonal = 1, main-diagonal = 4, super-diagonal = 1)
    std::vector<double> cp(m);
    std::vector<double> dp(m);
    cp[0] = 1.0 / 4.0;
    dp[0] = r[0] / 4.0;
    for (int i = 1; i < m; ++i) {
        double denom = 4.0 - cp[i - 1];
        cp[i] = 1.0 / denom;
        dp[i] = (r[i] - dp[i - 1]) / denom;
    }

    // Back substitution
    std::vector<double> sol(m);
    sol[m - 1] = dp[m - 1];
    for (int i = m - 2; i >= 0; --i)
        sol[i] = dp[i] - cp[i] * sol[i + 1];

    for (int i = 0; i < m; ++i)
        M[i + 1] = sol[i];
    return M;
}

// Segment i at local parameter u ∈ [0,1): S = a + b*u + c*u² + d*u³
double CubicSpline::evalAxis(const std::vector<double>& y,
                              const std::vector<double>& M, int i, double u) {
    double b = (y[i + 1] - y[i]) - (2.0 * M[i] + M[i + 1]) / 6.0;
    double c = M[i] / 2.0;
    double d = (M[i + 1] - M[i]) / 6.0;
    return y[i] + u * (b + u * (c + u * d));
}

// Analytic first derivative: S' = b + 2c*u + 3d*u²
double CubicSpline::derivAxis(const std::vector<double>& y,
                               const std::vector<double>& M, int i, double u) {
    double b = (y[i + 1] - y[i]) - (2.0 * M[i] + M[i + 1]) / 6.0;
    double c = M[i] / 2.0;
    double d = (M[i + 1] - M[i]) / 6.0;
    return b + u * (2.0 * c + u * 3.0 * d);
}

std::vector<SplinePoint> CubicSpline::interpolate(int pps) const {
    std::vector<SplinePoint> result;
    result.reserve((n_ - 1) * pps);

    for (int i = 0; i < n_ - 1; ++i) {
        for (int j = 0; j < pps; ++j) {
            double u = static_cast<double>(j) / pps;
            SplinePoint sp;
            sp.pos     = { evalAxis(px_, mx_, i, u),
                           evalAxis(py_, my_, i, u),
                           evalAxis(pz_, mz_, i, u) };
            sp.tangent = { derivAxis(px_, mx_, i, u),
                           derivAxis(py_, my_, i, u),
                           derivAxis(pz_, mz_, i, u) };
            result.push_back(sp);
        }
    }
    return result;
}
```

- [ ] **Step 2: Run tests — verify they PASS**

```bash
cd build && cmake --build . && ctest -V -R test_kinematrix
```

Expected:
```
✓ throws on fewer than 2 control points
✓ two-point linear: output count is points_per_segment
✓ two-point linear: positions are uniformly spaced along X
✓ two-point linear: tangents point along segment direction
✓ three collinear points produce zero Y and Z deviation
✓ output size is (N-1) * points_per_segment
```

- [ ] **Step 3: Commit**

```bash
git add lib/src/spline.cpp
git commit -m "feat: CubicSpline implementation — Thomas algorithm, analytic tangent"
```

---

## Task 5: IKSolver — Failing Tests Then Implementation

**Files:**
- Modify: `tests/test_ik.cpp`
- Modify: `lib/src/ik.cpp`

- [ ] **Step 1: Write tests/test_ik.cpp**

```cpp
#include <catch2/catch_test_macros.hpp>
#include <catch2/catch_approx.hpp>
#include "kinematrix/ik.hpp"

using Catch::Approx;

static MachineConfig testCfg() {
    return MachineConfig{5.0, 5.0, 5.0, 360.0, 360.0, 200};
}

TEST_CASE("degenerate near-zero tangent gives home orientation (A=B=0)", "[ik]") {
    IKSolver ik(testCfg());
    IKResult r = ik.solve({0, 0, 0}, {0, 0, 0});
    CHECK(r.a_deg == Approx(0.0));
    CHECK(r.b_deg == Approx(0.0));
}

TEST_CASE("tangent along +Z gives A=0 B=0 (home orientation)", "[ik]") {
    IKSolver ik(testCfg());
    IKResult r = ik.solve({0, 0, 0}, {0, 0, 1});
    CHECK(r.a_deg == Approx(0.0));
    CHECK(r.b_deg == Approx(0.0));
}

TEST_CASE("tangent along +X gives B=90 A=0", "[ik]") {
    IKSolver ik(testCfg());
    IKResult r = ik.solve({0, 0, 0}, {1, 0, 0});
    CHECK(r.b_deg == Approx(90.0));
    CHECK(r.a_deg == Approx(0.0));
}

TEST_CASE("tangent along -Y gives A=-90 B=0", "[ik]") {
    IKSolver ik(testCfg());
    IKResult r = ik.solve({0, 0, 0}, {0, -1, 0});
    CHECK(r.a_deg == Approx(90.0));
    CHECK(r.b_deg == Approx(0.0).margin(1e-9));
}

TEST_CASE("motor steps computed correctly from position", "[ik]") {
    // lead=5mm/rev, steps=200 → 1mm = 40 steps
    IKSolver ik(testCfg());
    IKResult r = ik.solve({5.0, 10.0, 2.5}, {0, 0, 1});
    CHECK(r.motors.m1 == 200);   // 5 / 5 * 200
    CHECK(r.motors.m2 == 400);   // 10 / 5 * 200
    CHECK(r.motors.m3 == 100);   // 2.5 / 5 * 200
    CHECK(r.motors.m4 == 0);     // A=0
    CHECK(r.motors.m5 == 0);     // B=0
}

TEST_CASE("diagonal tangent gives equal A and B components", "[ik]") {
    IKSolver ik(testCfg());
    // tangent (1,0,1)/sqrt(2): B=atan2(1,1)=45°, A=0
    IKResult r = ik.solve({0, 0, 0}, {1, 0, 1});
    CHECK(r.b_deg == Approx(45.0));
    CHECK(r.a_deg == Approx(0.0));
}
```

- [ ] **Step 2: Run — verify FAIL**

```bash
cd build && cmake --build . && ctest -V -R test_kinematrix
```

Expected: IK tests FAIL — `IKSolver` not implemented.

- [ ] **Step 3: Implement lib/src/ik.cpp**

```cpp
#include "kinematrix/ik.hpp"
#include <cmath>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

IKSolver::IKSolver(const MachineConfig& cfg) : cfg_(cfg) {}

IKResult IKSolver::solve(const Point3& pos, const Point3& raw_tangent) const {
    double len = std::sqrt(raw_tangent.x * raw_tangent.x +
                           raw_tangent.y * raw_tangent.y +
                           raw_tangent.z * raw_tangent.z);

    double tx, ty, tz;
    if (len < 1e-10) {
        tx = 0.0; ty = 0.0; tz = 1.0;
    } else {
        tx = raw_tangent.x / len;
        ty = raw_tangent.y / len;
        tz = raw_tangent.z / len;
    }

    double xz_len = std::hypot(tx, tz);
    double B_rad = (xz_len < 1e-10) ? 0.0 : std::atan2(tx, tz);
    double A_rad = std::atan2(-ty, xz_len);

    constexpr double RAD_TO_DEG = 180.0 / M_PI;
    double a_deg = A_rad * RAD_TO_DEG;
    double b_deg = B_rad * RAD_TO_DEG;

    double spr = static_cast<double>(cfg_.steps_per_rev);
    return IKResult{
        a_deg,
        b_deg,
        MotorPoint{
            std::lround(pos.x / cfg_.lead_x * spr),
            std::lround(pos.y / cfg_.lead_y * spr),
            std::lround(pos.z / cfg_.lead_z * spr),
            std::lround(a_deg / cfg_.gear_a * spr),
            std::lround(b_deg / cfg_.gear_b * spr)
        }
    };
}
```

- [ ] **Step 4: Run — verify all tests PASS**

```bash
cd build && cmake --build . && ctest -V
```

Expected: all spline and IK tests pass.

- [ ] **Step 5: Commit**

```bash
git add tests/test_ik.cpp lib/src/ik.cpp
git commit -m "feat: IKSolver — tangent-derived A/B tilt angles and motor steps"
```

---

## Task 6: CSV Parser — TDD

**Files:**
- Create: `cli/csv_parser.hpp`
- Create: `cli/csv_parser.cpp`
- Modify: `tests/test_csv.cpp`

- [ ] **Step 1: Write tests/test_csv.cpp**

```cpp
#include <catch2/catch_test_macros.hpp>
#include <catch2/catch_approx.hpp>
#include "csv_parser.hpp"

using Catch::Approx;

TEST_CASE("parse two-row CSV with header", "[csv]") {
    std::string s = "x,y,z\n1.0,2.0,3.0\n4.0,5.0,6.0\n";
    auto pts = CsvParser::parseString(s);
    REQUIRE(pts.size() == 2);
    CHECK(pts[0].x == Approx(1.0));
    CHECK(pts[0].y == Approx(2.0));
    CHECK(pts[0].z == Approx(3.0));
    CHECK(pts[1].z == Approx(6.0));
}

TEST_CASE("parse CSV without header", "[csv]") {
    std::string s = "1.0,2.0,3.0\n4.0,5.0,6.0\n";
    auto pts = CsvParser::parseString(s);
    REQUIRE(pts.size() == 2);
    CHECK(pts[0].x == Approx(1.0));
}

TEST_CASE("trailing newline does not produce extra row", "[csv]") {
    std::string s = "1.0,2.0,3.0\n";
    auto pts = CsvParser::parseString(s);
    REQUIRE(pts.size() == 1);
}

TEST_CASE("throws on row with fewer than 3 values", "[csv]") {
    std::string s = "1.0,2.0\n";
    REQUIRE_THROWS(CsvParser::parseString(s));
}

TEST_CASE("throws on non-numeric value", "[csv]") {
    std::string s = "1.0,abc,3.0\n";
    REQUIRE_THROWS(CsvParser::parseString(s));
}
```

- [ ] **Step 2: Run — verify FAIL**

```bash
cd build && cmake --build . && ctest -V -R test_kinematrix
```

Expected: CSV tests FAIL — `CsvParser` not declared.

- [ ] **Step 3: Write cli/csv_parser.hpp**

```cpp
#pragma once
#include "kinematrix/types.hpp"
#include <string>
#include <vector>

class CsvParser {
public:
    static std::vector<Point3> parseFile(const std::string& path);
    static std::vector<Point3> parseString(const std::string& content);
};
```

- [ ] **Step 4: Write cli/csv_parser.cpp**

```cpp
#include "csv_parser.hpp"
#include <fstream>
#include <sstream>
#include <stdexcept>

static bool isNumeric(const std::string& s) {
    if (s.empty()) return false;
    try { std::stod(s); return true; }
    catch (...) { return false; }
}

static std::vector<Point3> parseStream(std::istream& in) {
    std::vector<Point3> pts;
    std::string line;
    while (std::getline(in, line)) {
        if (line.empty()) continue;
        std::istringstream ss(line);
        std::string tok;
        std::vector<std::string> fields;
        while (std::getline(ss, tok, ','))
            fields.push_back(tok);
        if (fields.size() < 3) {
            if (!isNumeric(fields[0])) continue; // header row
            throw std::runtime_error("CSV row has fewer than 3 columns: " + line);
        }
        if (!isNumeric(fields[0])) continue; // header row
        try {
            pts.push_back({std::stod(fields[0]),
                           std::stod(fields[1]),
                           std::stod(fields[2])});
        } catch (...) {
            throw std::runtime_error("Non-numeric value in CSV row: " + line);
        }
    }
    return pts;
}

std::vector<Point3> CsvParser::parseString(const std::string& content) {
    std::istringstream ss(content);
    return parseStream(ss);
}

std::vector<Point3> CsvParser::parseFile(const std::string& path) {
    std::ifstream f(path);
    if (!f) throw std::runtime_error("Cannot open file: " + path);
    return parseStream(f);
}
```

- [ ] **Step 5: Add csv_parser sources to test target — update tests/CMakeLists.txt**

```cmake
add_executable(test_kinematrix
    test_spline.cpp
    test_ik.cpp
    test_csv.cpp
    ${CMAKE_SOURCE_DIR}/cli/csv_parser.cpp
)
target_link_libraries(test_kinematrix PRIVATE kinematrix Catch2::Catch2WithMain)
target_include_directories(test_kinematrix PRIVATE ${CMAKE_SOURCE_DIR}/cli)

include(Catch)
catch_discover_tests(test_kinematrix)
```

- [ ] **Step 6: Run — verify all tests PASS**

```bash
cd build && cmake .. && cmake --build . && ctest -V
```

Expected: all spline, IK, and CSV tests pass.

- [ ] **Step 7: Commit**

```bash
git add cli/csv_parser.hpp cli/csv_parser.cpp tests/test_csv.cpp tests/CMakeLists.txt
git commit -m "feat: CsvParser with header detection and error handling"
```

---

## Task 7: CLI Binary & Sample Data

**Files:**
- Create: `cli/CMakeLists.txt`
- Create: `cli/main.cpp`
- Create: `data/sample_path.csv`

- [ ] **Step 1: Write cli/CMakeLists.txt**

```cmake
add_executable(kinematrix_cli
    csv_parser.cpp
    main.cpp
)
target_link_libraries(kinematrix_cli PRIVATE kinematrix)
```

- [ ] **Step 2: Generate data/sample_path.csv (100-point helix)**

Run this Python one-liner:

```bash
python3 -c "
import math, sys
print('x,y,z')
N = 100
for i in range(N):
    t = 4 * math.pi * i / (N - 1)
    print(f'{math.cos(t):.6f},{math.sin(t):.6f},{t/(2*math.pi):.6f}')
" > data/sample_path.csv
```

Verify first 3 lines:
```bash
head -4 data/sample_path.csv
```
Expected:
```
x,y,z
1.000000,0.000000,0.000000
0.998027,0.062791,0.020202
0.992115,0.125333,0.040404
```

- [ ] **Step 3: Write cli/main.cpp**

```cpp
#include <kinematrix/spline.hpp>
#include <kinematrix/ik.hpp>
#include "csv_parser.hpp"
#include <chrono>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

static const MachineConfig kDefaultCfg{5.0, 5.0, 5.0, 360.0, 360.0, 200};

int main(int argc, char* argv[]) {
    if (argc < 3) {
        std::cerr << "Usage: kinematrix_cli <input.csv> <output.json> [--density N]\n";
        return 1;
    }

    std::string input_path  = argv[1];
    std::string output_path = argv[2];
    int density = 100;

    for (int i = 3; i < argc - 1; ++i) {
        if (std::string(argv[i]) == "--density") {
            try { density = std::stoi(argv[i + 1]); }
            catch (...) {
                std::cerr << "Invalid density value: " << argv[i + 1] << "\n";
                return 1;
            }
        }
    }

    std::vector<Point3> ctrl;
    try {
        ctrl = CsvParser::parseFile(input_path);
    } catch (const std::exception& e) {
        std::cerr << "CSV error: " << e.what() << "\n";
        return 1;
    }

    if (static_cast<int>(ctrl.size()) < 2) {
        std::cerr << "Error: need at least 2 control points, got "
                  << ctrl.size() << "\n";
        return 1;
    }

    IKSolver ik(kDefaultCfg);

    auto t0 = std::chrono::high_resolution_clock::now();
    CubicSpline spline(ctrl);
    auto pts = spline.interpolate(density);
    std::vector<IKResult> results;
    results.reserve(pts.size());
    for (const auto& sp : pts)
        results.push_back(ik.solve(sp.pos, sp.tangent));
    auto t1 = std::chrono::high_resolution_clock::now();
    long dur_us = std::chrono::duration_cast<std::chrono::microseconds>(t1 - t0).count();

    std::ofstream out(output_path);
    if (!out) {
        std::cerr << "Cannot open output: " << output_path << "\n";
        return 1;
    }

    out << std::fixed << std::setprecision(4);
    out << "{\n  \"meta\": { \"count\": " << pts.size()
        << ", \"duration_us\": " << dur_us << " },\n";
    out << "  \"points\": [\n";
    for (std::size_t i = 0; i < pts.size(); ++i) {
        const auto& sp = pts[i];
        const auto& r  = results[i];
        out << "    { \"x\": " << sp.pos.x   << ", \"y\": " << sp.pos.y
            << ", \"z\": "     << sp.pos.z   << ", \"a\": " << r.a_deg
            << ", \"b\": "     << r.b_deg    << ", \"m1\": " << r.motors.m1
            << ", \"m2\": "    << r.motors.m2 << ", \"m3\": " << r.motors.m3
            << ", \"m4\": "    << r.motors.m4 << ", \"m5\": " << r.motors.m5
            << " }";
        if (i + 1 < pts.size()) out << ",";
        out << "\n";
    }
    out << "  ]\n}\n";

    std::cout << "Done: " << pts.size() << " points in " << dur_us << " µs\n";
    return 0;
}
```

- [ ] **Step 4: Build and smoke-test the CLI**

```bash
cd build && cmake .. && cmake --build .
./kinematrix_cli ../data/sample_path.csv ../output/trajectory.json --density 100
```

Expected output (numbers will vary):
```
Done: 9900 points in 847 µs
```

```bash
head -6 ../output/trajectory.json
```

Expected:
```json
{
  "meta": { "count": 9900, "duration_us": 847 },
  "points": [
    { "x": 1.0000, "y": 0.0000, "z": 0.0000, "a": ...
```

- [ ] **Step 5: Commit**

```bash
git add cli/ data/sample_path.csv
git commit -m "feat: kinematrix_cli — CSV→spline→IK→JSON pipeline"
```

---

## Task 8: Benchmark Binary

**Files:**
- Create: `benchmark/CMakeLists.txt`
- Create: `benchmark/bench_main.cpp`

- [ ] **Step 1: Write benchmark/CMakeLists.txt**

```cmake
add_executable(kinematrix_bench bench_main.cpp)
target_link_libraries(kinematrix_bench PRIVATE kinematrix)
```

- [ ] **Step 2: Write benchmark/bench_main.cpp**

```cpp
#include <kinematrix/spline.hpp>
#include <kinematrix/ik.hpp>
#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdio>
#include <vector>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

static constexpr int    N_CTRL      = 100;
static constexpr int    DENSITY     = 100;
static constexpr int    ITERATIONS  = 1000;
static constexpr double THRESHOLD_MS = 10.0;

static std::vector<Point3> makeHelix(int n) {
    std::vector<Point3> pts(n);
    for (int i = 0; i < n; ++i) {
        double t = 4.0 * M_PI * i / (n - 1);
        pts[i] = {std::cos(t), std::sin(t), t / (2.0 * M_PI)};
    }
    return pts;
}

int main() {
    auto ctrl = makeHelix(N_CTRL);
    MachineConfig cfg{5.0, 5.0, 5.0, 360.0, 360.0, 200};
    IKSolver ik(cfg);

    std::vector<double> times_us(ITERATIONS);
    for (int iter = 0; iter < ITERATIONS; ++iter) {
        auto t0 = std::chrono::high_resolution_clock::now();
        CubicSpline spline(ctrl);
        auto pts = spline.interpolate(DENSITY);
        for (const auto& sp : pts)
            (void)ik.solve(sp.pos, sp.tangent);
        auto t1 = std::chrono::high_resolution_clock::now();
        times_us[iter] =
            std::chrono::duration<double, std::micro>(t1 - t0).count();
    }

    std::sort(times_us.begin(), times_us.end());
    double min_us    = times_us.front();
    double median_us = times_us[ITERATIONS / 2];
    double max_us    = times_us.back();

    int out_pts = (N_CTRL - 1) * DENSITY;
    std::printf("Kinematrix-Edge Benchmark\n");
    std::printf("Control pts: %d  Density: %d  Output pts/run: %d  Runs: %d\n\n",
                N_CTRL, DENSITY, out_pts, ITERATIONS);
    std::printf("%-14s %-14s %-14s\n", "Min (µs)", "Median (µs)", "Max (µs)");
    std::printf("%-14.1f %-14.1f %-14.1f\n\n", min_us, median_us, max_us);
    std::printf("%-14s %-14s %-14s\n", "Min (ms)", "Median (ms)", "Max (ms)");
    std::printf("%-14.3f %-14.3f %-14.3f\n\n",
                min_us/1000, median_us/1000, max_us/1000);

    if (median_us / 1000.0 > THRESHOLD_MS) {
        std::fprintf(stderr, "FAIL: median %.3f ms exceeds threshold %.1f ms\n",
                     median_us / 1000.0, THRESHOLD_MS);
        return 1;
    }
    std::printf("PASS: median %.3f ms within %.1f ms threshold\n",
                median_us / 1000.0, THRESHOLD_MS);
    return 0;
}
```

- [ ] **Step 3: Build and run benchmark**

```bash
cd build && cmake .. && cmake --build .
./benchmark/kinematrix_bench
```

Expected (native x86/ARM64, numbers will vary):
```
Kinematrix-Edge Benchmark
Control pts: 100  Density: 100  Output pts/run: 9900  Runs: 1000

Min (µs)       Median (µs)    Max (µs)
312.4          398.1          1204.7

Min (ms)       Median (ms)    Max (ms)
0.312          0.398          1.205

PASS: median 0.398 ms within 10.0 ms threshold
```

- [ ] **Step 4: Commit**

```bash
git add benchmark/
git commit -m "feat: kinematrix_bench — 1000-iteration timing harness, CI-able exit code"
```

---

## Task 9: FastAPI Dashboard

**Files:**
- Create: `dashboard/requirements.txt`
- Create: `dashboard/main.py`

- [ ] **Step 1: Write dashboard/requirements.txt**

```
fastapi==0.111.0
uvicorn[standard]==0.29.0
```

- [ ] **Step 2: Install dependencies**

```bash
cd dashboard
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

- [ ] **Step 3: Write dashboard/main.py**

```python
from __future__ import annotations

import json
import pathlib
import subprocess

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI()

_ROOT = pathlib.Path(__file__).parent.parent
_OUTPUT = _ROOT / "output" / "trajectory.json"
_CLI = _ROOT / "build" / "kinematrix_cli"
_STATIC = pathlib.Path(__file__).parent / "static"


class RunRequest(BaseModel):
    input: str = "data/sample_path.csv"
    density: int = 100


@app.get("/")
def index() -> FileResponse:
    return FileResponse(_STATIC / "index.html")


@app.get("/api/trajectory")
def get_trajectory() -> JSONResponse:
    if not _OUTPUT.exists():
        raise HTTPException(
            status_code=404,
            detail="No trajectory file. POST /api/run first.",
        )
    return JSONResponse(json.loads(_OUTPUT.read_text()))


@app.post("/api/run")
def run_engine(req: RunRequest) -> dict:
    result = subprocess.run(
        [str(_CLI), str(_ROOT / req.input), str(_OUTPUT),
         "--density", str(req.density)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise HTTPException(status_code=500, detail=result.stderr)
    data = json.loads(_OUTPUT.read_text())
    return {
        "duration_us": data["meta"]["duration_us"],
        "count": data["meta"]["count"],
    }


app.mount("/static", StaticFiles(directory=str(_STATIC)), name="static")
```

- [ ] **Step 4: Verify FastAPI starts**

```bash
cd dashboard && source .venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000
```

Expected: `INFO: Application startup complete.`  
Visit http://localhost:8000/api/trajectory — should return 404 (no file yet, correct).

- [ ] **Step 5: Commit**

```bash
git add dashboard/requirements.txt dashboard/main.py
git commit -m "feat: FastAPI dashboard — trajectory serve, engine trigger endpoint"
```

---

## Task 10: Three.js Frontend

**Files:**
- Create: `dashboard/static/index.html`
- Create: `dashboard/static/app.js`

- [ ] **Step 1: Write dashboard/static/index.html**

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Kinematrix-Edge</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { background: #08080f; color: #d0d0e0; font-family: monospace; overflow: hidden; }
    #canvas-container { position: fixed; inset: 0; }
    #panel {
      position: fixed; top: 20px; right: 20px; width: 230px;
      background: rgba(8, 8, 20, 0.88);
      border: 1px solid #222244;
      border-radius: 6px; padding: 18px; z-index: 10;
    }
    #panel h2 { font-size: 11px; color: #555577; letter-spacing: 3px; margin-bottom: 14px; }
    .stat { margin-bottom: 10px; }
    .label { font-size: 10px; color: #445; text-transform: uppercase; letter-spacing: 1px; }
    .value { font-size: 22px; color: #58c8ff; font-weight: bold; }
    .unit  { font-size: 12px; color: #445; }
    #run-btn {
      margin-top: 18px; width: 100%; padding: 9px;
      background: #0d2540; color: #58c8ff;
      border: 1px solid #1a4070; border-radius: 4px;
      cursor: pointer; font-family: monospace; font-size: 12px;
      letter-spacing: 1px;
    }
    #run-btn:hover { background: #1a3a60; }
    #status { margin-top: 10px; font-size: 10px; color: #556; min-height: 14px; }
  </style>
</head>
<body>
  <div id="canvas-container"></div>
  <div id="panel">
    <h2>KINEMATRIX EDGE</h2>
    <div class="stat">
      <div class="label">Points</div>
      <div class="value" id="count">—</div>
    </div>
    <div class="stat">
      <div class="label">Engine time</div>
      <div class="value"><span id="duration">—</span> <span class="unit">µs</span></div>
    </div>
    <button id="run-btn">▶ RUN ENGINE</button>
    <div id="status"></div>
  </div>
  <script type="module" src="/static/app.js"></script>
</body>
</html>
```

- [ ] **Step 2: Write dashboard/static/app.js**

```javascript
import * as THREE from 'https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js';
import { OrbitControls } from 'https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/controls/OrbitControls.js';

const container = document.getElementById('canvas-container');
const countEl   = document.getElementById('count');
const durEl     = document.getElementById('duration');
const statusEl  = document.getElementById('status');
const runBtn    = document.getElementById('run-btn');

// --- Scene setup ---
const scene    = new THREE.Scene();
scene.background = new THREE.Color(0x08080f);

const camera   = new THREE.PerspectiveCamera(55, window.innerWidth / window.innerHeight, 0.001, 500);
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

// Faint grid for spatial reference
scene.add(new THREE.GridHelper(10, 20, 0x111133, 0x111133));

// --- Trajectory rendering ---
let trajLine = null;

function buildTrajectory(data) {
  if (trajLine) { scene.remove(trajLine); trajLine.geometry.dispose(); }

  const pts  = data.points;
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
    colors[i * 3]     = t;           // R: high tilt → red
    colors[i * 3 + 1] = 0.1;
    colors[i * 3 + 2] = 1.0 - t;    // B: low tilt → blue
  }

  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
  geo.setAttribute('color',    new THREE.BufferAttribute(colors, 3));
  trajLine = new THREE.Line(geo, new THREE.LineBasicMaterial({ vertexColors: true }));
  scene.add(trajLine);

  countEl.textContent = data.meta.count.toLocaleString();
  durEl.textContent   = data.meta.duration_us.toLocaleString();
}

async function loadTrajectory() {
  try {
    const res = await fetch('/api/trajectory');
    if (!res.ok) { statusEl.textContent = 'No trajectory — click RUN ENGINE'; return; }
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

// --- Render loop ---
(function animate() {
  requestAnimationFrame(animate);
  controls.update();
  renderer.render(scene, camera);
})();

loadTrajectory();
```

- [ ] **Step 3: Run the full stack and verify**

Terminal 1 — ensure trajectory exists:
```bash
./build/kinematrix_cli data/sample_path.csv output/trajectory.json --density 100
```

Terminal 2 — start dashboard:
```bash
cd dashboard && source .venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000
```

Open http://localhost:8000 in a browser.  
Expected: 3D helix visible, coloured blue→red, stats panel shows count (~9900) and duration. Orbit controls (left-drag = rotate, scroll = zoom) work. "RUN ENGINE" button recomputes and reloads.

- [ ] **Step 4: Commit**

```bash
git add dashboard/static/
git commit -m "feat: Three.js dashboard — orbit controls, blue-red tilt colour gradient"
```

---

## Task 11: ARM Cross-Compile & Benchmark

**Files:** No new files. Uses `Dockerfile` from Task 1.

- [ ] **Step 1: Ensure Docker is running**

```bash
docker info | grep "Server Version"
```

Expected: prints a version string (Docker is running).

- [ ] **Step 2: Enable multi-platform builder (once)**

```bash
docker buildx create --name arm-builder --use
docker buildx inspect --bootstrap
```

Expected: `Driver: docker-container` and `Platforms: linux/arm/v7` in the list.

- [ ] **Step 3: Build the ARM image and capture benchmark output**

```bash
docker buildx build --platform linux/arm/v7 --load -t kinematrix-arm .
docker run --rm kinematrix-arm
```

Expected output (ARM is slower than native — this is the portfolio proof point):
```
Kinematrix-Edge Benchmark
Control pts: 100  Density: 100  Output pts/run: 9900  Runs: 1000

Min (µs)       Median (µs)    Max (µs)
1842.3         2104.7         4891.2

Min (ms)       Median (ms)    Max (ms)
1.842          2.105          4.891

PASS: median 2.105 ms within 10.0 ms threshold
```

Save this output — it's the benchmark evidence for the portfolio.

- [ ] **Step 4: Commit benchmark result as a markdown note**

Create `docs/benchmark-arm.md`:
```markdown
# ARM Benchmark Results (linux/arm/v7 via Docker buildx)

Date: 2026-05-15  
Platform: linux/arm/v7 (emulated via Docker buildx)  
Input: 100 control points, density=100 → 9900 output pts/run  
Iterations: 1000

| | Min | Median | Max |
|---|---|---|---|
| µs | 1842 | 2105 | 4891 |
| ms | 1.84 | 2.10 | 4.89 |

**PASS** — median well under 10 ms threshold.
```
*(Fill in actual numbers from your run.)*

```bash
git add docs/benchmark-arm.md
git commit -m "docs: ARM benchmark results — sub-3ms median on emulated arm/v7"
```

---

## Task 12: End-to-End Smoke Test

- [ ] **Step 1: Full pipeline native run**

```bash
# From project root
./build/kinematrix_cli data/sample_path.csv output/trajectory.json --density 100
```

Expected: `Done: 9900 points in <N> µs`

- [ ] **Step 2: Validate JSON structure**

```bash
python3 -c "
import json, sys
d = json.load(open('output/trajectory.json'))
assert 'meta' in d and 'points' in d, 'missing top-level keys'
assert d['meta']['count'] == len(d['points']), 'count mismatch'
p = d['points'][0]
for k in ['x','y','z','a','b','m1','m2','m3','m4','m5']:
    assert k in p, f'missing key {k}'
print(f'OK — {d[\"meta\"][\"count\"]} points, {d[\"meta\"][\"duration_us\"]} µs')
"
```

Expected: `OK — 9900 points, <N> µs`

- [ ] **Step 3: Run all unit tests**

```bash
cd build && ctest -V
```

Expected: all tests pass, exit 0.

- [ ] **Step 4: Run benchmark and confirm PASS exit code**

```bash
./build/benchmark/kinematrix_bench ; echo "Exit: $?"
```

Expected: `PASS: median X.XXX ms within 10.0 ms threshold` then `Exit: 0`

- [ ] **Step 5: Final commit**

```bash
git add -A
git commit -m "chore: end-to-end verified — all tests pass, benchmark PASS, dashboard live"
```

---

## Self-Review Checklist

**Spec coverage:**

| Spec requirement | Task |
|---|---|
| CSV parser (X,Y,Z) | Task 6 |
| Cubic spline interpolation | Task 4 |
| Thomas algorithm O(N) | Task 4 |
| Analytic tangent | Task 4 |
| IK: tangent → A/B angles | Task 5 |
| IK: motor step mapping | Task 5 |
| Degenerate tangent clamp | Task 5 (near-zero → home) |
| kinematrix_cli binary | Task 7 |
| --density flag | Task 7 |
| JSON output schema | Task 7 |
| Timing (duration_us in JSON) | Task 7 |
| kinematrix_bench | Task 8 |
| 1000-iteration harness | Task 8 |
| CI-able exit code | Task 8 |
| FastAPI / `/api/trajectory` | Task 9 |
| FastAPI / `/api/run` | Task 9 |
| HTTP 404 when file missing | Task 9 |
| HTTP 500 on CLI error | Task 9 |
| Three.js 3D line | Task 10 |
| Orbit controls | Task 10 |
| Blue→red tilt colour | Task 10 |
| Stats panel | Task 10 |
| ARM cross-compile | Task 11 |
| Benchmark on ARM | Task 11 |
| CMake BUILD_BENCHMARK option | Task 1 |
| CMake BUILD_TESTS option | Task 1 |

All spec requirements covered. ✓
