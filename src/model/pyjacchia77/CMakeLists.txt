add_library(
  jacchia77
  SHARED
    j77sri.for
    jacchia77_cshim.F90
)

upperatmpy_set_output(jacchia77 "${CMAKE_CURRENT_SOURCE_DIR}")
upperatmpy_use_gnu_legacy_fortran(j77sri.for)
upperatmpy_link_static_gnu_runtime(jacchia77)

install(
  TARGETS jacchia77
  RUNTIME DESTINATION model/pyjacchia77
  LIBRARY DESTINATION model/pyjacchia77
)
