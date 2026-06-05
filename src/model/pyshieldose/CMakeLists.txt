add_library(
  shieldose
  SHARED
    shieldose_cshim.F90
)

upperatmpy_set_output(shieldose "${CMAKE_CURRENT_SOURCE_DIR}")
upperatmpy_link_static_gnu_runtime(shieldose)

install(
  TARGETS shieldose
  RUNTIME DESTINATION model/pyshieldose
  LIBRARY DESTINATION model/pyshieldose
)
