add_library(
  xuli
  SHARED
    xuli.for
    xuli_cshim.F90
)

upperatmpy_set_output(xuli "${CMAKE_CURRENT_SOURCE_DIR}")
upperatmpy_use_gnu_legacy_fortran(xuli.for)
upperatmpy_link_static_gnu_runtime(xuli)

install(
  TARGETS xuli
  RUNTIME DESTINATION model/pyxuli
  LIBRARY DESTINATION model/pyxuli
)
