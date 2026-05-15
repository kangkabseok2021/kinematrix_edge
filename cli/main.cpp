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
