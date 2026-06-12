! xuli_cshim.F90 — C ABI shim for Xu-Li Neutral Sheet Model
!
! Exposes two C-callable functions:
!   xuli_eval(tila, xsm, ysm, zaen, zsen, zden, rmp, ie_aen, ie_sen, ie_den)
!   xuli_tilt(doy, ut_hours, tilt_deg)
!
! Wraps the original SAEN, SSEN, SDEN, and STIL subroutines from xuli.for.
! All three variants share the same input signature; the shim calls each
! independently and returns all results in one call.
!
! IMPORTANT: In the original Fortran 77 source, variable names starting with
! I–N follow implicit typing (INTEGER).  Specifically:
!   IE  (in SAEN, SSEN, SDEN) — INTEGER flag (1=inside, 2=outside)
!   IM  (in SMPF)             — INTEGER flag (0 or 9999.99 stored as REAL)
! The interface blocks below must declare IE as integer to match.
!
module xuli_cshim
  use, intrinsic :: iso_c_binding, only: c_int, c_float
  implicit none
contains

  ! ----------------------------------------------------------------
  ! xuli_eval — compute all three neutral sheet variants at once
  !
  !   tila    : geomagnetic dipole tilt angle in degrees (float, in)
  !   xsm     : X position in GSM, Earth Radii (float, in)
  !   ysm     : Y position in GSM, Earth Radii (float, in)
  !   zaen    : AEN neutral sheet Z position, RE (float, out)
  !   zsen    : SEN neutral sheet Z position, RE (float, out)
  !   zden    : DEN neutral sheet Z position, RE (float, out)
  !   rmp     : magnetopause radius at XSM, RE (float, out)
  !   ie_aen  : 1=inside, 2=outside magnetopause (int, out)
  !   ie_sen  : 1=inside, 2=outside magnetopause (int, out)
  !   ie_den  : 1=inside, 2=outside magnetopause (int, out)
  ! ----------------------------------------------------------------
  subroutine xuli_eval(tila, xsm, ysm, zaen, zsen, zden, rmp, &
                        ie_aen, ie_sen, ie_den) bind(C, name="xuli_eval")
    real(c_float),  value, intent(in)  :: tila
    real(c_float),  value, intent(in)  :: xsm
    real(c_float),  value, intent(in)  :: ysm
    real(c_float),         intent(out) :: zaen
    real(c_float),         intent(out) :: zsen
    real(c_float),         intent(out) :: zden
    real(c_float),         intent(out) :: rmp
    integer(c_int),        intent(out) :: ie_aen
    integer(c_int),        intent(out) :: ie_sen
    integer(c_int),        intent(out) :: ie_den

    ! Local variables — IE is INTEGER in original Fortran 77 (implicit typing)
    integer :: ie_a, ie_s, ie_d
    real :: rmp_a, rmp_s, rmp_d

    interface
      subroutine SAEN(TILA, XSM, YSM, ZAEN, RMP, IE)
        real,    intent(in)  :: TILA, XSM, YSM
        real,    intent(out) :: ZAEN, RMP
        integer, intent(out) :: IE
      end subroutine SAEN

      subroutine SSEN(TILA, XSM, YSM, ZSEN, RMP, IE)
        real,    intent(in)  :: TILA, XSM, YSM
        real,    intent(out) :: ZSEN, RMP
        integer, intent(out) :: IE
      end subroutine SSEN

      subroutine SDEN(TILA, XSM, YSM, ZDEN, RMP, IE)
        real,    intent(in)  :: TILA, XSM, YSM
        real,    intent(out) :: ZDEN, RMP
        integer, intent(out) :: IE
      end subroutine SDEN
    end interface

    call SAEN(tila, xsm, ysm, zaen, rmp_a, ie_a)
    call SSEN(tila, xsm, ysm, zsen, rmp_s, ie_s)
    call SDEN(tila, xsm, ysm, zden, rmp_d, ie_d)

    ! RMP is the same from all three (SMPF called with same XSM)
    rmp = rmp_a
    ! IE is already integer (1 or 2)
    ie_aen = ie_a
    ie_sen = ie_s
    ie_den = ie_d
  end subroutine xuli_eval

  ! ----------------------------------------------------------------
  ! xuli_tilt — compute dipole tilt angle from DOY + UT
  !
  !   doy       : day of year, 1.0–366.0 (float, in)
  !   ut_hours  : universal time in hours (float, in)
  !   tilt_deg  : dipole tilt angle in degrees (float, out)
  ! ----------------------------------------------------------------
  subroutine xuli_tilt(doy, ut_hours, tilt_deg) bind(C, name="xuli_tilt")
    real(c_float),  value, intent(in)  :: doy
    real(c_float),  value, intent(in)  :: ut_hours
    real(c_float),         intent(out) :: tilt_deg

    real :: hr, tmi

    interface
      subroutine STIL(DOY, HR, TMI, TILA)
        real, intent(in)  :: DOY, HR, TMI
        real, intent(out) :: TILA
      end subroutine STIL
    end interface

    ! Decompose ut_hours into integer hours and minutes for STIL
    hr  = aint(ut_hours)
    tmi = (ut_hours - hr) * 60.0

    call STIL(doy, hr, tmi, tilt_deg)
  end subroutine xuli_tilt

end module xuli_cshim
