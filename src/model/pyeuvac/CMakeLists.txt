add_library(euvac SHARED euvac_cshim.F90)
upperatmpy_set_output(euvac "${CMAKE_CURRENT_SOURCE_DIR}")
upperatmpy_link_static_gnu_runtime(euvac)
install(TARGETS euvac RUNTIME DESTINATION model/pyeuvac LIBRARY DESTINATION model/pyeuvac)
