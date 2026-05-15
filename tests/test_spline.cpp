#include <catch2/catch_test_macros.hpp>
#include <catch2/catch_approx.hpp>
#include "kinematrix/spline.hpp"
#include <vector>

using Catch::Approx;

TEST_CASE("throws on fewer than 2 control points", "[spline]") {
    std::vector<Point3> pts = {{0, 0, 0}};
    REQUIRE_THROWS_AS(CubicSpline(pts), std::invalid_argument);
}

TEST_CASE("two-point linear: output count is points_per_segment", "[spline]") {
    std::vector<Point3> pts = {{0, 0, 0}, {2, 0, 0}};
    CubicSpline s(pts);
    auto result = s.interpolate(4);
    REQUIRE(result.size() == 4);
}

TEST_CASE("two-point linear: positions are uniformly spaced along X", "[spline]") {
    std::vector<Point3> pts = {{0, 0, 0}, {2, 0, 0}};
    CubicSpline s(pts);
    auto result = s.interpolate(4);
    CHECK(result[0].pos.x == Approx(0.0));
    CHECK(result[1].pos.x == Approx(0.5));
    CHECK(result[2].pos.x == Approx(1.0));
    CHECK(result[3].pos.x == Approx(1.5));
}

TEST_CASE("two-point linear: tangents point along segment direction", "[spline]") {
    std::vector<Point3> pts = {{0, 0, 0}, {2, 0, 0}};
    CubicSpline s(pts);
    auto result = s.interpolate(4);
    for (auto& sp : result) {
        CHECK(sp.tangent.x == Approx(2.0));
        CHECK(sp.tangent.y == Approx(0.0));
        CHECK(sp.tangent.z == Approx(0.0));
    }
}

TEST_CASE("three collinear points produce zero Y and Z deviation", "[spline]") {
    std::vector<Point3> pts = {{0, 0, 0}, {1, 0, 0}, {2, 0, 0}};
    CubicSpline s(pts);
    auto result = s.interpolate(10);
    for (auto& sp : result) {
        CHECK(sp.pos.y == Approx(0.0).margin(1e-10));
        CHECK(sp.pos.z == Approx(0.0).margin(1e-10));
    }
}

TEST_CASE("output size is (N-1) * points_per_segment", "[spline]") {
    std::vector<Point3> pts = {
        {0,0,0}, {1,1,0}, {2,0,0}, {3,1,0}, {4,0,0}
    };
    CubicSpline s(pts);
    auto result = s.interpolate(7);
    REQUIRE(result.size() == 4 * 7);
}
