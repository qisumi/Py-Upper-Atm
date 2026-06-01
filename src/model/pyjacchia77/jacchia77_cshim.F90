! jacchia77_cshim.F90 — C ABI shim for Jacchia 1977 Reference Atmosphere
!
! Exposes: void jacchia77_eval(float Tinf, float *alt_km, int n_alt,
!                             float *T_out, float *N2_out, float *O2_out,
!                             float *O_out, float *Ar_out, float *He_out,
!                             float *H_out, float *rho_out, float *W_out)
!
! Wraps the original j77sri.for subroutine for use via ctypes / C callers.
! Tinf    : exospheric temperature in K (float, input)
! alt_km  : array of altitudes in km (float, input)
! n_alt   : number of altitudes (int, input)
! T_out   : temperature at each altitude (float, output)
! N2_out  : N2 number density at each altitude (float, output)
! O2_out  : O2 number density at each altitude (float, output)
! O_out   : O number density at each altitude (float, output)
! Ar_out  : Ar number density at each altitude (float, output)
! He_out  : He number density at each altitude (float, output)
! H_out   : H number density at each altitude (float, output)
! rho_out : total number density at each altitude (float, output)
! W_out   : molecular weight at each altitude (float, output)
!
module jacchia77_cshim
  use, intrinsic :: iso_c_binding, only: c_int, c_float
  implicit none

  ! Maximum altitude for internal profile calculation
  integer, parameter :: MAXZ = 2500

contains

  subroutine jacchia77_eval(Tinf, alt_km, n_alt, &
      T_out, N2_out, O2_out, O_out, Ar_out, He_out, H_out, rho_out, W_out) &
      bind(C, name="jacchia77_eval")

    real(c_float), value, intent(in)  :: Tinf
    real(c_float),           intent(in)  :: alt_km(*)
    integer(c_int),   value, intent(in)  :: n_alt
    real(c_float),           intent(out) :: T_out(*)
    real(c_float),           intent(out) :: N2_out(*)
    real(c_float),           intent(out) :: O2_out(*)
    real(c_float),           intent(out) :: O_out(*)
    real(c_float),           intent(out) :: Ar_out(*)
    real(c_float),           intent(out) :: He_out(*)
    real(c_float),           intent(out) :: H_out(*)
    real(c_float),           intent(out) :: rho_out(*)
    real(c_float),           intent(out) :: W_out(*)

    ! Internal arrays for full profile calculation
    real :: Z(0:MAXZ), T(0:MAXZ), CN2(0:MAXZ), CO2(0:MAXZ)
    real :: CO(0:MAXZ), CAr(0:MAXZ), CHe(0:MAXZ), CH(0:MAXZ)
    real :: CM(0:MAXZ), WM(0:MAXZ)

    integer :: i, iz
    real :: alt, frac
    integer :: iz_low, iz_high

    interface
      subroutine j77sri(maxz, Tinf, Z, T, CN2, CO2, CO, CAr, CHe, CH, CM, WM)
        integer, intent(in) :: maxz
        real, intent(in) :: Tinf
        real, intent(out) :: Z(0:maxz), T(0:maxz), CN2(0:maxz), CO2(0:maxz)
        real, intent(out) :: CO(0:maxz), CAr(0:maxz), CHe(0:maxz), CH(0:maxz)
        real, intent(out) :: CM(0:maxz), WM(0:maxz)
      end subroutine j77sri
    end interface

    ! Calculate full profile
    call j77sri(MAXZ, real(Tinf), Z, T, CN2, CO2, CO, CAr, CHe, CH, CM, WM)

    ! Interpolate to requested altitudes
    do i = 1, n_alt
      alt = real(alt_km(i))

      ! Clamp to valid range
      if (alt < 0.0) alt = 0.0
      if (alt > real(MAXZ)) alt = real(MAXZ)

      ! Find bracketing indices
      iz_low = int(alt)
      iz_high = iz_low + 1
      if (iz_high > MAXZ) then
        iz_high = MAXZ
        iz_low = MAXZ
      end if

      ! Interpolation factor
      frac = alt - real(iz_low)

      ! Linear interpolation
      T_out(i)    = T(iz_low)    + frac * (T(iz_high)    - T(iz_low))
      N2_out(i)   = CN2(iz_low)  + frac * (CN2(iz_high)  - CN2(iz_low))
      O2_out(i)   = CO2(iz_low)  + frac * (CO2(iz_high)  - CO2(iz_low))
      O_out(i)    = CO(iz_low)   + frac * (CO(iz_high)   - CO(iz_low))
      Ar_out(i)   = CAr(iz_low)  + frac * (CAr(iz_high)  - CAr(iz_low))
      He_out(i)   = CHe(iz_low)  + frac * (CHe(iz_high)  - CHe(iz_low))
      H_out(i)    = CH(iz_low)   + frac * (CH(iz_high)   - CH(iz_low))
      rho_out(i)  = CM(iz_low)   + frac * (CM(iz_high)   - CM(iz_low))
      W_out(i)    = WM(iz_low)   + frac * (WM(iz_high)   - WM(iz_low))
    end do

  end subroutine jacchia77_eval

end module jacchia77_cshim
