add_library(
  sofip
  SHARED
    sofip_legacy.for
    sofip_cshim.F90
)

upperatmpy_set_output(sofip "${CMAKE_CURRENT_SOURCE_DIR}")
upperatmpy_use_gnu_legacy_fortran(sofip_legacy.for)
upperatmpy_link_static_gnu_runtime(sofip)

install(
  TARGETS sofip
  RUNTIME DESTINATION model/pysofip
  LIBRARY DESTINATION model/pysofip
)
