#pragma once
#include "types.hpp"
#include <vector>

class CubicSpline {
public:
    explicit CubicSpline(const std::vector<Point3>& ctrl_pts);
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
