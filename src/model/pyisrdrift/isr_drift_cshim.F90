! isr_drift_cshim.F90 — C ABI shim for ISR Ion Drift Model (Richmond et al., 1980)
!
! Exposes: void isr_drift_eval(float xmlat, float xmlon, float dayno, float ut,
!                               int isea, int iutav, float *pot, float *vu, float *ve)
!
! Wraps the original EFIELD subroutine from isr_drift.for for use via ctypes / C callers.
! xmlat  : magnetic latitude in degrees (float)
! xmlon  : magnetic east longitude in degrees (float)
! dayno  : day of year, 1.0–365.24, with 1.0 = Jan 1 (float)
! ut     : universal time in hours (float)
! isea   : seasonal averaging mode, 0–4 (int)
! iutav  : UT averaging mode, 0 or 1 (int)
! pot    : output electrostatic pseudo-potential in Volts (float)
! vu     : output poleward/upward E x B drift velocity in m/s (float)
! ve     : output eastward E x B drift velocity in m/s (float)
!
module isr_drift_cshim
  use, intrinsic :: iso_c_binding, only: c_int, c_float
  implicit none
contains
  subroutine isr_drift_eval(xmlat, xmlon, dayno, ut, isea, iutav, &
                             pot, vu, ve) bind(C, name="isr_drift_eval")
    real(c_float),  value, intent(in)  :: xmlat
    real(c_float),  value, intent(in)  :: xmlon
    real(c_float),  value, intent(in)  :: dayno
    real(c_float),  value, intent(in)  :: ut
    integer(c_int), value, intent(in)  :: isea
    integer(c_int), value, intent(in)  :: iutav
    real(c_float),         intent(out) :: pot
    real(c_float),         intent(out) :: vu
    real(c_float),         intent(out) :: ve

    interface
      subroutine EFIELD(XMLAT, XMLON, DAYNO, UT, ISEASAV, IUTAV, POT, VU, VE)
        real,    intent(in)  :: XMLAT, XMLON, DAYNO, UT
        integer, intent(in)  :: ISEASAV, IUTAV
        real,    intent(out) :: POT, VU, VE
      end subroutine EFIELD
    end interface

    call EFIELD(xmlat, xmlon, dayno, ut, isea, iutav, pot, vu, ve)
  end subroutine isr_drift_eval
end module isr_drift_cshim
