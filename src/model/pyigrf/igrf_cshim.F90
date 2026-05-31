! igrf_cshim.F90 — C ABI shim for IGRF geomagnetic field model
!
!  Exposes:
!    void igrf_set_data_root(const char *path)
!    void igrf_set_version(int ver)
!    void igrf_eval(float xlat, float xlong, float year, float height,
!                   float *bnorth, float *beast, float *bdown, float *babs,
!                   float *xl, int *icode)
!
!  Wraps the IGRF + SHELLG subroutines for use via ctypes / C callers.
!  All field values are in Gauss (Python wrapper converts to nT).
!  Derived quantities (H, D, I) are computed in Python.
!
module igrf_cshim
  use, intrinsic :: iso_c_binding, only: c_int, c_float, c_char, c_null_char
  use upperatmpy_igrf_data, only: data_root, igrf_version
  implicit none
contains

  ! ------------------------------------------------------------------
  ! Set the directory containing IGRF coefficient .dat files.
  ! Called once during Model.__init__.
  ! ------------------------------------------------------------------
  subroutine igrf_set_data_root(path) bind(C, name="igrf_set_data_root")
    character(kind=c_char), intent(in) :: path(*)
    integer :: i

    data_root = ''
    do i = 1, len(data_root)
      if (path(i) == c_null_char) exit
      data_root(i:i) = achar(iachar(path(i)))
    enddo
  end subroutine

  ! ------------------------------------------------------------------
  ! Set IGRF generation (13 or 14).  Called once during Model.__init__.
  ! ------------------------------------------------------------------
  subroutine igrf_set_version(ver) bind(C, name="igrf_set_version")
    integer(c_int), value, intent(in) :: ver
    igrf_version = ver
  end subroutine

  ! ------------------------------------------------------------------
  ! Compute geomagnetic field components and L-value at one point.
  !
  ! Inputs (all pass-by-value):
  !   xlat   — geodetic latitude in degrees (north positive)
  !   xlong  — geodetic longitude in degrees (east positive)
  !   year   — decimal year (e.g. 2024.5)
  !   height — altitude in km above sea level
  !
  ! Outputs (all pass-by-reference):
  !   bnorth — north component of B (Gauss)
  !   beast  — east  component of B (Gauss)
  !   bdown  — down  component of B (Gauss, positive downward)
  !   babs   — total field strength |B| (Gauss)
  !   xl     — L-shell parameter (from SHELLG)
  !   icode  — L-value status: 1=ok, 2=unphysical, 3=approximation
  ! ------------------------------------------------------------------
  subroutine igrf_eval(xlat, xlong, year, height, &
                        bnorth, beast, bdown, babs, &
                        xl, icode) bind(C, name="igrf_eval")
    real(c_float),    value, intent(in)  :: xlat, xlong, year, height
    real(c_float),           intent(out) :: bnorth, beast, bdown, babs
    real(c_float),           intent(out) :: xl
    integer(c_int),          intent(out) :: icode

    real :: dimo, bab1

    ! Declare original Fortran subroutines via interface blocks
    interface
      subroutine INITIZE
      end subroutine INITIZE
      subroutine FELDCOF(YEAR, DIMO)
        real, intent(in)  :: YEAR
        real, intent(out) :: DIMO
      end subroutine FELDCOF
      subroutine FELDG(GLAT, GLON, ALT, BNORTH, BEAST, BDOWN, BABS)
        real, intent(in)  :: GLAT, GLON, ALT
        real, intent(out) :: BNORTH, BEAST, BDOWN, BABS
      end subroutine FELDG
      subroutine SHELLG(GLAT, GLON, ALT, DIMO, FL, ICODE, B0)
        real, intent(in)  :: GLAT, GLON, ALT, DIMO
        real, intent(out) :: FL, B0
        integer, intent(out) :: ICODE
      end subroutine SHELLG
    end interface

    call INITIZE()
    call FELDCOF(year, dimo)
    call FELDG(xlat, xlong, height, bnorth, beast, bdown, babs)
    call SHELLG(xlat, xlong, height, dimo, xl, icode, bab1)
  end subroutine

end module igrf_cshim
