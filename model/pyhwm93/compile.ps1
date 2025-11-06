gfortran -O3 -c hwm93.f
gfortran -O3 -c hwm93_cshim.F90

gfortran -shared -o hwm93.dll hwm93.o hwm93_cshim.o "-Wl,--out-implib,hwm93.a" -static-libgcc -static-libgfortran -static-libquadmath

rm *.mod
rm *.o