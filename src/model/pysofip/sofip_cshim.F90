! sofip_cshim.F90 — C ABI shim for SOFIP (Short Orbital Flux Integration Program)
!
! Exposes:
!   subroutine sofip_load_data(ihead, nmap, map) — load radiation belt map data
!   subroutine sofip_integrate(...)              — orbit-averaged flux integration
!   subroutine sofip_is_loaded(flag)             — check if data is loaded
!
! Uses TRARA1/TRARA2 from sofip_legacy.for for per-point flux lookup,
! DSPCTR for differential spectrum, and SOFIP_SOLPRO for solar proton fluence.

module sofip_data
  use, intrinsic :: iso_c_binding, only: c_int, c_float
  implicit none

  integer(c_int), save :: g_ihead(8)       ! map header (8 integers)
  integer(c_int), allocatable, save :: g_map(:) ! map data array
  integer(c_int), save :: g_nmap = 0
  logical, save :: g_loaded = .false.

end module sofip_data


module sofip_cshim
  use, intrinsic :: iso_c_binding, only: c_int, c_float
  use sofip_data, only: g_ihead, g_map, g_nmap, g_loaded
  implicit none

  ! Proton energy levels (MeV), 30 thresholds + 1 sentinel
  real(c_float), parameter, private :: E_PROTON(31) = [ &
    2.0, 3.0, 4.0, 5.0, 6.0, 8.0, 10.0, 15.0, 20.0, 25.0, &
    30.0, 35.0, 40.0, 45.0, 50.0, 55.0, 60.0, 70.0, 80.0, 90.0, &
    100.0, 125.0, 150.0, 175.0, 200.0, 250.0, 300.0, 350.0, 400.0, 500.0, &
    0.0 ]

  ! Electron energy levels (MeV), 30 thresholds + 1 sentinel
  real(c_float), parameter, private :: E_ELECTRON(31) = [ &
    0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, &
    1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0, 3.25, 3.5, &
    3.75, 4.0, 4.25, 4.5, 4.75, 5.0, 5.5, 6.0, 6.5, 7.0, &
    0.0 ]

  ! Solar proton energy levels (MeV), 20 values
  real(c_float), parameter, private :: E_SOLPRO(20) = [ &
    10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0, &
    110.0, 120.0, 130.0, 140.0, 150.0, 160.0, 170.0, 180.0, 190.0, 200.0 ]

  ! Equatorial magnetic field at L=1 (gauss)
  real(c_float), parameter, private :: B0_EQ = 0.311653

