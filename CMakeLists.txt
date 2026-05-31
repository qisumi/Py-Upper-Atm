cmake_minimum_required(VERSION 3.20)

project(UpperAtmPyNative LANGUAGES Fortran)

set(CMAKE_POSITION_INDEPENDENT_CODE ON)

include(cmake/UpperAtmPyNative.cmake)

add_subdirectory(src/model/pymsis2)
add_subdirectory(src/model/pymsis00)
add_subdirectory(src/model/pyhwm14)
add_subdirectory(src/model/pyhwm93)
add_subdirectory(src/model/pyaurora)
add_subdirectory(src/model/pyigrf)
add_subdirectory(src/model/pymsis86)
add_subdirectory(src/model/pymsise90)
