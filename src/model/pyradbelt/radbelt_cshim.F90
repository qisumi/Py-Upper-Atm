! radbelt_cshim.F90 — C ABI shim for RADBELT trapped radiation model (AP-8/AE-8)
!
! Exposes:
!   subroutine radbelt_load_data(ihead, nmap, map) — load model data arrays
!   subroutine radbelt_calc_flux(l_value, bb0, energies, flux, n) — compute fluxes
!
! Wraps TRARA1 from trmfun.for for use via ctypes / C callers.
!
! ihead(8) : header array from binary data file (input)
! nmap     : number of elements in map array (input)
! map(nmap): flux map array from binary data file (input)
! l_value  : L-value (input)
! bb0      : B/B0, magnetic field strength normalized to equatorial value (input)
! energies : array of energies in MeV (input)
! flux     : output array of log10(integral flux) in particles/(cm^2*s)
! n        : number of energies (input)

module radbelt_data
  use, intrinsic :: iso_c_binding, only: c_int, c_float
  implicit none

  integer(c_int), save :: g_ihead(8)
  integer(c_int), allocatable, save :: g_map(:)
  integer(c_int), save :: g_nmap = 0

end module radbelt_data


module radbelt_cshim
  use, intrinsic :: iso_c_binding, only: c_int, c_float
  use radbelt_data, only: g_ihead, g_map, g_nmap
  implicit none
contains

  subroutine radbelt_load_data(ihead, nmap, map) bind(C, name="radbelt_load_data")
    integer(c_int), intent(in) :: ihead(8)
    integer(c_int), value, intent(in) :: nmap
    integer(c_int), intent(in) :: map(nmap)

    g_ihead = ihead
    g_nmap = nmap

    if (allocated(g_map)) deallocate(g_map)
    allocate(g_map(nmap))
    g_map = map
  end subroutine radbelt_load_data


  subroutine radbelt_calc_flux(l_value, bb0, energies, flux, n) &
      bind(C, name="radbelt_calc_flux")
    real(c_float), value, intent(in)  :: l_value
    real(c_float), value, intent(in)  :: bb0
    real(c_float),        intent(in)  :: energies(n)
    real(c_float),        intent(out) :: flux(n)
    integer(c_int), value, intent(in) :: n

    interface
      subroutine TRARA1(DESCR, MAP, FL, BB0, E, F, N)
        integer, intent(in)  :: DESCR(8)
        integer, intent(in)  :: MAP(*)
        real,    intent(in)  :: FL
        real,    intent(in)  :: BB0
        real,    intent(in)  :: E(N)
        real,    intent(out) :: F(N)
        integer, intent(in)  :: N
      end subroutine TRARA1
    end interface

    call TRARA1(g_ihead, g_map, l_value, bb0, energies, flux, n)
  end subroutine radbelt_calc_flux

end module radbelt_cshim
