---
description: Debugging and profiling C++ applications on Windows and Linux
---

# C++ Debugging & Profiling

## Debugging Basics

### Compiler Debug Flags
```cmake
# CMake debug build
set(CMAKE_BUILD_TYPE Debug)

# Manual flags
# MSVC: /Zi /Od /DEBUG
# GCC/Clang: -g -O0
```

### Debug Build
// turbo
```powershell
cmake -B build-debug -DCMAKE_BUILD_TYPE=Debug
cmake --build build-debug
```

---

## Sanitizers (Catch Bugs at Runtime)

### Address Sanitizer (ASan) - Memory Errors
```cmake
# CMake
if(ENABLE_ASAN)
    add_compile_options(-fsanitize=address -fno-omit-frame-pointer)
    add_link_options(-fsanitize=address)
endif()
```

Catches:
- Buffer overflows
- Use-after-free
- Memory leaks
- Double-free

### Undefined Behavior Sanitizer (UBSan)
```cmake
add_compile_options(-fsanitize=undefined)
add_link_options(-fsanitize=undefined)
```

Catches:
- Integer overflow
- Null pointer dereference
- Misaligned access
- Out-of-bounds array access

### Thread Sanitizer (TSan) - Data Races
```cmake
add_compile_options(-fsanitize=thread)
add_link_options(-fsanitize=thread)
```

### Combined (Development Builds)
```cmake
option(ENABLE_SANITIZERS "Enable sanitizers" OFF)

if(ENABLE_SANITIZERS AND NOT MSVC)
    add_compile_options(
        -fsanitize=address,undefined
        -fno-omit-frame-pointer
        -fno-optimize-sibling-calls
    )
    add_link_options(-fsanitize=address,undefined)
endif()
```

---

## Visual Studio Debugging (Windows)

### Debug with VS
```powershell
# Generate VS solution
cmake -B build -G "Visual Studio 17 2022"

# Open in VS
start build/ProjectName.sln
```

### Key VS Debugger Features
- F5: Start debugging
- F9: Toggle breakpoint
- F10: Step over
- F11: Step into
- Shift+F11: Step out
- Watch window for variables
- Immediate window for expressions

### Conditional Breakpoints
Right-click breakpoint → Conditions:
```cpp
// Break when i equals 42
i == 42

// Break when string contains "error"
str.find("error") != std::string::npos
```

---

## GDB/LLDB Debugging (CLI)

### Basic GDB Commands
```bash
# Start debugging
gdb ./myapp

# Common commands
break main          # Set breakpoint at main
break file.cpp:42   # Breakpoint at line
run                 # Start program
run arg1 arg2       # With arguments

next (n)            # Step over
step (s)            # Step into
continue (c)        # Continue to next breakpoint
finish              # Run until function returns

print var           # Print variable
print *ptr          # Dereference pointer
print arr[0]@10     # Print 10 elements of array

backtrace (bt)      # Show call stack
frame 2             # Switch to frame 2
info locals         # Show local variables

watch var           # Break when var changes
quit                # Exit
```

### GDB with Core Dumps
```bash
# Enable core dumps
ulimit -c unlimited

# Debug core dump
gdb ./myapp core
```

---

## Printf Debugging (Quick & Dirty)

### Modern C++ Logging
```cpp
// Using fmt library (or std::format in C++20)
#include <fmt/core.h>
#include <fmt/ranges.h>

#define DEBUG_LOG(msg, ...) \
    fmt::print(stderr, "[DEBUG {}:{}] " msg "\n", \
               __FILE__, __LINE__, ##__VA_ARGS__)

void someFunction() {
    std::vector<int> v = {1, 2, 3};
    DEBUG_LOG("v = {}", v);
    DEBUG_LOG("size = {}, capacity = {}", v.size(), v.capacity());
}
```

### Macro-Based Debug Output
```cpp
#ifdef NDEBUG
    #define DEBUG_PRINT(x) ((void)0)
#else
    #define DEBUG_PRINT(x) do { std::cerr << #x << " = " << (x) << std::endl; } while(0)
#endif

// Usage
int value = compute();
DEBUG_PRINT(value);  // Prints: value = 42
```

