# FindOrFetchOpenFHE.cmake
#
# Acquires OpenFHE either from a system installation (fast local iteration) or by
# building it from source via FetchContent at a pinned tag (hermetic, what CI
# does by default). Exports:
#   VEIL_OPENFHE_LIBRARIES     - targets/libs to link
#   VEIL_OPENFHE_INCLUDE_DIRS  - include directories
#
# Decisions: see DESIGN.md §4.5 and §11.

include_guard(GLOBAL)

if(VEIL_USE_SYSTEM_OPENFHE)
    # ----------------------------------------------------------------------
    # Path A: link a preinstalled OpenFHE (built with `make install`).
    # ----------------------------------------------------------------------
    message(STATUS "[veil] Using system OpenFHE via find_package")
    find_package(OpenFHE REQUIRED)

    # OpenFHE's package config exposes OpenFHE_INCLUDE / OpenFHE_LIBRARIES and
    # per-component include dirs. Aggregate what we need.
    set(VEIL_OPENFHE_INCLUDE_DIRS
        ${OPENFHE_INCLUDE}
        ${OPENFHE_INCLUDE}/core
        ${OPENFHE_INCLUDE}/pke
        ${OPENFHE_INCLUDE}/binfhe
    )
    set(VEIL_OPENFHE_LIBRARIES ${OpenFHE_SHARED_LIBRARIES})
    if(NOT VEIL_OPENFHE_LIBRARIES)
        set(VEIL_OPENFHE_LIBRARIES OPENFHEcore OPENFHEpke OPENFHEbinfhe)
    endif()
else()
    # ----------------------------------------------------------------------
    # Path B: build OpenFHE from source at a pinned tag (hermetic).
    # NOTE: this is the long pole of the build. CI caches it per tag/platform.
    # ----------------------------------------------------------------------
    message(STATUS "[veil] Fetching OpenFHE ${VEIL_OPENFHE_TAG} via FetchContent (this is slow on a cold cache)")
    include(FetchContent)

    set(BUILD_UNITTESTS    OFF CACHE BOOL "" FORCE)
    set(BUILD_EXAMPLES     OFF CACHE BOOL "" FORCE)
    set(BUILD_BENCHMARKS   OFF CACHE BOOL "" FORCE)
    set(BUILD_SHARED       ON  CACHE BOOL "" FORCE)
    if(VEIL_WITH_HEXL)
        set(WITH_INTEL_HEXL ON CACHE BOOL "" FORCE)
    endif()

    FetchContent_Declare(
        OpenFHE
        GIT_REPOSITORY https://github.com/openfheorg/openfhe-development.git
        GIT_TAG        ${VEIL_OPENFHE_TAG}
        GIT_SHALLOW    TRUE
    )
    FetchContent_GetProperties(OpenFHE)
    if(NOT openfhe_POPULATED)
        FetchContent_Populate(OpenFHE)
        add_subdirectory(${openfhe_SOURCE_DIR} ${openfhe_BINARY_DIR} EXCLUDE_FROM_ALL)
    endif()

    set(VEIL_OPENFHE_INCLUDE_DIRS
        ${openfhe_SOURCE_DIR}/src/core/include
        ${openfhe_SOURCE_DIR}/src/pke/include
        ${openfhe_SOURCE_DIR}/src/binfhe/include
        ${openfhe_BINARY_DIR}/src/core/config
    )
    set(VEIL_OPENFHE_LIBRARIES OPENFHEcore OPENFHEpke OPENFHEbinfhe)
endif()

message(STATUS "[veil] OpenFHE libraries: ${VEIL_OPENFHE_LIBRARIES}")
