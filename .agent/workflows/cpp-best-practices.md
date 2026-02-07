---
description: Modern C++ idioms, patterns, and best practices for clean, safe code
---

# Modern C++ Best Practices

## Memory Management

### Smart Pointers (Never use raw new/delete)
```cpp
#include <memory>

// Unique ownership (default choice)
auto ptr = std::make_unique<MyClass>(args...);

// Shared ownership (when truly needed)
auto shared = std::make_shared<MyClass>(args...);

// Weak reference (break cycles)
std::weak_ptr<MyClass> weak = shared;
if (auto locked = weak.lock()) {
    locked->doSomething();
}

// Factory function pattern
std::unique_ptr<Base> createObject(Type type) {
    switch (type) {
        case Type::A: return std::make_unique<DerivedA>();
        case Type::B: return std::make_unique<DerivedB>();
    }
}
```

### RAII (Resource Acquisition Is Initialization)
```cpp
class FileHandle {
public:
    explicit FileHandle(const std::string& path) 
        : handle_(std::fopen(path.c_str(), "r")) {
        if (!handle_) throw std::runtime_error("Failed to open file");
    }
    
    ~FileHandle() {
        if (handle_) std::fclose(handle_);
    }
    
    // Delete copy
    FileHandle(const FileHandle&) = delete;
    FileHandle& operator=(const FileHandle&) = delete;
    
    // Allow move
    FileHandle(FileHandle&& other) noexcept : handle_(other.handle_) {
        other.handle_ = nullptr;
    }
    
    FileHandle& operator=(FileHandle&& other) noexcept {
        if (this != &other) {
            if (handle_) std::fclose(handle_);
            handle_ = other.handle_;
            other.handle_ = nullptr;
        }
        return *this;
    }

private:
    FILE* handle_;
};
```

---

## Modern C++ Features

### Auto and Type Deduction
```cpp
// Use auto for complex types
auto it = container.begin();
auto lambda = [](int x) { return x * 2; };
auto ptr = std::make_unique<MyClass>();

// Trailing return type for complex returns
template<typename T, typename U>
auto add(T t, U u) -> decltype(t + u) {
    return t + u;
}

// C++14: return type deduction
template<typename T>
auto square(T x) {
    return x * x;
}
```

### Range-based For Loops
```cpp
std::vector<int> vec = {1, 2, 3, 4, 5};

// Read-only
for (const auto& item : vec) {
    std::cout << item << '\n';
}

// Modify
for (auto& item : vec) {
    item *= 2;
}

// With structured bindings (C++17)
std::map<std::string, int> map = {{"a", 1}, {"b", 2}};
for (const auto& [key, value] : map) {
    std::cout << key << ": " << value << '\n';
}
```

### Structured Bindings (C++17)
```cpp
// Tuples
auto [x, y, z] = std::make_tuple(1, 2.0, "three");

// Pairs
std::map<int, std::string> m;
auto [iter, inserted] = m.insert({1, "one"});

// Structs
struct Point { double x, y; };
Point p{1.0, 2.0};
auto [px, py] = p;

// Arrays
int arr[] = {1, 2, 3};
auto [a, b, c] = arr;
```

### Optional, Variant, Any (C++17)
```cpp
#include <optional>
#include <variant>
#include <any>

// Optional - nullable value
std::optional<int> findValue(int key) {
    if (/* found */) return value;
    return std::nullopt;
}

if (auto result = findValue(42)) {
    std::cout << *result << '\n';
}

// Variant - type-safe union
std::variant<int, double, std::string> v;
v = 42;
v = 3.14;
v = "hello";

std::visit([](auto&& arg) {
    std::cout << arg << '\n';
}, v);

// Any - type-erased container
std::any a = 42;
a = std::string("hello");
try {
    auto s = std::any_cast<std::string>(a);
} catch (const std::bad_any_cast&) {}
```

---

## Containers & Algorithms

### Choose the Right Container
```cpp
// Sequential
std::vector<T>          // Default choice, cache-friendly
std::array<T, N>        // Fixed size, stack allocated
std::deque<T>           // Fast front/back insert
std::list<T>            // Stable iterators, frequent middle insert

// Associative
std::unordered_map<K,V> // O(1) average lookup (default choice)
std::map<K,V>           // Ordered keys, O(log n)
std::unordered_set<T>   // O(1) membership test
std::set<T>             // Ordered, O(log n)

// Special
std::string_view        // Non-owning string reference
std::span<T>            // Non-owning array view (C++20)
```

