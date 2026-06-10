add_library(
  mgst
  SHARED
    fieldg.for
    mgst_cshim.F90
)

upperatmpy_set_output(mgst "${CMAKE_CURRENT_SOURCE_DIR}")
upperatmpy_use_gnu_legacy_fortran(fieldg.for)
upperatmpy_link_static_gnu_runtime(mgst)

install(
  TARGETS mgst
  RUNTIME DESTINATION model/pymgst
  LIBRARY DESTINATION model/pymgst
)
