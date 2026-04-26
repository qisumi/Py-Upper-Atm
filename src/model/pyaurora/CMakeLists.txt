add_library(
  aurora_oval
  SHARED
    oval.for
    oval_cshim.F90
)

upperatmpy_set_output(aurora_oval "${CMAKE_CURRENT_SOURCE_DIR}")
upperatmpy_use_gnu_legacy_fortran(oval.for)
upperatmpy_link_static_gnu_runtime(aurora_oval)

install(
  TARGETS aurora_oval
  RUNTIME DESTINATION model/pyaurora
  LIBRARY DESTINATION model/pyaurora
)
