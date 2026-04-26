! oval_cshim.F90 — C ABI shim for Feldstein auroral oval (Holzworth & Meng)
!
! Exposes: void oval_eval(float xmlt, int iql, float *pcgl, float *ecgl)
!
! Wraps the original oval.for subroutine for use via ctypes / C callers.
! xmlt  : magnetic local time in hours (float)
! iql   : geomagnetic activity level 0 (quiet) – 6 (active) (int)
! pcgl  : output corrected geomagnetic latitude of poleward boundary (float)
! ecgl  : output corrected geomagnetic latitude of equatorward boundary (float)
!
module oval_cshim
  use, intrinsic :: iso_c_binding, only: c_int, c_float
  implicit none
contains
  subroutine oval_eval(xmlt, iql, pcgl, ecgl) bind(C, name="oval_eval")
    real(c_float),    value, intent(in)  :: xmlt
    integer(c_int),   value, intent(in)  :: iql
    real(c_float),           intent(out) :: pcgl
    real(c_float),           intent(out) :: ecgl

    interface
      subroutine OVAL(XMLT, IQL, PCGL, ECGL)
        real,    intent(in)  :: XMLT
        integer, intent(in)  :: IQL
        real,    intent(out) :: PCGL
        real,    intent(out) :: ECGL
      end subroutine OVAL
    end interface

    call OVAL(xmlt, iql, pcgl, ecgl)
  end subroutine oval_eval
end module oval_cshim
