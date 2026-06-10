add_library(
  jensen
  SHARED
    fieldg.for
    jensen_cshim.F90
)

upperatmpy_set_output(jensen "${CMAKE_CURRENT_SOURCE_DIR}")
upperatmpy_use_gnu_legacy_fortran(fieldg.for)
upperatmpy_link_static_gnu_runtime(jensen)

install(
  TARGETS jensen
  RUNTIME DESTINATION model/pyjensen
  LIBRARY DESTINATION model/pyjensen
)
