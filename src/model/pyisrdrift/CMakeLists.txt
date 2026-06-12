add_library(
  isr_drift
  SHARED
    isr_drift.for
    isr_drift_cshim.F90
)

upperatmpy_set_output(isr_drift "${CMAKE_CURRENT_SOURCE_DIR}")
upperatmpy_use_gnu_legacy_fortran(isr_drift.for)
upperatmpy_link_static_gnu_runtime(isr_drift)

install(
  TARGETS isr_drift
  RUNTIME DESTINATION model/pyisrdrift
  LIBRARY DESTINATION model/pyisrdrift
)
