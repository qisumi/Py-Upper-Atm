add_library(
  hwm93
  SHARED
    hwm93.f
    hwm93_cshim.F90
)

upperatmpy_use_gnu_legacy_fortran(hwm93.f)
upperatmpy_set_output(hwm93 "${CMAKE_CURRENT_SOURCE_DIR}")
upperatmpy_link_static_gnu_runtime(hwm93)

install(
  TARGETS hwm93
  RUNTIME DESTINATION model/pyhwm93
  LIBRARY DESTINATION model/pyhwm93
)
