add_library(
  igrf
  SHARED
    igrf.for
    igrf_cshim.F90
)

upperatmpy_set_output(igrf "${CMAKE_CURRENT_SOURCE_DIR}")
upperatmpy_use_gnu_legacy_fortran(igrf.for)
target_compile_options(igrf PRIVATE -fno-align-commons)
upperatmpy_link_static_gnu_runtime(igrf)

install(
  TARGETS igrf
  RUNTIME DESTINATION model/pyigrf
  LIBRARY DESTINATION model/pyigrf
)
