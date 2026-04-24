add_library(
  nrlmsis2
  SHARED
    msis_constants.F90
    msis_init.F90
    alt2gph.F90
    msis_gfn.F90
    msis_tfn.F90
    msis_dfn.F90
    msis_calc.F90
    msis_gtd8d.F90
    msis_cshim.F90
)

if(CMAKE_Fortran_COMPILER_ID STREQUAL "GNU")
  target_compile_options(nrlmsis2 PRIVATE -cpp)
endif()

upperatmpy_set_output(nrlmsis2 "${CMAKE_CURRENT_SOURCE_DIR}/build")
upperatmpy_link_static_gnu_runtime(nrlmsis2)

install(
  TARGETS nrlmsis2
  RUNTIME DESTINATION model/pymsis2/build
  LIBRARY DESTINATION model/pymsis2/build
)
