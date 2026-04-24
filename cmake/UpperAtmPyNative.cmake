function(upperatmpy_set_output target output_dir)
  set_target_properties(
    ${target}
    PROPERTIES
      RUNTIME_OUTPUT_DIRECTORY "${output_dir}"
      LIBRARY_OUTPUT_DIRECTORY "${output_dir}"
      ARCHIVE_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/lib"
      Fortran_MODULE_DIRECTORY "${CMAKE_BINARY_DIR}/modules/${target}"
  )
  if(WIN32)
    set_target_properties(${target} PROPERTIES PREFIX "")
  endif()
endfunction()

function(upperatmpy_link_static_gnu_runtime target)
  if(CMAKE_Fortran_COMPILER_ID STREQUAL "GNU")
    target_link_options(
      ${target}
      PRIVATE
        -static-libgcc
        -static-libgfortran
        -static-libquadmath
    )
  endif()
endfunction()
