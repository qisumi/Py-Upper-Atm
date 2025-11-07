gfortran -O3 -c hwm14.f90;gfortran -O3 -c hwm_cshim.F90

gfortran -shared -o hwm14.dll hwm14.o hwm_cshim.o "-Wl,--out-implib,hwm14.a" -static-libgcc -static-libgfortran -static-libquadmath

rm *.mod;rm *.o