contains

  ! -----------------------------------------------------------------------
  ! Load radiation belt map data (same format as RADBELT)
  ! -----------------------------------------------------------------------
  subroutine sofip_load_data(ihead, nmap, map) bind(C, name="sofip_load_data")
    integer(c_int), intent(in) :: ihead(8)
    integer(c_int), value, intent(in) :: nmap
    integer(c_int), intent(in) :: map(nmap)

    g_ihead = ihead
    g_nmap = nmap

    if (allocated(g_map)) deallocate(g_map)
    allocate(g_map(nmap))
    g_map = map
    g_loaded = .true.
  end subroutine sofip_load_data


  ! -----------------------------------------------------------------------
  ! Check if data has been loaded
  ! -----------------------------------------------------------------------
  subroutine sofip_is_loaded(flag) bind(C, name="sofip_is_loaded")
    integer(c_int), intent(out) :: flag
    if (g_loaded) then
      flag = 1
    else
      flag = 0
    end if
  end subroutine sofip_is_loaded


  ! -----------------------------------------------------------------------
  ! Main orbit integration routine
  !
  ! For each trajectory point (time, B, L), computes trapped radiation
  ! flux at 30 energy levels using TRARA1. Accumulates and normalizes to
  ! produce orbit-averaged integral and differential flux spectra.
  ! Also computes solar proton fluence via SOFIP_SOLPRO for regions
  ! with L >= 5 (weak geomagnetic shielding).
  ! -----------------------------------------------------------------------
  subroutine sofip_integrate( &
      npts, times, l_vals, b_vals, &
      itype, dur_months, conf_pct, &
      energy_levels, integ_flux, diff_flux, diff_integ, &
      sol_energy, sol_fluence, n_al_events, exposure_factor, &
      lzone_counts, total_time, kpstep_out) &
      bind(C, name="sofip_integrate")

    integer(c_int), value, intent(in)  :: npts        ! number of trajectory points
    real(c_float),        intent(in)  :: times(npts)  ! time in hours
    real(c_float),        intent(in)  :: l_vals(npts) ! L-shell (earth radii)
    real(c_float),        intent(in)  :: b_vals(npts) ! B-field (gauss)
    integer(c_int), value, intent(in)  :: itype       ! 1=proton, 2=electron
    real(c_float), value, intent(in)  :: dur_months   ! mission duration (months) for SOLPRO
    integer(c_int), value, intent(in)  :: conf_pct    ! confidence % for SOLPRO (80-99)

    real(c_float), intent(out) :: energy_levels(30) ! energy levels (MeV)
    real(c_float), intent(out) :: integ_flux(30)    ! averaged integral flux (#/cm2/s)
    real(c_float), intent(out) :: diff_flux(30)     ! differential flux (#/cm2/s/keV)
    real(c_float), intent(out) :: diff_integ(30)    ! difference integral flux (#/cm2/s/DE)
    real(c_float), intent(out) :: sol_energy(20)    ! solar proton energy levels (MeV)
    real(c_float), intent(out) :: sol_fluence(20)   ! solar proton fluence (#/cm2)
    integer(c_int), intent(out) :: n_al_events      ! number of AL events
    real(c_float), intent(out) :: exposure_factor   ! exposure factor for solar protons
    integer(c_int), intent(out) :: lzone_counts(4)  ! L-zone point counts
    real(c_float), intent(out) :: total_time         ! total trajectory time (hours)
    real(c_float), intent(out) :: kpstep_out         ! time step (minutes)

    ! Local variables
    real(c_float) :: energies(31)  ! energy table (30 + sentinel)
    real(c_float) :: algflx(30)    ! log10(flux) at current point
    real(c_float) :: fluxes(30)    ! linear flux at current point
    real :: alnflx(30)             ! log of averaged integral flux (for DSPCTR)
    real :: difspc(30)             ! differential flux (from DSPCTR)
    real :: f_sol(20)              ! solar proton fluence (raw)
    real(c_float) :: bb0, psnl, psnb, psntim, tmlast
    real(c_float) :: kpstep, afctrs, flxsum
    real(c_float) :: expotm
    integer :: l_ge5, nrg, ipass

    ! Interfaces to legacy routines
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

      subroutine DSPCTR(FF, XX, DD)
        real*4, intent(in)  :: FF(30)
        real*4, intent(in)  :: XX(30)
        real*4, intent(out) :: DD(30)
      end subroutine DSPCTR

      subroutine SOFIP_SOLPRO(TAU, IQ, F, INALE)
        real,    intent(in)  :: TAU
        integer, intent(in)  :: IQ
        real,    intent(out) :: F(20)
        integer, intent(out) :: INALE
      end subroutine SOFIP_SOLPRO
    end interface

    ! --- Initialize ---
    if (itype == 1) then
      energies(1:31) = E_PROTON(1:31)
    else
      energies(1:31) = E_ELECTRON(1:31)
    end if

    ! Copy energy levels to output
    energy_levels(1:30) = energies(1:30)

    ! Zero all accumulators
    integ_flux = 0.0
    diff_flux = 0.0
    diff_integ = 0.0
    sol_energy = E_SOLPRO
    sol_fluence = 0.0
    n_al_events = 0
    exposure_factor = 0.0
    lzone_counts = 0
    total_time = 0.0
    kpstep_out = 0.0

    flxsum = 0.0
    l_ge5 = 0
    tmlast = 0.0
    kpstep = 0.0

    if (npts < 1) return

    ! --- Main integration loop ---
    do ipass = 1, npts
      psntim = times(ipass)
      psnl = l_vals(ipass)
      psnb = b_vals(ipass)

      ! Calculate time step (minutes between consecutive points)
      if (ipass == 1) then
        kpstep = 1.0  ! default for first point
      else
        kpstep = int((psntim - tmlast) / 0.0166667 + 0.1)
        if (kpstep < 1.0) kpstep = 1.0
      end if
      tmlast = psntim

      ! Convert absolute B (gauss) and L to B/B0
      ! B0 = B0_EQ / L^3 (equatorial field at given L)
      if (psnl > 0.0) then
        bb0 = psnb * psnl**3 / B0_EQ
      else
        bb0 = 1.0
      end if

      ! Test L-value: bypass flux calculation if outside valid range
      if (psnl > 0.0 .and. psnl < 12.0) then
        ! Call TRARA1 for 30 energy levels
        call TRARA1(g_ihead, g_map, real(psnl), real(bb0), &
                    energies(1), algflx, 30)
      else
        algflx = 0.0
      end if

      ! Convert log-flux to linear flux, accumulate
      do nrg = 1, 30
        fluxes(nrg) = 10.0**algflx(nrg)
        if (fluxes(nrg) < 1.001) fluxes(nrg) = 0.0
        integ_flux(nrg) = integ_flux(nrg) + fluxes(nrg)
      end do

      ! L-zone tracking
      ! Zone 1: 0 <= L < 1.1
      ! Zone 2: 1.1 <= L < 2.8 (inner zone)
      ! Zone 3: 2.8 <= L < 11.0 (outer zone)
      ! Zone 4: L >= 11.0 or L < 0 (external)
      if (psnl >= 0.0 .and. psnl < 1.1) then
        lzone_counts(1) = lzone_counts(1) + 1
      else if (psnl >= 1.1 .and. psnl < 2.8) then
        lzone_counts(2) = lzone_counts(2) + 1
      else if (psnl >= 2.8 .and. psnl < 11.0) then
        lzone_counts(3) = lzone_counts(3) + 1
      else
        lzone_counts(4) = lzone_counts(4) + 1
      end if

      ! Geomagnetic shielding counter (for solar proton exposure)
      ! Points with L >= 5 or L <= 0 have weak shielding
      if (int(psnl) >= 5 .or. psnl <= 0.0) then
        l_ge5 = l_ge5 + 1
      end if

    end do

    ! --- Normalize: compute orbit-averaged integral flux ---
    total_time = tmlast
    kpstep_out = kpstep

    if (tmlast > 0.0 .and. kpstep > 0.0) then
      ! AFCTRS converts accumulated sum to time-averaged flux
      ! Original formula: AFCTRS = (KPSTEP * 1440) / (TMLAST * 86400)
      afctrs = (kpstep * 1440.0) / (tmlast * 86400.0)

      do nrg = 1, 30
        integ_flux(nrg) = integ_flux(nrg) * afctrs
      end do
    end if

    ! Difference integral flux (integral flux at E_n minus E_{n+1})
    do nrg = 1, 29
      diff_integ(nrg) = integ_flux(nrg) - integ_flux(nrg + 1)
    end do
    diff_integ(30) = integ_flux(30)

    ! --- Differential spectrum via DSPCTR ---
    ! DSPCTR needs log of averaged integral fluxes
    do nrg = 1, 30
      if (integ_flux(nrg) > 0.0) then
        alnflx(nrg) = alog(integ_flux(nrg))
      else
        alnflx(nrg) = 0.0
      end if
    end do
    call DSPCTR(alnflx, energies, difspc)
    diff_flux(1:30) = difspc(1:30)

    ! --- Solar proton fluence ---
    ! Only meaningful when there are points with weak geomagnetic shielding
    if (l_ge5 > 0 .and. tmlast > 0.0) then
      call SOFIP_SOLPRO(real(dur_months), conf_pct, f_sol, n_al_events)
      ! Exposure factor: fraction of total time spent with weak shielding
      expotm = float(l_ge5 * int(kpstep)) * 0.0166667
      exposure_factor = expotm / tmlast
      do nrg = 1, 20
        sol_fluence(nrg) = f_sol(nrg) * exposure_factor
      end do
    else
      n_al_events = 0
      exposure_factor = 0.0
      sol_fluence = 0.0
    end if

  end subroutine sofip_integrate

end module sofip_cshim
