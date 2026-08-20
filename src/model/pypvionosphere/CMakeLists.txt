add_library(pvionosphere SHARED pvionosphere_cshim.F90)
upperatmpy_set_output(pvionosphere "${CMAKE_CURRENT_SOURCE_DIR}")
upperatmpy_link_static_gnu_runtime(pvionosphere)
install(TARGETS pvionosphere RUNTIME DESTINATION model/pypvionosphere LIBRARY DESTINATION model/pypvionosphere)
