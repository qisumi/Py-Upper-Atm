! met_cshim.F90 — C ABI shim for Marshall Engineering Thermosphere (MET) model
!
! Exposes: void met_eval(float *indata, float *outdata, float *auxdata)
!
! Wraps the original met.for subroutines J70 and J70SUP for use via ctypes / C callers.
!
! indata   : input array (12 elements)
! outdata  : output array (12 elements)
! auxdata  : auxiliary output array (5 elements)
!
! Input array elements:
!   indata(1)  = altitude (km)
!   indata(2)  = latitude (degrees)
!   indata(3)  = longitude (degrees)
!   indata(4)  = year (yy, 2 digits)
!   indata(5)  = month (mm)
!   indata(6)  = day (dd)
!   indata(7)  = hour (hh)
!   indata(8)  = minute (mm)
!   indata(9)  = geomagnetic index (1=Kp, 2=Ap)
!   indata(10) = solar radio noise flux F10.7
!   indata(11) = 162-day average F10.7
!   indata(12) = geomagnetic activity index (Ap or Kp)
!
! Output array elements:
!   outdata(1)  = exospheric temperature (K)
!   outdata(2)  = temperature at altitude Z (K)
!   outdata(3)  = N2 number density (per m³)
!   outdata(4)  = O2 number density (per m³)
!   outdata(5)  = O number density (per m³)
!   outdata(6)  = Ar number density (per m³)
!   outdata(7)  = He number density (per m³)
!   outdata(8)  = H number density (per m³)
!   outdata(9)  = average molecular weight
!   outdata(10) = total density (kg/m³)
!   outdata(11) = log10(total density)
!   outdata(12) = total pressure (Pa)
!
! Auxiliary output array elements:
!   auxdata(1) = gravitational acceleration (m/s²)
!   auxdata(2) = ratio of specific heats
!   auxdata(3) = pressure scale-height (m)
!   auxdata(4) = specific heat at constant pressure
!   auxdata(5) = specific heat at constant volume
!
module met_cshim
  use, intrinsic :: iso_c_binding, only: c_float
  implicit none
contains

  subroutine met_eval(indata, outdata, auxdata) bind(C, name="met_eval")
    real(c_float), intent(in)  :: indata(12)
    real(c_float), intent(out) :: outdata(12)
    real(c_float), intent(out) :: auxdata(5)

    real*4 :: indata_local(12), outdata_local(12), auxdata_local(5)
    real*4 :: z

    interface
      subroutine J70(INDATA, OUTDATA)
        real*4, intent(in)  :: INDATA(12)
        real*4, intent(out) :: OUTDATA(12)
      end subroutine J70

      subroutine J70SUP(Z, OUTDATA, AUXDATA)
        real*4, intent(in)  :: Z
        real*4, intent(in)  :: OUTDATA(12)
        real*4, intent(out) :: AUXDATA(5)
      end subroutine J70SUP
    end interface

    ! Copy input data to local arrays (real*4)
    indata_local = real(indata, kind=4)

    ! Call J70 to compute atmospheric parameters
    call J70(indata_local, outdata_local)

    ! Get altitude for J70SUP
    z = indata_local(1)

    ! Call J70SUP to compute auxiliary parameters
    call J70SUP(z, outdata_local, auxdata_local)

    ! Copy results back to output arrays
    outdata = real(outdata_local, kind=c_float)
    auxdata = real(auxdata_local, kind=c_float)

  end subroutine met_eval

end module met_cshim
