add_library(
  chiu
  SHARED
    chiu.for
    chiu_cshim.F90
)

upperatmpy_set_output(chiu "${CMAKE_CURRENT_SOURCE_DIR}")
upperatmpy_use_gnu_legacy_fortran(chiu.for)
upperatmpy_link_static_gnu_runtime(chiu)

install(
  TARGETS chiu
  RUNTIME DESTINATION model/pychiu
  LIBRARY DESTINATION model/pychiu
)
