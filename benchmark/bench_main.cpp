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

static constexpr int    N_CTRL       = 100;
static constexpr int    DENSITY      = 100;
static constexpr int    ITERATIONS   = 1000;
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
    std::printf("%-14s %-14s %-14s\n", "Min (us)", "Median (us)", "Max (us)");
    std::printf("%-14.1f %-14.1f %-14.1f\n\n", min_us, median_us, max_us);
    std::printf("%-14s %-14s %-14s\n", "Min (ms)", "Median (ms)", "Max (ms)");
    std::printf("%-14.3f %-14.3f %-14.3f\n\n",
                min_us / 1000.0, median_us / 1000.0, max_us / 1000.0);

    if (median_us / 1000.0 > THRESHOLD_MS) {
        std::fprintf(stderr, "FAIL: median %.3f ms exceeds threshold %.1f ms\n",
                     median_us / 1000.0, THRESHOLD_MS);
        return 1;
    }
    std::printf("PASS: median %.3f ms within %.1f ms threshold\n",
                median_us / 1000.0, THRESHOLD_MS);
    return 0;
}
