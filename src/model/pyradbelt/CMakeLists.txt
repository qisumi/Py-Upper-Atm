add_library(
  radbelt
  SHARED
    trmfun.for
    radbelt_cshim.F90
)

upperatmpy_set_output(radbelt "${CMAKE_CURRENT_SOURCE_DIR}")
upperatmpy_use_gnu_legacy_fortran(trmfun.for)
upperatmpy_link_static_gnu_runtime(radbelt)

install(
  TARGETS radbelt
  RUNTIME DESTINATION model/pyradbelt
  LIBRARY DESTINATION model/pyradbelt
)
