! msise90_cshim.F90 — C ABI shim for MSISE-90 so it can be called from Python (ctypes)
!
! Exposes:
!   void gtd6_eval(int iyd, float sec, float alt, float glat, float glong,
!                  float stl, float f107a, float f107,
!                  const float ap[7], int mass, float d_out[8], float t_out[2])
!
! Types are 32-bit to match the original msise90.for (default INTEGER, REAL).
!
module msise90_cshim
  use, intrinsic :: iso_c_binding, only: c_int, c_float
  implicit none
contains

  subroutine gtd6_eval(iyd, sec, alt, glat, glong, stl, f107a, f107, ap, mass, d_out, t_out) bind(C, name="gtd6_eval")
    ! C-callable wrapper with a stable symbol name.
    integer(c_int),  value      :: iyd, mass
    real(c_float),   value      :: sec, alt, glat, glong, stl, f107a, f107
    real(c_float),   intent(in) :: ap(7)
    real(c_float),   intent(out):: d_out(8), t_out(2)

    interface
      subroutine gtd6(iyd, sec, alt, glat, glong, stl, f107a, f107, ap, mass, d, t)
        use, intrinsic :: iso_c_binding, only: c_int, c_float
        implicit none
        integer(c_int),  intent(in)  :: iyd, mass
        real(c_float),   intent(in)  :: sec, alt, glat, glong, stl, f107a, f107
        real(c_float),   intent(in)  :: ap(7)
        real(c_float),   intent(out) :: d(8), t(2)
      end subroutine gtd6
    end interface

    call gtd6(iyd, sec, alt, glat, glong, stl, f107a, f107, ap, mass, d_out, t_out)
  end subroutine gtd6_eval

end module msise90_cshim
