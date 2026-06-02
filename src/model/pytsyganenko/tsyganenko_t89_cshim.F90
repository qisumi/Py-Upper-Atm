! tsyganenko_t89_cshim.F90 — C ABI shim for T89 magnetic field model
!
!  Exposes:
!    void tsyganenko_recalc(int iyear, int iday, int ihour, int imin, int isec,
!                           double *ps)
!    void tsyganenko_eval_dip(double x, double y, double z,
!                             double *bx, double *by, double *bz)
!    void tsyganenko_eval(int iopt, const double *parmod,
!                         double ps, double x, double y, double z,
!                         double *bx, double *by, double *bz)
!
!  T89C uses single-precision (REAL) arguments internally; the shim converts.
!
module tsyganenko_t89_cshim
  use, intrinsic :: iso_c_binding, only: c_int, c_double
  implicit none

  ! Access COMMON /GEOPACK1/ to read SPS/CPS/PSI after RECALC.
  ! Layout (35 single-precision reals):
  !   1-8:   ST0,CT0,SL0,CL0,CTCL,STCL,CTSL,STSL
  !   9-10:  SFI,CFI
  !   11:    SPS  (sin of dipole tilt)
  !   12:    CPS  (cos of dipole tilt)
  !   13-15: SHI,CHI,HI
  !   16:    PSI  (dipole tilt angle in radians)
  !   17-35: XMUT,A11..A33,DS3,CGST,SGST,BA(6)
  real(4) :: gp1(35)
  common /GEOPACK1/ gp1

contains

  ! ------------------------------------------------------------------
  ! Call RECALC to populate COMMON blocks, then return dipole tilt angle.
  ! ------------------------------------------------------------------
  subroutine tsyganenko_recalc(iyear, iday, ihour, imin, isec, ps) &
      bind(C, name="tsyganenko_recalc")
    integer(c_int), value, intent(in) :: iyear, iday, ihour, imin, isec
    real(c_double), intent(out) :: ps

    interface
      subroutine RECALC(IYEAR, IDAY, IHOUR, MIN, ISEC)
        integer, intent(in) :: IYEAR, IDAY, IHOUR, MIN, ISEC
      end subroutine
    end interface

    call RECALC(iyear, iday, ihour, imin, isec)
    ! PSI is element 16 in COMMON /GEOPACK1/
    ps = real(gp1(16), c_double)
  end subroutine

  ! ------------------------------------------------------------------
  ! Internal dipole field (calls DIP from Geopack).
  ! Requires RECALC to have been called first.
  ! ------------------------------------------------------------------
  subroutine tsyganenko_eval_dip(x, y, z, bx, by, bz) &
      bind(C, name="tsyganenko_eval_dip")
    real(c_double), value, intent(in) :: x, y, z
    real(c_double), intent(out) :: bx, by, bz

    interface
      subroutine DIP(XGSM, YGSM, ZGSM, BXGSM, BYGSM, BZGSM)
        real, intent(in) :: XGSM, YGSM, ZGSM
        real, intent(out) :: BXGSM, BYGSM, BZGSM
      end subroutine
    end interface

    real :: bx_s, by_s, bz_s
    call DIP(real(x), real(y), real(z), bx_s, by_s, bz_s)
    bx = dble(bx_s)
    by = dble(by_s)
    bz = dble(bz_s)
  end subroutine

  ! ------------------------------------------------------------------
  ! T89C external field evaluation.
  ! T89C arguments are single-precision; convert from/to c_double.
  ! ------------------------------------------------------------------
  subroutine tsyganenko_eval(iopt, parmod, ps, x, y, z, bx, by, bz) &
      bind(C, name="tsyganenko_eval")
    integer(c_int), value, intent(in) :: iopt
    real(c_double), intent(in) :: parmod(10)
    real(c_double), value, intent(in) :: ps, x, y, z
    real(c_double), intent(out) :: bx, by, bz

    interface
      subroutine T89C(IOPT, PARMOD, PS, X, Y, Z, BX, BY, BZ)
        integer, intent(in) :: IOPT
        real, intent(in) :: PARMOD(10), PS, X, Y, Z
        real, intent(out) :: BX, BY, BZ
      end subroutine
    end interface

    real :: pm_s(10), bx_s, by_s, bz_s
    integer :: i
    do i = 1, 10
      pm_s(i) = real(parmod(i))
    end do

    call T89C(iopt, pm_s, real(ps), real(x), real(y), real(z), &
              bx_s, by_s, bz_s)
    bx = dble(bx_s)
    by = dble(by_s)
    bz = dble(bz_s)
  end subroutine

end module tsyganenko_t89_cshim
