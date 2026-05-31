! msis86_cshim.F90 — C ABI shim for MSIS-86 so it can be called from Python (ctypes)
!
! Exposes:
!   void msis86_set_data_root(const char *path, int path_len)
!   void gts5_eval(int iyd, float sec, float alt, float glat, float glong,
!                  float stl, float f107a, float f107,
!                  const float ap[7], int mass, float d_out[8], float t_out[2])
!
! Types are 32-bit to match the original msis86.for (default INTEGER, REAL).
!
module msis86_cshim
  use, intrinsic :: iso_c_binding, only: c_int, c_float, c_char
  implicit none
contains

  subroutine msis86_set_data_root(path, path_len) bind(C, name="msis86_set_data_root")
    ! C-callable wrapper to set the data root directory for MSIS86.DAT lookup.
    character(kind=c_char), intent(in) :: path(*)
    integer(c_int), value              :: path_len

    interface
      subroutine msis86_sdr(p, pl)
        character, intent(in) :: p(*)
        integer, intent(in)   :: pl
      end subroutine msis86_sdr
    end interface

    call msis86_sdr(path, path_len)
  end subroutine msis86_set_data_root

  subroutine gts5_eval(iyd, sec, alt, glat, glong, stl, f107a, f107, ap, mass, d_out, t_out) bind(C, name="gts5_eval")
    ! C-callable wrapper with a stable symbol name.
    integer(c_int),  value      :: iyd, mass
    real(c_float),   value      :: sec, alt, glat, glong, stl, f107a, f107
    real(c_float),   intent(in) :: ap(7)
    real(c_float),   intent(out):: d_out(8), t_out(2)

    interface
      subroutine gts5(iyd, sec, alt, glat, glong, stl, f107a, f107, ap, mass, d, t)
        use, intrinsic :: iso_c_binding, only: c_int, c_float
        implicit none
        integer(c_int),  intent(in)  :: iyd, mass
        real(c_float),   intent(in)  :: sec, alt, glat, glong, stl, f107a, f107
        real(c_float),   intent(in)  :: ap(7)
        real(c_float),   intent(out) :: d(8), t(2)
      end subroutine gts5
    end interface

    call gts5(iyd, sec, alt, glat, glong, stl, f107a, f107, ap, mass, d_out, t_out)
  end subroutine gts5_eval

end module msis86_cshim
