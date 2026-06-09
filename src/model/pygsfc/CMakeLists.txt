add_library(
  gsfc
  SHARED
    gsfcsub.for
    gsfc_cshim.F90
)

upperatmpy_set_output(gsfc "${CMAKE_CURRENT_SOURCE_DIR}")
upperatmpy_use_gnu_legacy_fortran(gsfcsub.for)
target_compile_options(gsfc PRIVATE -fno-align-commons)
upperatmpy_link_static_gnu_runtime(gsfc)

install(
  TARGETS gsfc
  RUNTIME DESTINATION model/pygsfc
  LIBRARY DESTINATION model/pygsfc
)
