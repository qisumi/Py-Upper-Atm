! msis00_cshim.F90 — C ABI shim for MSIS00 so it can be called from Python (ctypes)
!
! Exposes: void gtd7_eval(int iyd, float sec, float alt, float glat, float glong,
!                         float stl, float f107a, float f107,
!                         const float ap[7], int mass, float d_out[9], float t_out[2])
!
! Types are 32-bit to match the original msis00.F (integer(4), real(4)).
!
module msis00_cshim
  use, intrinsic :: iso_c_binding, only: c_int, c_float
  implicit none
contains
  subroutine gtd7_eval(iyd, sec, alt, glat, glong, stl, f107a, f107, ap, mass, d_out, t_out) bind(C, name="gtd7_eval")
    ! C-callable wrapper with a stable symbol name.
    integer(c_int),  value      :: iyd, mass
    real(c_float),   value      :: sec, alt, glat, glong, stl, f107a, f107
    real(c_float),   intent(in) :: ap(7)
    real(c_float),   intent(out):: d_out(9), t_out(2)

    interface
      subroutine gtd7(iyd, sec, alt, glat, glong, stl, f107a, f107, ap, mass, d, t)
        use, intrinsic :: iso_c_binding, only: c_int, c_float
        implicit none
        integer(c_int),  intent(in)  :: iyd, mass
        real(c_float),   intent(in)  :: sec, alt, glat, glong, stl, f107a, f107
        real(c_float),   intent(in)  :: ap(7)
        real(c_float),   intent(out) :: d(9), t(2)
      end subroutine gtd7
    end interface

    call gtd7(iyd, sec, alt, glat, glong, stl, f107a, f107, ap, mass, d_out, t_out)
  end subroutine gtd7_eval

  subroutine gtd7d_eval(iyd, sec, alt, glat, glong, stl, f107a, f107, ap, mass, d_out, t_out) bind(C, name="gtd7d_eval")
    ! C-callable wrapper for GTD7D (includes anomalous oxygen in total mass density)
    integer(c_int),  value      :: iyd, mass
    real(c_float),   value      :: sec, alt, glat, glong, stl, f107a, f107
    real(c_float),   intent(in) :: ap(7)
    real(c_float),   intent(out):: d_out(9), t_out(2)

    interface
      subroutine gtd7d(iyd, sec, alt, glat, glong, stl, f107a, f107, ap, mass, d, t)
        use, intrinsic :: iso_c_binding, only: c_int, c_float
        implicit none
        integer(c_int),  intent(in)  :: iyd, mass
        real(c_float),   intent(in)  :: sec, alt, glat, glong, stl, f107a, f107
        real(c_float),   intent(in)  :: ap(7)
        real(c_float),   intent(out) :: d(9), t(2)
      end subroutine gtd7d
    end interface

    call gtd7d(iyd, sec, alt, glat, glong, stl, f107a, f107, ap, mass, d_out, t_out)
  end subroutine gtd7d_eval
end module msis00_cshim