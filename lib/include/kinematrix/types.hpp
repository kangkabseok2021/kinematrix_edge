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
