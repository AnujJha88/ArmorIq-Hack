---
description: Numerical computing and scientific C++ with Eigen, performance optimization, and numerical methods
---

# Scientific & Numerical C++

## Libraries Setup

### Essential Libraries
```cmake
# CMakeLists.txt
find_package(Eigen3 REQUIRED)
find_package(OpenMP)

target_link_libraries(mylib
    PUBLIC
        Eigen3::Eigen
    PRIVATE
        OpenMP::OpenMP_CXX
)
```

// turbo
```powershell
# Install via vcpkg
vcpkg install eigen3 boost-math
```

---

## Eigen Basics (Linear Algebra)

### Vectors and Matrices
```cpp
#include <Eigen/Dense>

using Eigen::MatrixXd;
using Eigen::VectorXd;
using Eigen::Matrix3d;
using Eigen::Vector3d;

// Dynamic size
MatrixXd A(3, 3);
VectorXd v(3);

// Fixed size (faster for small matrices)
Matrix3d B;
Vector3d u;

// Initialization
A << 1, 2, 3,
     4, 5, 6,
     7, 8, 9;

v << 1, 2, 3;

// Special matrices
MatrixXd I = MatrixXd::Identity(3, 3);
MatrixXd Z = MatrixXd::Zero(3, 3);
MatrixXd R = MatrixXd::Random(3, 3);
```

### Operations
```cpp
// Arithmetic
MatrixXd C = A + B;
MatrixXd D = A * B;     // Matrix multiplication
MatrixXd E = A.array() * B.array();  // Element-wise

// Transpose, inverse
MatrixXd At = A.transpose();
MatrixXd Ainv = A.inverse();

// Dot and cross product
double dot = u.dot(v);
Vector3d cross = u.cross(v);

// Norms
double norm = v.norm();
double sqnorm = v.squaredNorm();

// Reductions
double sum = A.sum();
double mean = A.mean();
double max = A.maxCoeff();
```

### Solving Linear Systems
```cpp
// Ax = b

// LU decomposition (general)
VectorXd x = A.lu().solve(b);

// Cholesky (symmetric positive definite)
VectorXd x = A.llt().solve(b);

// QR (least squares)
VectorXd x = A.colPivHouseholderQr().solve(b);

// SVD (robust)
VectorXd x = A.bdcSvd(Eigen::ComputeThinU | Eigen::ComputeThinV).solve(b);
```

### Eigenvalues
```cpp
Eigen::SelfAdjointEigenSolver<MatrixXd> solver(A);
VectorXd eigenvalues = solver.eigenvalues();
MatrixXd eigenvectors = solver.eigenvectors();
```

---

## Numerical Methods

### Root Finding (Newton-Raphson)
```cpp
template<typename F, typename DF>
double newton_raphson(F f, DF df, double x0, double tol = 1e-10, int max_iter = 100) {
    double x = x0;
    for (int i = 0; i < max_iter; ++i) {
        double fx = f(x);
        if (std::abs(fx) < tol) return x;
        x -= fx / df(x);
    }
    throw std::runtime_error("Newton-Raphson did not converge");
}

// Usage
auto f = [](double x) { return x*x - 2; };
auto df = [](double x) { return 2*x; };
double sqrt2 = newton_raphson(f, df, 1.0);
```

### Numerical Integration (Simpson's Rule)
```cpp
template<typename F>
double simpson(F f, double a, double b, int n = 1000) {
    double h = (b - a) / n;
    double sum = f(a) + f(b);
    
    for (int i = 1; i < n; i += 2) {
        sum += 4 * f(a + i * h);
    }
    for (int i = 2; i < n; i += 2) {
        sum += 2 * f(a + i * h);
    }
    
    return sum * h / 3;
}
```

### ODE Solver (RK4)
```cpp
template<typename F>
std::vector<double> rk4(F f, double y0, double t0, double t1, double dt) {
    std::vector<double> result;
    double y = y0;
    double t = t0;
    
    while (t <= t1) {
        result.push_back(y);
        
        double k1 = f(t, y);
        double k2 = f(t + dt/2, y + dt*k1/2);
        double k3 = f(t + dt/2, y + dt*k2/2);
        double k4 = f(t + dt, y + dt*k3);
        
        y += dt * (k1 + 2*k2 + 2*k3 + k4) / 6;
        t += dt;
    }
    
    return result;
}
```

---

## Random Number Generation

### Modern C++ Random
```cpp
#include <random>

// Generator (seed once, reuse)
std::mt19937_64 rng(std::random_device{}());

// Distributions
std::uniform_real_distribution<double> uniform(0.0, 1.0);
std::normal_distribution<double> normal(0.0, 1.0);  // N(μ=0, σ=1)
std::exponential_distribution<double> exponential(1.0);

// Generate
double u = uniform(rng);
double z = normal(rng);

// Vectorized generation
VectorXd random_normal(int n) {
    static std::mt19937_64 rng(42);
    static std::normal_distribution<double> dist(0.0, 1.0);
    
    VectorXd v(n);
    for (int i = 0; i < n; ++i) {
        v[i] = dist(rng);
    }
    return v;
}
```

---

## Performance Optimization

### Compiler Optimization Flags
```cmake
# Release flags
set(CMAKE_CXX_FLAGS_RELEASE "-O3 -march=native -DNDEBUG")

# For numerical code
add_compile_options(-ffast-math)  # Be careful: breaks IEEE compliance
```

