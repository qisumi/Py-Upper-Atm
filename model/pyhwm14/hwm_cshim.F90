
! cshim.F90 — C ABI shim for HWM14 so it can be called from Python (ctypes)
!
! Exposes: void hwm14_eval(int iyd, float sec, float alt, float glat, float glon,
!                          float stl, float f107a, float f107,
!                          const float ap[2], float w_out[2])
!
! Types are 32‑bit to match the original hwm14.f90 (integer(4), real(4)).
!
module hwm14_cshim
  use, intrinsic :: iso_c_binding, only: c_int, c_float
  implicit none
contains
  subroutine hwm14_eval(iyd,sec,alt,glat,glon,stl,f107a,f107,ap,w_out) bind(C, name="hwm14_eval")
    ! C‑callable wrapper with a stable symbol name.
    integer(c_int),  value      :: iyd
    real(c_float),   value      :: sec,alt,glat,glon,stl,f107a,f107
    real(c_float),   intent(in) :: ap(2)
    real(c_float),   intent(out):: w_out(2)

    interface
      subroutine hwm14(iyd,sec,alt,glat,glon,stl,f107a,f107,ap,w)
        use, intrinsic :: iso_c_binding, only: c_int, c_float
        implicit none
        integer(c_int),  intent(in)  :: iyd
        real(c_float),   intent(in)  :: sec,alt,glat,glon,stl,f107a,f107
        real(c_float),   intent(in)  :: ap(2)
        real(c_float),   intent(out) :: w(2)
      end subroutine hwm14
    end interface

    call hwm14(iyd,sec,alt,glat,glon,stl,f107a,f107,ap,w_out)
  end subroutine hwm14_eval
end module hwm14_cshim
