#pragma once
#include "types.hpp"

class IKSolver {
public:
    explicit IKSolver(const MachineConfig& cfg);
    IKResult solve(const Point3& pos, const Point3& raw_tangent) const;

private:
    MachineConfig cfg_;
};
