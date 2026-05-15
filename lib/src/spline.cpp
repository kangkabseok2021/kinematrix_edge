#include "kinematrix/spline.hpp"
#include <stdexcept>

CubicSpline::CubicSpline(const std::vector<Point3>& pts) {
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

// Thomas algorithm: solves the natural cubic spline second-derivative system.
// Tridiagonal: sub=1, main=4, super=1; natural BCs: M[0]=M[n-1]=0.
std::vector<double> CubicSpline::computeM(const std::vector<double>& y) {
    int n = static_cast<int>(y.size());
    std::vector<double> M(n, 0.0);
    if (n <= 2) return M;

    int m = n - 2;  // unknowns: M[1]..M[n-2]

    std::vector<double> r(m);
    for (int i = 0; i < m; ++i)
        r[i] = 6.0 * (y[i] - 2.0 * y[i + 1] + y[i + 2]);

    // Forward sweep
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

// Evaluate position on segment i at local parameter u in [0,1).
double CubicSpline::evalAxis(const std::vector<double>& y,
                              const std::vector<double>& M, int i, double u) {
    double b = (y[i + 1] - y[i]) - (2.0 * M[i] + M[i + 1]) / 6.0;
    double c = M[i] / 2.0;
    double d = (M[i + 1] - M[i]) / 6.0;
    return y[i] + u * (b + u * (c + u * d));
}

// Analytic first derivative S'(u) = b + 2c*u + 3d*u².
double CubicSpline::derivAxis(const std::vector<double>& y,
                               const std::vector<double>& M, int i, double u) {
    double b = (y[i + 1] - y[i]) - (2.0 * M[i] + M[i + 1]) / 6.0;
    double c = M[i] / 2.0;
    double d = (M[i + 1] - M[i]) / 6.0;
    return b + u * (2.0 * c + u * 3.0 * d);
}

std::vector<SplinePoint> CubicSpline::interpolate(int pps) const {
    std::vector<SplinePoint> result;
    result.reserve(static_cast<std::size_t>((n_ - 1) * pps));

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
