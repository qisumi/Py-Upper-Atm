! tsyganenko_t01_cshim.F90 — C ABI shim for T01 magnetic field model
!
!  T01_01 uses IMPLICIT REAL*8 internally, but its formal arguments
!  (PARMOD, PS, X, Y, Z, BX, BY, BZ) are explicitly declared REAL
!  (single precision).  The shim converts c_double <-> REAL.
!
module tsyganenko_t01_cshim
  use, intrinsic :: iso_c_binding, only: c_int, c_double
  implicit none

  real(4) :: gp1(35)
  common /GEOPACK1/ gp1

contains

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
    ps = real(gp1(16), c_double)
  end subroutine

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

  subroutine tsyganenko_eval(iopt, parmod, ps, x, y, z, bx, by, bz) &
      bind(C, name="tsyganenko_eval")
    integer(c_int), value, intent(in) :: iopt
    real(c_double), intent(in) :: parmod(10)
    real(c_double), value, intent(in) :: ps, x, y, z
    real(c_double), intent(out) :: bx, by, bz

    interface
      subroutine T01_01(IOPT, PARMOD, PS, X, Y, Z, BX, BY, BZ)
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

    call T01_01(iopt, pm_s, real(ps), real(x), real(y), real(z), &
                bx_s, by_s, bz_s)
    bx = dble(bx_s)
    by = dble(by_s)
    bz = dble(bz_s)
  end subroutine

end module tsyganenko_t01_cshim