### Eigen Optimization
```cpp
// Use fixed-size matrices when possible (< 16 elements)
Eigen::Matrix4d M;  // Faster than MatrixXd(4,4)

// Avoid temporaries
// Bad
VectorXd v = A * B * C * x;

// Good (Eigen evaluates lazily)
VectorXd v = (A * B * C) * x;

// Even better for repeated operations
MatrixXd ABC = A * B * C;  // Precompute

// Use .noalias() for known non-aliasing
C.noalias() = A * B;  // Avoids temporary
```

### Cache-Friendly Access
```cpp
// Row-major iteration for Eigen (default is column-major)
for (int col = 0; col < A.cols(); ++col) {
    for (int row = 0; row < A.rows(); ++row) {
        // Process A(row, col)
    }
}

// Or use row-major storage
Eigen::Matrix<double, Eigen::Dynamic, Eigen::Dynamic, Eigen::RowMajor> A;
```

### SIMD with Eigen
```cpp
// Eigen uses SIMD automatically for aligned data
// Ensure alignment
Eigen::Matrix4d A;  // Automatically aligned

// For dynamic matrices in containers
std::vector<MatrixXd, Eigen::aligned_allocator<MatrixXd>> matrices;
```

### OpenMP Parallelization
```cpp
#include <omp.h>

// Parallel for
#pragma omp parallel for
for (int i = 0; i < n; ++i) {
    result[i] = compute(data[i]);
}

// Reduction
double sum = 0.0;
#pragma omp parallel for reduction(+:sum)
for (int i = 0; i < n; ++i) {
    sum += data[i];
}

// Eigen with OpenMP
Eigen::setNbThreads(4);
MatrixXd C = A * B;  // Parallelized automatically
```

---

## Financial/Option Pricing Specifics

### Black-Scholes
```cpp
#include <cmath>

double normal_cdf(double x) {
    return 0.5 * std::erfc(-x * M_SQRT1_2);
}

double black_scholes_call(double S, double K, double r, double sigma, double T) {
    double d1 = (std::log(S/K) + (r + 0.5*sigma*sigma)*T) / (sigma * std::sqrt(T));
    double d2 = d1 - sigma * std::sqrt(T);
    return S * normal_cdf(d1) - K * std::exp(-r*T) * normal_cdf(d2);
}

double black_scholes_put(double S, double K, double r, double sigma, double T) {
    double d1 = (std::log(S/K) + (r + 0.5*sigma*sigma)*T) / (sigma * std::sqrt(T));
    double d2 = d1 - sigma * std::sqrt(T);
    return K * std::exp(-r*T) * normal_cdf(-d2) - S * normal_cdf(-d1);
}
```

### Monte Carlo Simulation
```cpp
double monte_carlo_european_call(double S0, double K, double r, double sigma, 
                                  double T, int n_paths) {
    std::mt19937_64 rng(42);
    std::normal_distribution<double> normal(0.0, 1.0);
    
    double sum_payoff = 0.0;
    double drift = (r - 0.5*sigma*sigma) * T;
    double vol = sigma * std::sqrt(T);
    
    #pragma omp parallel for reduction(+:sum_payoff)
    for (int i = 0; i < n_paths; ++i) {
        double z = normal(rng);
        double ST = S0 * std::exp(drift + vol * z);
        sum_payoff += std::max(ST - K, 0.0);
    }
    
    return std::exp(-r*T) * sum_payoff / n_paths;
}
```

### Greeks (Finite Differences)
```cpp
struct Greeks {
    double delta;
    double gamma;
    double vega;
    double theta;
    double rho;
};

Greeks compute_greeks(double S, double K, double r, double sigma, double T, double h = 0.01) {
    Greeks g;
    
    double price = black_scholes_call(S, K, r, sigma, T);
    
    // Delta: dV/dS
    g.delta = (black_scholes_call(S+h, K, r, sigma, T) - 
               black_scholes_call(S-h, K, r, sigma, T)) / (2*h);
    
    // Gamma: d²V/dS²
    g.gamma = (black_scholes_call(S+h, K, r, sigma, T) - 
               2*price + 
               black_scholes_call(S-h, K, r, sigma, T)) / (h*h);
    
    // Vega: dV/dσ
    g.vega = (black_scholes_call(S, K, r, sigma+h, T) - 
              black_scholes_call(S, K, r, sigma-h, T)) / (2*h);
    
    // Theta: dV/dT
    g.theta = (black_scholes_call(S, K, r, sigma, T-h) - price) / h;
    
    // Rho: dV/dr
    g.rho = (black_scholes_call(S, K, r+h, sigma, T) - 
             black_scholes_call(S, K, r-h, sigma, T)) / (2*h);
    
    return g;
}
```

---

## Quick Reference

```cpp
// Essential includes
#include <Eigen/Dense>
#include <Eigen/Sparse>
#include <cmath>
#include <random>
#include <omp.h>

// Common Eigen types
Eigen::MatrixXd    // Dynamic matrix
Eigen::VectorXd    // Dynamic vector
Eigen::Matrix3d    // Fixed 3x3
Eigen::Vector3d    // Fixed 3-vector
Eigen::ArrayXd     // Element-wise operations

// Math constants
M_PI, M_E, M_SQRT2, M_LN2
```
