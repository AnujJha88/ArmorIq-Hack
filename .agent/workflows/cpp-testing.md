---
description: Testing C++ code with GoogleTest and Catch2 frameworks
---

# C++ Testing Workflow

## Setup

### GoogleTest (via CMake FetchContent)
```cmake
include(FetchContent)
FetchContent_Declare(
    googletest
    GIT_REPOSITORY https://github.com/google/googletest.git
    GIT_TAG v1.14.0
)
set(gtest_force_shared_crt ON CACHE BOOL "" FORCE)
FetchContent_MakeAvailable(googletest)

enable_testing()

add_executable(tests
    test_main.cpp
    test_module.cpp
)

target_link_libraries(tests
    PRIVATE
        GTest::gtest_main
        GTest::gmock
        mylib
)

include(GoogleTest)
gtest_discover_tests(tests)
```

### Catch2 (Header-only alternative)
```cmake
FetchContent_Declare(
    Catch2
    GIT_REPOSITORY https://github.com/catchorg/Catch2.git
    GIT_TAG v3.5.2
)
FetchContent_MakeAvailable(Catch2)

target_link_libraries(tests PRIVATE Catch2::Catch2WithMain)
```

---

## GoogleTest Basics

### Simple Tests
```cpp
#include <gtest/gtest.h>

// Basic test
TEST(CalculatorTest, Add) {
    EXPECT_EQ(add(2, 3), 5);
    EXPECT_EQ(add(-1, 1), 0);
}

// Multiple assertions
TEST(StringTest, Concatenation) {
    std::string a = "Hello";
    std::string b = "World";
    std::string result = a + " " + b;
    
    EXPECT_EQ(result, "Hello World");
    EXPECT_EQ(result.size(), 11);
    EXPECT_TRUE(result.starts_with("Hello"));
}
```

### Assertions
```cpp
// Fatal (stops test)
ASSERT_EQ(a, b);
ASSERT_NE(a, b);
ASSERT_TRUE(condition);
ASSERT_FALSE(condition);

// Non-fatal (continues)
EXPECT_EQ(a, b);
EXPECT_NE(a, b);
EXPECT_LT(a, b);    // <
EXPECT_LE(a, b);    // <=
EXPECT_GT(a, b);    // >
EXPECT_GE(a, b);    // >=

// Floating point
EXPECT_FLOAT_EQ(a, b);
EXPECT_DOUBLE_EQ(a, b);
EXPECT_NEAR(a, b, tolerance);

// Strings
EXPECT_STREQ(cstr1, cstr2);
EXPECT_THAT(str, testing::HasSubstr("substring"));

// Exceptions
EXPECT_THROW(func(), ExceptionType);
EXPECT_ANY_THROW(func());
EXPECT_NO_THROW(func());
```

### Test Fixtures
```cpp
class DatabaseTest : public ::testing::Test {
protected:
    void SetUp() override {
        db = std::make_unique<Database>();
        db->connect("test.db");
    }
    
    void TearDown() override {
        db->disconnect();
    }
    
    std::unique_ptr<Database> db;
};

TEST_F(DatabaseTest, Insert) {
    EXPECT_TRUE(db->insert("key", "value"));
}

TEST_F(DatabaseTest, Retrieve) {
    db->insert("key", "value");
    EXPECT_EQ(db->get("key"), "value");
}
```

### Parameterized Tests
```cpp
class AddTest : public ::testing::TestWithParam<std::tuple<int, int, int>> {};

TEST_P(AddTest, ReturnsCorrectSum) {
    auto [a, b, expected] = GetParam();
    EXPECT_EQ(add(a, b), expected);
}

INSTANTIATE_TEST_SUITE_P(
    AdditionTests,
    AddTest,
    ::testing::Values(
        std::make_tuple(1, 2, 3),
        std::make_tuple(0, 0, 0),
        std::make_tuple(-1, 1, 0),
        std::make_tuple(100, 200, 300)
    )
);
```

---

## GMock (Mocking)

```cpp
#include <gmock/gmock.h>

// Interface
class Database {
public:
    virtual ~Database() = default;
    virtual bool connect(const std::string& url) = 0;
    virtual std::string query(const std::string& sql) = 0;
};

// Mock
class MockDatabase : public Database {
public:
    MOCK_METHOD(bool, connect, (const std::string& url), (override));
    MOCK_METHOD(std::string, query, (const std::string& sql), (override));
};

// Test with mock
TEST(ServiceTest, UsesDatabase) {
    MockDatabase mockDb;
    
    EXPECT_CALL(mockDb, connect("localhost"))
        .WillOnce(testing::Return(true));
    
    EXPECT_CALL(mockDb, query(testing::HasSubstr("SELECT")))
        .WillOnce(testing::Return("result"));
    
    Service service(&mockDb);
    EXPECT_EQ(service.getData(), "result");
}
```

---

## Catch2 Basics

```cpp
#include <catch2/catch_test_macros.hpp>
#include <catch2/catch_approx.hpp>

TEST_CASE("Vector operations", "[vector]") {
    std::vector<int> v;
    
    REQUIRE(v.empty());
    
    SECTION("push_back increases size") {
        v.push_back(1);
        REQUIRE(v.size() == 1);
    }
    
    SECTION("clear empties vector") {
        v.push_back(1);
        v.clear();
        REQUIRE(v.empty());
    }
}

// Floating point comparison
TEST_CASE("Floating point", "[math]") {
    double result = compute();
    REQUIRE(result == Catch::Approx(3.14159).epsilon(0.01));
}

// BDD style
SCENARIO("User login", "[auth]") {
    GIVEN("a registered user") {
        User user("test@test.com", "password");
        
        WHEN("they login with correct password") {
            auto result = user.login("password");
            
            THEN("they are authenticated") {
                REQUIRE(result.success);
            }
        }
        
        WHEN("they login with wrong password") {
            auto result = user.login("wrong");
            
            THEN("they are rejected") {
                REQUIRE_FALSE(result.success);
            }
        }
    }
}
```

---

## Running Tests

// turbo
```powershell
# Build tests
cmake --build build --target tests

# Run all tests
cd build
ctest --output-on-failure

# Run specific test
./tests --gtest_filter="CalculatorTest.*"

# Run with verbose output
./tests --gtest_filter="*" --gtest_print_time=1
```

---

## Test Organization

```
tests/
├── CMakeLists.txt
├── test_main.cpp       # Optional: custom main
├── unit/
│   ├── test_math.cpp
│   └── test_string.cpp
├── integration/
│   └── test_database.cpp
└── fixtures/
    └── test_data.json
```

```cpp
// test_main.cpp (optional custom main)
#include <gtest/gtest.h>

int main(int argc, char** argv) {
    ::testing::InitGoogleTest(&argc, argv);
    // Custom setup here
    return RUN_ALL_TESTS();
}
```
