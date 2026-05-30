# ARM Benchmark Results (linux/arm64 via Docker buildx)

**Date:** 2026-05-15  
**Platform:** linux/arm64 (emulated via Docker buildx on Apple Silicon)  
**Input:** 100 control points, density=100 → 9,900 output pts/run  
**Iterations:** 1,000

| | Min | Median | Max |
|---|---|---|---|
| µs | 247 | 253 | 651 |
| ms | 0.247 | 0.253 | 0.651 |

**PASS** — median 0.253 ms, 40× under the 10 ms threshold.

Pipeline: cubic spline (Thomas algorithm) + tangent-derived IK (A/B tilt angles) + motor-step mapping for all 9,900 points.
