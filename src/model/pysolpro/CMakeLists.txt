add_library(
  solpro
  SHARED
    solpro.for
    solpro_cshim.F90
)

upperatmpy_set_output(solpro "${CMAKE_CURRENT_SOURCE_DIR}")
upperatmpy_use_gnu_legacy_fortran(solpro.for)
upperatmpy_link_static_gnu_runtime(solpro)

install(
  TARGETS solpro
  RUNTIME DESTINATION model/pysolpro
  LIBRARY DESTINATION model/pysolpro
)
