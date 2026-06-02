# Tsyganenko magnetic field models (T89, T96, T01, TS04)
# Each model is compiled into a separate shared library because T96/T01/TS04
# share identically-named internal subroutines that would collide in a single DLL.
# All four DLLs include a copy of Geopack_2005.for for COMMON block support.

set(GEOPACK_SRC geopack_2005.for)

# --- T89 ---
add_library(tsyganenko_t89 SHARED
    ${GEOPACK_SRC}
    t89.for
    tsyganenko_t89_cshim.F90
)
upperatmpy_set_output(tsyganenko_t89 "${CMAKE_CURRENT_SOURCE_DIR}")
upperatmpy_use_gnu_legacy_fortran(${GEOPACK_SRC} t89.for)
target_compile_options(tsyganenko_t89 PRIVATE -fno-align-commons)
upperatmpy_link_static_gnu_runtime(tsyganenko_t89)
install(TARGETS tsyganenko_t89
    RUNTIME DESTINATION model/pytsyganenko
    LIBRARY DESTINATION model/pytsyganenko
)

# --- T96 ---
add_library(tsyganenko_t96 SHARED
    ${GEOPACK_SRC}
    t96.for
    tsyganenko_t96_cshim.F90
)
upperatmpy_set_output(tsyganenko_t96 "${CMAKE_CURRENT_SOURCE_DIR}")
upperatmpy_use_gnu_legacy_fortran(${GEOPACK_SRC} t96.for)
target_compile_options(tsyganenko_t96 PRIVATE -fno-align-commons)
upperatmpy_link_static_gnu_runtime(tsyganenko_t96)
install(TARGETS tsyganenko_t96
    RUNTIME DESTINATION model/pytsyganenko
    LIBRARY DESTINATION model/pytsyganenko
)

# --- T01 ---
add_library(tsyganenko_t01 SHARED
    ${GEOPACK_SRC}
    t01.for
    tsyganenko_t01_cshim.F90
)
upperatmpy_set_output(tsyganenko_t01 "${CMAKE_CURRENT_SOURCE_DIR}")
upperatmpy_use_gnu_legacy_fortran(${GEOPACK_SRC} t01.for)
target_compile_options(tsyganenko_t01 PRIVATE -fno-align-commons)
upperatmpy_link_static_gnu_runtime(tsyganenko_t01)
install(TARGETS tsyganenko_t01
    RUNTIME DESTINATION model/pytsyganenko
    LIBRARY DESTINATION model/pytsyganenko
)

# --- TS04 ---
add_library(tsyganenko_ts04 SHARED
    ${GEOPACK_SRC}
    ts04.for
    tsyganenko_ts04_cshim.F90
)
upperatmpy_set_output(tsyganenko_ts04 "${CMAKE_CURRENT_SOURCE_DIR}")
upperatmpy_use_gnu_legacy_fortran(${GEOPACK_SRC} ts04.for)
target_compile_options(tsyganenko_ts04 PRIVATE -fno-align-commons)
upperatmpy_link_static_gnu_runtime(tsyganenko_ts04)
install(TARGETS tsyganenko_ts04
    RUNTIME DESTINATION model/pytsyganenko
    LIBRARY DESTINATION model/pytsyganenko
)
