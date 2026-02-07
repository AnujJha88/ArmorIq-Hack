---
description: Set up a modern C++ project with CMake, dependencies, and best practices
---

# C++ Project Setup Workflow

## Project Structure

```
project_name/
├── CMakeLists.txt          # Root CMake config
├── cmake/
│   └── FindXXX.cmake       # Custom find modules
├── src/
│   ├── CMakeLists.txt
│   ├── main.cpp
│   └── lib/
│       ├── module.cpp
│       └── module.hpp
├── include/
│   └── project_name/       # Public headers
│       └── api.hpp
├── tests/
│   ├── CMakeLists.txt
│   └── test_module.cpp
├── benchmarks/
│   └── bench_main.cpp
├── third_party/            # External deps (submodules)
├── docs/
├── .clang-format
├── .clang-tidy
├── .gitignore
└── README.md
```

---

## CMake Setup

### Root CMakeLists.txt
```cmake
cmake_minimum_required(VERSION 3.20)
project(ProjectName VERSION 1.0.0 LANGUAGES CXX)

# C++ Standard
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Export compile_commands.json for IDE/tools
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# Build type
if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release)
endif()

# Compiler warnings
if(MSVC)
    add_compile_options(/W4 /WX /permissive-)
else()
    add_compile_options(-Wall -Wextra -Wpedantic -Werror)
endif()

# Options
option(BUILD_TESTS "Build test suite" ON)
option(BUILD_BENCHMARKS "Build benchmarks" OFF)
option(ENABLE_SANITIZERS "Enable ASan/UBSan" OFF)

# Sanitizers (debug builds)
if(ENABLE_SANITIZERS AND NOT MSVC)
    add_compile_options(-fsanitize=address,undefined -fno-omit-frame-pointer)
    add_link_options(-fsanitize=address,undefined)
endif()

# Dependencies
find_package(fmt REQUIRED)          # Or use FetchContent
find_package(Eigen3 REQUIRED)

# Main library
add_subdirectory(src)

# Tests
if(BUILD_TESTS)
    enable_testing()
    add_subdirectory(tests)
endif()

# Benchmarks
if(BUILD_BENCHMARKS)
    add_subdirectory(benchmarks)
endif()
```

### src/CMakeLists.txt
```cmake
# Library target
add_library(mylib
    lib/module.cpp
)

target_include_directories(mylib
    PUBLIC
        $<BUILD_INTERFACE:${CMAKE_SOURCE_DIR}/include>
        $<INSTALL_INTERFACE:include>
    PRIVATE
        ${CMAKE_CURRENT_SOURCE_DIR}
)

target_link_libraries(mylib
    PUBLIC
        Eigen3::Eigen
    PRIVATE
        fmt::fmt
)

# Executable
add_executable(myapp main.cpp)
target_link_libraries(myapp PRIVATE mylib)
```

---

## FetchContent for Dependencies

```cmake
include(FetchContent)

# GoogleTest
FetchContent_Declare(
    googletest
    GIT_REPOSITORY https://github.com/google/googletest.git
    GIT_TAG v1.14.0
)
FetchContent_MakeAvailable(googletest)

# fmt library
FetchContent_Declare(
    fmt
    GIT_REPOSITORY https://github.com/fmtlib/fmt.git
    GIT_TAG 10.2.1
)
FetchContent_MakeAvailable(fmt)

# JSON
FetchContent_Declare(
    json
    GIT_REPOSITORY https://github.com/nlohmann/json.git
    GIT_TAG v3.11.3
)
FetchContent_MakeAvailable(json)
```

---

## Build Commands

### Configure and Build
// turbo
```powershell
# Create build directory
cmake -B build -DCMAKE_BUILD_TYPE=Release

# Build
cmake --build build --config Release -j

# Build specific target
cmake --build build --target myapp
```

### Debug Build with Sanitizers
```powershell
cmake -B build-debug -DCMAKE_BUILD_TYPE=Debug -DENABLE_SANITIZERS=ON
cmake --build build-debug
```

### Run Tests
// turbo
```powershell
cd build
ctest --output-on-failure
```

---

## Code Formatting (.clang-format)

```yaml
---
Language: Cpp
BasedOnStyle: Google
IndentWidth: 4
ColumnLimit: 100
PointerAlignment: Left
ReferenceAlignment: Left
SpaceAfterTemplateKeyword: false
AllowShortFunctionsOnASingleLine: Inline
AllowShortIfStatementsOnASingleLine: Never
AllowShortLoopsOnASingleLine: false
BreakBeforeBraces: Attach
NamespaceIndentation: None
IncludeBlocks: Regroup
IncludeCategories:
  - Regex: '^<.*>'
    Priority: 1
  - Regex: '^".*"'
    Priority: 2
SortIncludes: CaseSensitive
```

// turbo
```powershell
# Format all files
clang-format -i src/**/*.cpp include/**/*.hpp
```

---

## Static Analysis (.clang-tidy)

```yaml
---
Checks: >
  *,
  -fuchsia-*,
  -google-build-using-namespace,
  -llvm-header-guard,
  -modernize-use-trailing-return-type,
  -readability-identifier-length
WarningsAsErrors: ''
HeaderFilterRegex: '.*'
FormatStyle: file
CheckOptions:
  - key: readability-identifier-naming.ClassCase
    value: CamelCase
  - key: readability-identifier-naming.FunctionCase
    value: camelCase
  - key: readability-identifier-naming.VariableCase
    value: lower_case
```

// turbo
```powershell
# Run clang-tidy
clang-tidy src/*.cpp -- -I include -std=c++20
```

---

## .gitignore for C++

```gitignore
# Build directories
build/
build-*/
out/
cmake-build-*/

# Compiled files
*.o
*.obj
*.exe
*.dll
*.so
*.a
*.lib

# IDE
.vs/
.vscode/
*.sln
*.vcxproj*
.idea/
*.swp

# CMake
CMakeCache.txt
CMakeFiles/
cmake_install.cmake
compile_commands.json

# Testing
Testing/

# Package managers
vcpkg_installed/
_deps/
```

---

## vcpkg Integration (Windows-friendly)

```powershell
# Install vcpkg
git clone https://github.com/microsoft/vcpkg.git
.\vcpkg\bootstrap-vcpkg.bat

# Install packages
.\vcpkg\vcpkg install fmt eigen3 catch2

# Use with CMake
cmake -B build -DCMAKE_TOOLCHAIN_FILE=./vcpkg/scripts/buildsystems/vcpkg.cmake
```

---

## Project Template Checklist

- [ ] CMakeLists.txt with proper targets
- [ ] C++20 or C++17 standard set
- [ ] Warnings enabled and treated as errors
- [ ] .clang-format for consistent style
- [ ] .clang-tidy for static analysis
- [ ] Test framework integrated (GoogleTest/Catch2)
- [ ] .gitignore configured
- [ ] README with build instructions
