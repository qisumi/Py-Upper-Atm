! cutoff_cshim.F90 — C ABI shim for Geomagnetic Cutoff Rigidity
!
! Exposes:
!   subroutine cutoff_trajectory(...)  — single trajectory at given rigidity
!   subroutine cutoff_rigidity_to_energy(...) — rigidity/energy conversion
!
! Uses GDGC, SINGLTJ, FGRAD, MAGNEW95 from cutoff_legacy.for for
! cosmic ray trajectory computation through the IGRF-95 geomagnetic field.

module cutoff_cshim
  use, intrinsic :: iso_c_binding, only: c_int, c_double
  implicit none

  ! Match F77 COMMON blocks exactly (same variable order and types)
  real(c_double) :: F(6), Y(6), ERAD, EOMC, VEL, BR, BT, BP, B
  common /WRKVLU/ F, Y, ERAD, EOMC, VEL, BR, BT, BP, B

  real(c_double) :: TSY2, TCY2, TSY3, TCY3
  common /WRKTSC/ TSY2, TCY2, TSY3, TCY3

  real(c_double) :: PI, RAD, PIO2
  common /TRIG/ PI, RAD, PIO2

  real(c_double) :: ERADPL, ERECSQ
  common /GEOID/ ERADPL, ERECSQ

  real(c_double) :: SALT, DISOUT, GCLATD, GDLATD, GLOND, GDAZD, GDZED
  real(c_double) :: RY1, RY2, RY3, RHT, TSTEP, PATH
  common /SNGLR/ SALT, DISOUT, GCLATD, GDLATD, GLOND, GDAZD, GDZED, &
                 RY1, RY2, RY3, RHT, TSTEP, PATH

  integer(c_int) :: LIMIT, NTRAJC, IERRPT
  common /SNGLI/ LIMIT, NTRAJC, IERRPT

