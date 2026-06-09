! gsfc_cshim.F90 — C ABI shim for GSFC geomagnetic field model
!
!  Exposes:
!    void gsfc_set_data_root(const char *path)
!    void gsfc_eval(int model, float lat, float lon, float alt, float year,
!                   int jj, float *x, float *y, float *z, float *f)
!
!  Wraps the FIDD subroutine for use via ctypes / C callers.
!  Field components are in nT (same as the original Fortran code).
!
module gsfc_cshim
  use, intrinsic :: iso_c_binding, only: c_int, c_float, c_char, c_null_char
  implicit none

  character(len=256) :: gsfc_data_root = ''

contains

  ! ------------------------------------------------------------------
  ! Set the directory containing GSFC coefficient .dat files.
  ! Called once during Model.__init__.
  ! ------------------------------------------------------------------
  subroutine gsfc_set_data_root(path) bind(C, name="gsfc_set_data_root")
    character(kind=c_char), intent(in) :: path(*)
    integer :: i

    gsfc_data_root = ''
    do i = 1, len(gsfc_data_root)
      if (path(i) == c_null_char) exit
      gsfc_data_root(i:i) = achar(iachar(path(i)))
    enddo
  end subroutine

  ! ------------------------------------------------------------------
  ! Copy module data_root into the Fortran COMMON block before calling FIDD.
  ! ------------------------------------------------------------------
  subroutine gsfc_apply_data_root()
    common /gsfc_path/ data_root
    character*256 data_root
    data_root = gsfc_data_root
  end subroutine

  ! ------------------------------------------------------------------
  ! Compute geomagnetic field components at one point.
  !
  ! Inputs (all pass-by-value):
  !   model — 0=GSFC80, 1=GSFC83, 2=GSFC87
  !   lat   — geodetic latitude in degrees (north positive)
  !   lon   — geodetic longitude in degrees (east positive)
  !   alt   — altitude in km above sea level (geodetic) or
  !           geocentric radius in km (if geocentric)
  !   year  — decimal year (e.g. 1985.5)
  !   jj    — 0=geodetic, 1=geocentric
  !
  ! Outputs (all pass-by-reference):
  !   x — north component of B (nT)
  !   y — east  component of B (nT)
  !   z — down  component of B (nT, positive downward)
  !   f — total field strength |B| (nT)
  ! ------------------------------------------------------------------
  subroutine gsfc_eval(model, lat, lon, alt, year, jj, &
                       x, y, z, f) bind(C, name="gsfc_eval")
    integer(c_int),  value, intent(in)  :: model, jj
    real(c_float),   value, intent(in)  :: lat, lon, alt, year
    real(c_float),          intent(out) :: x, y, z, f

    real(c_float) :: x_out, y_out, z_out, f_out
    integer :: jj_out

    interface
      subroutine FIDD(MODEL, JJ, DLAT, DLONG, ALT1, TM, X, Y, Z, F)
        integer, intent(in) :: MODEL, JJ
        real, intent(in)    :: DLAT, DLONG, ALT1
        double precision, intent(in) :: TM
        real, intent(out)   :: X, Y, Z, F
      end subroutine FIDD
    end interface

    call gsfc_apply_data_root()

    jj_out = jj
    call FIDD(model, jj_out, lat, lon, alt, dble(year), &
              x_out, y_out, z_out, f_out)

    x = x_out
    y = y_out
    z = z_out
    f = f_out
  end subroutine

end module gsfc_cshim
