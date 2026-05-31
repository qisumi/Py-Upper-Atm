add_library(
  msise90
  SHARED
    msise90.for
    msise90_cshim.F90
)

upperatmpy_use_gnu_legacy_fortran(msise90.for)
if(CMAKE_Fortran_COMPILER_ID STREQUAL "GNU")
  # MSISE-90 relies on legacy COMMON/ENTRY behavior that is not safe under -O3.
  set_property(SOURCE msise90.for APPEND PROPERTY COMPILE_OPTIONS -O0)
endif()
upperatmpy_set_output(msise90 "${CMAKE_CURRENT_SOURCE_DIR}/build")
upperatmpy_link_static_gnu_runtime(msise90)

install(
  TARGETS msise90
  RUNTIME DESTINATION model/pymsise90/build
  LIBRARY DESTINATION model/pymsise90/build
)
