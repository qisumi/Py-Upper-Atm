add_library(
  msis86
  SHARED
    msis86.for
    msis86_cshim.F90
)

upperatmpy_use_gnu_legacy_fortran(msis86.for)
if(CMAKE_Fortran_COMPILER_ID STREQUAL "GNU")
  # MSIS-86 relies on legacy static local storage and COMMON/ENTRY behavior.
  target_compile_options(msis86 PRIVATE -O0 -fno-automatic)
endif()
upperatmpy_set_output(msis86 "${CMAKE_CURRENT_SOURCE_DIR}/build")
upperatmpy_link_static_gnu_runtime(msis86)

install(
  TARGETS msis86
  RUNTIME DESTINATION model/pymsis86/build
  LIBRARY DESTINATION model/pymsis86/build
)
