add_library(
  hwm14
  SHARED
    hwm14.f90
    hwm_cshim.F90
)

upperatmpy_set_output(hwm14 "${CMAKE_CURRENT_SOURCE_DIR}")
upperatmpy_link_static_gnu_runtime(hwm14)

install(
  TARGETS hwm14
  RUNTIME DESTINATION model/pyhwm14
  LIBRARY DESTINATION model/pyhwm14
)
