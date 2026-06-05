cmake_minimum_required(VERSION 3.24)
project(veil_backend LANGUAGES CXX)

# --------------------------------------------------------------------------
# Options
# --------------------------------------------------------------------------
option(VEIL_USE_SYSTEM_OPENFHE "Link a preinstalled OpenFHE via find_package (fast local iteration)" OFF)
option(VEIL_WITH_HEXL          "Enable Intel HEXL (AVX-512) acceleration in OpenFHE" OFF)
option(VEIL_BUILD_CXX_TESTS    "Build the C++ (GoogleTest) unit suite" OFF)

# Pin OpenFHE to a released tag. Never track main. Bump deliberately via a PR
# that re-runs the benchmark suite (parameter behavior can shift across releases).
set(VEIL_OPENFHE_TAG "v1.5.1" CACHE STRING "OpenFHE git tag to fetch when not using the system install")

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

if(NOT CMAKE_BUILD_TYPE AND NOT CMAKE_CONFIGURATION_TYPES)
    set(CMAKE_BUILD_TYPE Release CACHE STRING "" FORCE)
endif()

set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# --------------------------------------------------------------------------
# Dependencies
# --------------------------------------------------------------------------
include(${CMAKE_CURRENT_SOURCE_DIR}/cmake/FindOrFetchOpenFHE.cmake)

# pybind11 is provided by scikit-build-core's build environment; fall back to
# find_package for standalone CMake builds.
find_package(pybind11 CONFIG)
if(NOT pybind11_FOUND)
    message(STATUS "[veil] pybind11 not found via find_package, fetching via FetchContent")
    include(FetchContent)
    FetchContent_Declare(
        pybind11
        GIT_REPOSITORY https://github.com/pybind/pybind11.git
        GIT_TAG v3.0.4
    )
    FetchContent_MakeAvailable(pybind11)
endif()

# --------------------------------------------------------------------------
# The extension module
# --------------------------------------------------------------------------
pybind11_add_module(veil_backend src/backend.cpp)

target_link_libraries(veil_backend PRIVATE ${VEIL_OPENFHE_LIBRARIES})
target_include_directories(veil_backend PRIVATE ${VEIL_OPENFHE_INCLUDE_DIRS})
target_compile_features(veil_backend PRIVATE cxx_std_17)

if(APPLE)
    if(EXISTS "/opt/homebrew/opt/libomp/lib")
        target_link_directories(veil_backend PRIVATE "/opt/homebrew/opt/libomp/lib")
    elseif(EXISTS "/usr/local/opt/libomp/lib")
        target_link_directories(veil_backend PRIVATE "/usr/local/opt/libomp/lib")
    endif()
endif()

# scikit-build-core installs the module into the veil package directory.
install(TARGETS veil_backend LIBRARY DESTINATION veil RUNTIME DESTINATION veil)

# --------------------------------------------------------------------------
# Optional C++ unit tests
# --------------------------------------------------------------------------
if(VEIL_BUILD_CXX_TESTS)
    enable_testing()
    include(FetchContent)
    FetchContent_Declare(
        googletest
        GIT_REPOSITORY https://github.com/google/googletest.git
        GIT_TAG v1.15.2
    )
    set(gtest_force_shared_crt ON CACHE BOOL "" FORCE)
    FetchContent_MakeAvailable(googletest)
    # add_executable(veil_cxx_tests tests/cxx/...) ; target_link_libraries(... gtest_main ...)
    # add_test(NAME veil_cxx_tests COMMAND veil_cxx_tests)
endif()