contains

  ! -----------------------------------------------------------------------
  ! Initialize all COMMON block constants (replaces PROGRAM TJI95 setup)
  ! -----------------------------------------------------------------------
  subroutine cutoff_init()
    integer(c_int) :: io_status

    ERAD   = 6371.2d0
    DISOUT = 25.0d0
    RHT    = 20.0d0
    VEL    = 2.99792458d5 / ERAD
    PI     = ACOS(-1.0d0)
    RAD    = 180.0d0 / PI
    PIO2   = PI / 2.0d0
    SALT   = 20.0d0
    LIMIT  = 600000
    IERRPT = 0
    NTRAJC = 0
    TSTEP  = 0.0d0
    PATH   = 0.0d0

    ! Redirect legacy diagnostic output to scratch units so calls do not
    ! create fort.7/fort.8 files in the caller's working directory.
    close(7,  status='delete', iostat=io_status)
    close(8,  status='delete', iostat=io_status)
    close(16, status='delete', iostat=io_status)
    open(unit=7,  status='scratch', action='write', iostat=io_status)
    open(unit=8,  status='scratch', action='write', iostat=io_status)
    open(unit=16, status='scratch', action='write', iostat=io_status)
  end subroutine cutoff_init


  ! -----------------------------------------------------------------------
  ! Single trajectory at given rigidity
  ! -----------------------------------------------------------------------
  subroutine cutoff_trajectory(lat_deg, lon_deg, rigidity_gv, &
                               zenith_deg, azimuth_deg, &
                               result_code, faslat, faslon, path_length) &
    bind(C, name="cutoff_trajectory")

    real(c_double), value, intent(in)  :: lat_deg, lon_deg, rigidity_gv
    real(c_double), value, intent(in)  :: zenith_deg, azimuth_deg
    integer(c_int),        intent(out) :: result_code
    real(c_double),        intent(out) :: faslat, faslon, path_length

    real(c_double) :: TCD, TSD, GDAZ, GDZE
    real(c_double) :: TSGDZE, TCGDZE, TSGDAZ, TCGDAZ
    real(c_double) :: Y1GD, Y2GD, Y3GD, Y1GC, Y2GC, Y3GC
    real(c_double) :: PC
    integer(c_int) :: INDXPC, IRSLT

    real(c_double) :: TCY2tmp, TSY2tmp, YDA5, ATRG1, ATRG2

    ! Initialize COMMON block constants
    call cutoff_init()

    ! Set input parameters
    GDLATD = lat_deg
    GLOND  = lon_deg
    GDZED  = zenith_deg
    GDAZD  = azimuth_deg

    ! Convert geodetic to geocentric coordinates
    call GDGC(TCD, TSD)

    ! Store initial position
    RY2 = Y(2)
    RY3 = Y(3)
    RY1 = Y(1)

    ! Compute direction vector in geodetic coordinates
    GDAZ  = GDAZD / RAD
    GDZE  = GDZED / RAD
    TSGDZE = SIN(GDZE)
    TCGDZE = COS(GDZE)
    TSGDAZ = SIN(GDAZ)
    TCGDAZ = COS(GDAZ)

    Y1GD =  TCGDZE
    Y2GD = -TSGDZE * TCGDAZ
    Y3GD =  TSGDZE * TSGDAZ

    ! Convert to geocentric components
    Y1GC =  Y1GD * TCD + Y2GD * TSD
    Y2GC = -Y1GD * TSD + Y2GD * TCD
    Y3GC =  Y3GD

    ! Compute trajectory
    PC = rigidity_gv
    INDXPC = INT(PC * 1000.0d0 + 0.0001d0)
    call SINGLTJ(PC, IRSLT, INDXPC, Y1GC, Y2GC, Y3GC)

    result_code = IRSLT
    path_length = PATH

    ! Compute asymptotic coordinates
    if (IRSLT > 0) then
      ! Allowed trajectory
      TCY2tmp = COS(Y(2))
      TSY2tmp = SIN(Y(2))
      YDA5  = Y(5) * TCY2tmp + Y(4) * TSY2tmp
      ATRG1 = Y(4) * TCY2tmp - Y(5) * TSY2tmp
      ATRG2 = SQRT(Y(6) * Y(6) + YDA5 * YDA5)
      faslat = 0.0d0
      if (ATRG1 /= 0.0d0 .and. ATRG2 /= 0.0d0) &
        faslat = ATAN2(ATRG1, ATRG2) * RAD
      faslon = Y(3) * RAD
      if (Y(6) /= 0.0d0 .and. YDA5 /= 0.0d0) &
        faslon = (Y(3) + ATAN2(Y(6), YDA5)) * RAD
      if (faslon < 0.0d0)   faslon = faslon + 360.0d0
      if (faslon > 360.0d0) faslon = faslon - 360.0d0
    else if (IRSLT < 0) then
      ! Re-entrant trajectory
      faslat = (PIO2 - Y(2)) * RAD
      faslon = Y(3) * RAD
    else
      ! Failed trajectory
      faslat = 0.0d0
      faslon = 0.0d0
    end if

  end subroutine cutoff_trajectory


  ! -----------------------------------------------------------------------
  ! Rigidity to energy conversion (wrapper around azrgeg)
  ! -----------------------------------------------------------------------
  subroutine cutoff_rigidity_to_energy(atomic_number, charge, mass_amu, &
                                       rigidity_mv, energy_mev) &
    bind(C, name="cutoff_rigidity_to_energy")

    integer(c_int), value, intent(in)  :: atomic_number, charge
    real(c_double), value, intent(in)  :: mass_amu, rigidity_mv
    real(c_double),        intent(out) :: energy_mev

    real(c_double) :: rigin, epn, beta_val

    rigin = rigidity_mv
    epn   = 0.0d0
    call azrgeg(atomic_number, charge, mass_amu, rigin, epn, beta_val)
    energy_mev = epn

  end subroutine cutoff_rigidity_to_energy

end module cutoff_cshim
