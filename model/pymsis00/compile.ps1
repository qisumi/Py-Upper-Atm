gfortran -O3 -c -std=legacy -fno-range-check msis00.F;gfortran -O3 -c msis00_cshim.F90

gfortran -shared -o msis00.dll msis00.o msis00_cshim.o "-Wl,--out-implib,msis00.a" -static-libgcc -static-libgfortran -static-libquadmath

rm *.mod;rm *.o