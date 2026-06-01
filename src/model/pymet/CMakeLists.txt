add_library(
  met
  SHARED
    met.for
    met_cshim.F90
)

upperatmpy_set_output(met "${CMAKE_CURRENT_SOURCE_DIR}")
upperatmpy_use_gnu_legacy_fortran(met.for)
upperatmpy_link_static_gnu_runtime(met)

install(
  TARGETS met
  RUNTIME DESTINATION model/pymet
  LIBRARY DESTINATION model/pymet
)
