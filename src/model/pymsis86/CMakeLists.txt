add_library(
  msis86
  SHARED
    msis86.for
    msis86_cshim.F90
)

upperatmpy_use_gnu_legacy_fortran(msis86.for)
if(CMAKE_Fortran_COMPILER_ID STREQUAL "GNU")
  # MSIS-86 relies on legacy COMMON/ENTRY behavior that is not safe under -O3.
  set_property(SOURCE msis86.for APPEND PROPERTY COMPILE_OPTIONS -O0)
endif()
upperatmpy_set_output(msis86 "${CMAKE_CURRENT_SOURCE_DIR}/build")
upperatmpy_link_static_gnu_runtime(msis86)

install(
  TARGETS msis86
  RUNTIME DESTINATION model/pymsis86/build
  LIBRARY DESTINATION model/pymsis86/build
)
