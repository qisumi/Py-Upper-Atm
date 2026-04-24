add_library(
  msis00
  SHARED
    msis00.f
    msis00_cshim.F90
)

upperatmpy_use_gnu_legacy_fortran(msis00.f)
upperatmpy_set_output(msis00 "${CMAKE_CURRENT_SOURCE_DIR}/build")
upperatmpy_link_static_gnu_runtime(msis00)

install(
  TARGETS msis00
  RUNTIME DESTINATION model/pymsis00/build
  LIBRARY DESTINATION model/pymsis00/build
)
