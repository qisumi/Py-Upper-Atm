add_library(
  cutoff
  SHARED
    cutoff_legacy.for
    cutoff_cshim.F90
)

upperatmpy_set_output(cutoff "${CMAKE_CURRENT_SOURCE_DIR}")
upperatmpy_use_gnu_legacy_fortran(cutoff_legacy.for)
target_compile_options(cutoff PRIVATE -fno-align-commons)
upperatmpy_link_static_gnu_runtime(cutoff)

install(
  TARGETS cutoff
  RUNTIME DESTINATION model/pycutoff
  LIBRARY DESTINATION model/pycutoff
)
