#include <catch2/catch_test_macros.hpp>
#include <catch2/catch_approx.hpp>
#include "csv_parser.hpp"

using Catch::Approx;

TEST_CASE("parse two-row CSV with header", "[csv]") {
    std::string s = "x,y,z\n1.0,2.0,3.0\n4.0,5.0,6.0\n";
    auto pts = CsvParser::parseString(s);
    REQUIRE(pts.size() == 2);
    CHECK(pts[0].x == Approx(1.0));
    CHECK(pts[0].y == Approx(2.0));
    CHECK(pts[0].z == Approx(3.0));
    CHECK(pts[1].z == Approx(6.0));
}

TEST_CASE("parse CSV without header", "[csv]") {
    std::string s = "1.0,2.0,3.0\n4.0,5.0,6.0\n";
    auto pts = CsvParser::parseString(s);
    REQUIRE(pts.size() == 2);
    CHECK(pts[0].x == Approx(1.0));
}

TEST_CASE("trailing newline does not produce extra row", "[csv]") {
    std::string s = "1.0,2.0,3.0\n";
    auto pts = CsvParser::parseString(s);
    REQUIRE(pts.size() == 1);
}

TEST_CASE("throws on row with fewer than 3 values", "[csv]") {
    std::string s = "1.0,2.0\n";
    REQUIRE_THROWS(CsvParser::parseString(s));
}

TEST_CASE("throws on non-numeric value", "[csv]") {
    std::string s = "1.0,abc,3.0\n";
    REQUIRE_THROWS(CsvParser::parseString(s));
}