### Modern Algorithm Usage
```cpp
#include <algorithm>
#include <ranges>  // C++20

std::vector<int> v = {5, 2, 8, 1, 9};

// Sort
std::ranges::sort(v);

// Find
if (auto it = std::ranges::find(v, 5); it != v.end()) {
    // found
}

// Transform
std::vector<int> squared;
std::ranges::transform(v, std::back_inserter(squared),
    [](int x) { return x * x; });

// Filter (C++20 ranges)
auto evens = v | std::views::filter([](int x) { return x % 2 == 0; });

// Chained operations
auto result = v 
    | std::views::filter([](int x) { return x > 3; })
    | std::views::transform([](int x) { return x * 2; });

// Parallel algorithms (C++17)
#include <execution>
std::sort(std::execution::par, v.begin(), v.end());
```

---

## Error Handling

### Exceptions Best Practices
```cpp
// Define custom exceptions
class MyError : public std::runtime_error {
public:
    explicit MyError(const std::string& msg) : std::runtime_error(msg) {}
};

// Use noexcept for functions that don't throw
void safeFunction() noexcept {
    // Guaranteed not to throw
}

// Exception-safe code (strong guarantee)
void safePush(std::vector<Widget>& v, Widget w) {
    v.push_back(std::move(w));  // vector provides strong guarantee
}
```

### std::expected (C++23) or Result Pattern
```cpp
// Result type pattern (pre-C++23)
template<typename T, typename E = std::string>
class Result {
public:
    static Result ok(T value) { return Result(std::move(value)); }
    static Result err(E error) { return Result(std::move(error), false); }
    
    bool isOk() const { return is_ok_; }
    T& value() { return std::get<T>(data_); }
    E& error() { return std::get<E>(data_); }

private:
    std::variant<T, E> data_;
    bool is_ok_;
};

Result<int> divide(int a, int b) {
    if (b == 0) return Result<int>::err("Division by zero");
    return Result<int>::ok(a / b);
}
```

---

## Concurrency

### Threads and Async
```cpp
#include <thread>
#include <future>
#include <mutex>

// Basic thread
std::thread t([]() {
    std::cout << "Hello from thread\n";
});
t.join();

// Async (prefer over raw threads)
auto future = std::async(std::launch::async, []() {
    return computeExpensiveThing();
});
auto result = future.get();  // Blocks until ready

// Mutex
std::mutex mtx;
{
    std::lock_guard<std::mutex> lock(mtx);
    // Critical section
}

// Multiple locks (avoid deadlock)
std::scoped_lock lock(mutex1, mutex2);
```

### Atomic Operations
```cpp
#include <atomic>

std::atomic<int> counter{0};

// Thread-safe increment
counter.fetch_add(1, std::memory_order_relaxed);

// Compare and swap
int expected = 0;
counter.compare_exchange_strong(expected, 1);
```

---

## Class Design

### Rule of Zero/Five
```cpp
// Rule of Zero: If you don't manage resources, don't define special members
struct SimpleClass {
    std::string name;
    std::vector<int> data;
    // Compiler-generated defaults are fine
};

// Rule of Five: If you define one, define all
class ResourceOwner {
public:
    ResourceOwner();
    ~ResourceOwner();
    ResourceOwner(const ResourceOwner&);
    ResourceOwner& operator=(const ResourceOwner&);
    ResourceOwner(ResourceOwner&&) noexcept;
    ResourceOwner& operator=(ResourceOwner&&) noexcept;
};
```

### Constructor Best Practices
```cpp
class Widget {
public:
    // Explicit for single-argument constructors
    explicit Widget(int size);
    
    // Use member initializer lists
    Widget(int x, int y) : x_(x), y_(y) {}
    
    // Delegating constructors
    Widget() : Widget(0, 0) {}
    
    // = default for trivial implementations
    Widget(const Widget&) = default;
    
    // = delete to prevent certain operations
    Widget& operator=(const Widget&) = delete;

private:
    int x_, y_;
};
```

---

## Performance Tips

### Move Semantics
```cpp
// Return by value (RVO/NRVO applies)
std::vector<int> createVector() {
    std::vector<int> v;
    v.reserve(1000);
    // ... populate
    return v;  // Moved or elided, not copied
}

// Take by value and move
class Container {
public:
    void add(std::string s) {  // Take by value
        data_.push_back(std::move(s));  // Move into container
    }
private:
    std::vector<std::string> data_;
};
```

### Avoid Copies
```cpp
// Pass large objects by const reference
void process(const std::vector<int>& data);

// Use string_view for read-only strings
void print(std::string_view sv);

// Reserve capacity
std::vector<int> v;
v.reserve(1000);  // Avoid reallocations
```

---

## Quick Reference

```cpp
// Essential headers
#include <vector>
#include <string>
#include <string_view>
#include <memory>
#include <optional>
#include <variant>
#include <algorithm>
#include <ranges>        // C++20
#include <span>          // C++20
#include <format>        // C++20
#include <concepts>      // C++20

// Prefer
std::array over C arrays
std::string_view over const std::string&
std::span over pointer+size
std::make_unique over new
std::variant over union
enum class over enum
nullptr over NULL
```
