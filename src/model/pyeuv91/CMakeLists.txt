add_library(euv91 SHARED euv91_cshim.F90)
upperatmpy_set_output(euv91 "${CMAKE_CURRENT_SOURCE_DIR}")
upperatmpy_link_static_gnu_runtime(euv91)
install(TARGETS euv91 RUNTIME DESTINATION model/pyeuv91 LIBRARY DESTINATION model/pyeuv91)
