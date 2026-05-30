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
        // Degenerate: default to home orientation (tool along +Z)
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
