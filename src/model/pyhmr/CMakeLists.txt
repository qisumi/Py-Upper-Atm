add_library(
  hmr
  SHARED
    hm_subr.for
    hmr_cshim.F90
)

upperatmpy_set_output(hmr "${CMAKE_CURRENT_SOURCE_DIR}")
upperatmpy_use_gnu_legacy_fortran(hm_subr.for)
target_compile_options(hmr PRIVATE -fno-align-commons)
upperatmpy_link_static_gnu_runtime(hmr)

install(
  TARGETS hmr
  RUNTIME DESTINATION model/pyhmr
  LIBRARY DESTINATION model/pyhmr
)
