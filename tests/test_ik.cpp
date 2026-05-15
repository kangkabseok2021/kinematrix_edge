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

TEST_CASE("tangent along -Y gives A=90 B=0", "[ik]") {
    IKSolver ik(testCfg());
    IKResult r = ik.solve({0, 0, 0}, {0, -1, 0});
    CHECK(r.a_deg == Approx(90.0));
    CHECK(r.b_deg == Approx(0.0).margin(1e-9));
}

TEST_CASE("motor steps computed correctly from position", "[ik]") {
    // lead=5mm/rev, steps=200 → 1mm = 40 steps
    IKSolver ik(testCfg());
    IKResult r = ik.solve({5.0, 10.0, 2.5}, {0, 0, 1});
    CHECK(r.motors.m1 == 200);  // 5/5*200
    CHECK(r.motors.m2 == 400);  // 10/5*200
    CHECK(r.motors.m3 == 100);  // 2.5/5*200
    CHECK(r.motors.m4 == 0);    // A=0
    CHECK(r.motors.m5 == 0);    // B=0
}

TEST_CASE("diagonal tangent (1,0,1) gives B=45 A=0", "[ik]") {
    IKSolver ik(testCfg());
    IKResult r = ik.solve({0, 0, 0}, {1, 0, 1});
    CHECK(r.b_deg == Approx(45.0));
    CHECK(r.a_deg == Approx(0.0));
}