---

## Profiling

### Timing Code
```cpp
#include <chrono>

class Timer {
public:
    Timer() : start_(std::chrono::high_resolution_clock::now()) {}
    
    double elapsed() const {
        auto end = std::chrono::high_resolution_clock::now();
        return std::chrono::duration<double>(end - start_).count();
    }
    
    void reset() { start_ = std::chrono::high_resolution_clock::now(); }

private:
    std::chrono::time_point<std::chrono::high_resolution_clock> start_;
};

// Usage
Timer timer;
doExpensiveWork();
std::cout << "Elapsed: " << timer.elapsed() << "s\n";
```

### RAII Scoped Timer
```cpp
class ScopedTimer {
public:
    explicit ScopedTimer(std::string name) 
        : name_(std::move(name)), start_(std::chrono::high_resolution_clock::now()) {}
    
    ~ScopedTimer() {
        auto end = std::chrono::high_resolution_clock::now();
        auto duration = std::chrono::duration<double, std::milli>(end - start_).count();
        std::cout << name_ << ": " << duration << " ms\n";
    }

private:
    std::string name_;
    std::chrono::time_point<std::chrono::high_resolution_clock> start_;
};

// Usage
void complexFunction() {
    ScopedTimer timer("complexFunction");
    // ... work ...
}  // Automatically prints timing on exit
```

### Visual Studio Profiler
```
Debug → Performance Profiler → CPU Usage
```

### perf (Linux)
```bash
# Record profile
perf record -g ./myapp

# View report
perf report

# Flame graph
perf script | stackcollapse-perf.pl | flamegraph.pl > flame.svg
```

---

## Memory Profiling

### Valgrind (Linux)
```bash
# Memory errors
valgrind --leak-check=full ./myapp

# Cache profiling
valgrind --tool=cachegrind ./myapp
cg_annotate cachegrind.out.*

# Call graph
valgrind --tool=callgrind ./myapp
kcachegrind callgrind.out.*
```

### Visual Studio Memory Tools
- Debug → Windows → Memory Usage
- Diagnostic Tools (F5 debugging)

### Custom Memory Tracking
```cpp
#include <cstdlib>

// Override global new/delete
void* operator new(std::size_t size) {
    std::cout << "Allocating " << size << " bytes\n";
    void* p = std::malloc(size);
    if (!p) throw std::bad_alloc();
    return p;
}

void operator delete(void* p) noexcept {
    std::cout << "Deallocating memory\n";
    std::free(p);
}
```

---

## Common Bug Patterns

### Buffer Overflow
```cpp
// Bug
int arr[10];
arr[10] = 42;  // Out of bounds!

// Fix: Use .at() or range-for
std::array<int, 10> arr;
arr.at(10) = 42;  // Throws std::out_of_range
```

### Use After Free
```cpp
// Bug
int* p = new int(42);
delete p;
*p = 10;  // Undefined behavior!

// Fix: Use smart pointers
auto p = std::make_unique<int>(42);
// Automatically managed
```

### Data Race
```cpp
// Bug
int counter = 0;
std::thread t1([&]() { counter++; });
std::thread t2([&]() { counter++; });

// Fix: Use atomic or mutex
std::atomic<int> counter{0};
```

### Iterator Invalidation
```cpp
// Bug
std::vector<int> v = {1, 2, 3, 4, 5};
for (auto it = v.begin(); it != v.end(); ++it) {
    if (*it == 3) {
        v.erase(it);  // Invalidates it!
    }
}

// Fix: Use erase-remove idiom
v.erase(std::remove(v.begin(), v.end(), 3), v.end());

// Or C++20
std::erase(v, 3);
```

---

## Quick Debug Checklist

- [ ] Build with debug symbols (-g / /Zi)
- [ ] Enable sanitizers in debug builds
- [ ] Check with valgrind (Linux) or Dr. Memory (Windows)
- [ ] Use assertions for invariants
- [ ] Test edge cases (empty inputs, max values)
- [ ] Run static analyzer (clang-tidy)
- [ ] Profile before optimizing
