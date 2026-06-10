! hmr_cshim.F90 — C ABI shim for Heppner-Maynard-Rich electric field model
!
!  Exposes:
!    void hmr_set_data_root(const char *path)
!    void hmr_epot(float lat, float lon, int model, int nmax,
!                  float *potential)
!    void hmr_pmodel(float lat, float lon_hrs, float pole2m, float pole2d,
!                    float *potential, float *dpdlat, float *dpdlt)
!    void hmr_conduct(float lat_deg, float mlt_hrs, float kp, int model_type,
!                     float sublat_deg, float f107, int sun_model_type,
!                     float *cond_total)
!    void hmr_full(float kp, float sublat_deg, float f107,
!                  int model, int nmax,
!                  float pole2m, float pole2d,
!                  float *ephi, float *ey, float *ez,
!                  float *sigma_h, float *sigma_p,
!                  float *joule, float *fac)
!
!  Wraps EPOT, PMODEL, CONDUCT, CONDSUN and the full computation
!  from hm_main.for for use via ctypes / C callers.
!
module hmr_cshim
  use, intrinsic :: iso_c_binding, only: c_int, c_float, c_char, c_null_char

  character(len=256) :: hmr_data_root = ''
  logical :: hmr_initialized = .false.

  ! Mirror the /RUNCON/ COMMON block as module variables so we can
  ! initialise them once and share with the legacy Fortran 77 subroutines.
  real :: hmr_PII, hmr_RAD, hmr_RE

  ! The legacy subroutines use COMMON /RUNCON/ PII,RAD,RE.
  ! Expose the same storage through a module-level COMMON block.
  common /RUNCON/ hmr_PII, hmr_RAD, hmr_RE

contains

  ! ------------------------------------------------------------------
  ! Set the directory containing HMR coefficient .dat files.
  ! ------------------------------------------------------------------
  subroutine hmr_set_data_root(path) bind(C, name="hmr_set_data_root")
    character(kind=c_char), intent(in) :: path(*)
    integer :: i

    hmr_data_root = ''
    do i = 1, len(hmr_data_root)
      if (path(i) == c_null_char) exit
      hmr_data_root(i:i) = achar(iachar(path(i)))
    enddo
  end subroutine

  ! ------------------------------------------------------------------
  ! Initialize /RUNCON/ COMMON block if not already done.
  ! ------------------------------------------------------------------
  subroutine hmr_init_common()
    if (.not. hmr_initialized) then
      hmr_PII = 4.0 * ATAN(1.0)
      hmr_RAD = 180.0 / hmr_PII
      hmr_RE = 6.49E6
      hmr_initialized = .true.
    endif
  end subroutine

  ! ------------------------------------------------------------------
  ! Compute Heppner-Maynard electric potential at one point.
  ! ------------------------------------------------------------------
  subroutine hmr_epot(lat, lon, model, nmax, &
                      potential) bind(C, name="hmr_epot")
    real(c_float),  value, intent(in)  :: lat, lon
    integer(c_int), value, intent(in)  :: model, nmax
    real(c_float),         intent(out) :: potential

    character(len=512) :: coeff_file
    integer :: ios
    real :: achg, bchg, dxchg, dychg, ahm, bhm, dxhm, dyhm

    interface
      subroutine EPOT(TLAT,TLON,VALUE,NTAPE,IABC,NNMAX,ACHG,BCHG,DXCHG, &
                      DYCHG,AHM,BHM,DXHM,DYHM,ICHGHM)
        real, intent(in)    :: TLAT, TLON
        real, intent(out)   :: VALUE
        integer, intent(in) :: NTAPE, IABC, NNMAX
        real, intent(in)    :: ACHG, BCHG, DXCHG, DYCHG
        real, intent(in)    :: AHM, BHM, DXHM, DYHM
        integer, intent(in) :: ICHGHM
      end subroutine EPOT
    end interface

    call hmr_init_common()

    coeff_file = trim(hmr_data_root) // '/hmcoef.dat'

    open(unit=99, file=trim(coeff_file), status='old', iostat=ios)
    if (ios /= 0) then
      potential = 0.0
      return
    endif

    achg = 0.0; bchg = 0.0; dxchg = 0.0; dychg = 0.0
    ahm = 0.0;  bhm = 0.0;  dxhm = 0.0;  dyhm = 0.0

    call EPOT(lat, lon, potential, 99, model, nmax, &
              achg, bchg, dxchg, dychg, &
              ahm, bhm, dxhm, dyhm, 0)

    close(unit=99)
  end subroutine

  ! ------------------------------------------------------------------
  ! Compute Heelis model electric potential at one point.
  ! ------------------------------------------------------------------
  subroutine hmr_pmodel(lat, lon_hrs, pole2m, pole2d, &
                        potential, dpdlat, dpdlt) bind(C, name="hmr_pmodel")
    real(c_float), value, intent(in)  :: lat, lon_hrs, pole2m, pole2d
    real(c_float),        intent(out) :: potential, dpdlat, dpdlt

    real :: gmlat2, tloc2

    interface
      subroutine PBROT(GMLAT1, GMLT1, ANGLE, DMLT, GMLAT2, GMLT2)
        real, intent(in)  :: GMLAT1, GMLT1, ANGLE, DMLT
        real, intent(out) :: GMLAT2, GMLT2
      end subroutine PBROT
      subroutine PMODEL(RLAT, RLT, POT, PLAT, PLT)
        real, intent(in)  :: RLAT, RLT
        real, intent(out) :: POT, PLAT, PLT
      end subroutine PMODEL
    end interface

    call hmr_init_common()

    call PBROT(lat, lon_hrs, pole2m, pole2d, gmlat2, tloc2)
    call PMODEL(gmlat2, tloc2, potential, dpdlat, dpdlt)
  end subroutine

  ! ------------------------------------------------------------------
  ! Compute conductivity at one point.
  ! ------------------------------------------------------------------
  subroutine hmr_conduct(lat_deg, mlt_hrs, kp, model_type, &
                         sublat_deg, f107, sun_model_type, &
                         cond_total) bind(C, name="hmr_conduct")
    real(c_float),  value, intent(in)  :: lat_deg, mlt_hrs, kp
    integer(c_int), value, intent(in)  :: model_type
    real(c_float),  value, intent(in)  :: sublat_deg, f107
    integer(c_int), value, intent(in)  :: sun_model_type
    real(c_float),         intent(out) :: cond_total

    real :: conj, consun, gmlt, colat, colats
    integer :: kp_int
    real :: dkp, cutl, cuth

    interface
      subroutine CONDUCT(ALAT,ANMLT,KP,DKP,CUTL,CUTH,MODEL,CON)
        real, intent(in)    :: ALAT, ANMLT
        integer, intent(in) :: KP
        real, intent(in)    :: DKP, CUTL, CUTH
        integer, intent(in) :: MODEL
        real, intent(out)   :: CON
      end subroutine CONDUCT
      subroutine CONDSUN(COLAT, GMLT, COLATS, GMLTS, F107, MODEL, CONS)
        real, intent(in)    :: COLAT, GMLT, COLATS, GMLTS, F107
        integer, intent(in) :: MODEL
        real, intent(out)   :: CONS
      end subroutine CONDSUN
    end interface

    call hmr_init_common()

    kp_int = int(kp)
    dkp = kp - float(kp_int)
    cutl = 0.01
    cuth = 0.5

    call CONDUCT(lat_deg, mlt_hrs, kp_int, dkp, cutl, cuth, model_type, conj)

    gmlt = (mlt_hrs * 15.0) / hmr_RAD
    colat = (90.0 - lat_deg) / hmr_RAD
    colats = (90.0 - sublat_deg) / hmr_RAD
    call CONDSUN(colat, gmlt, colats, hmr_PII, f107, sun_model_type, consun)

    cond_total = SQRT(conj**2 + consun**2)
  end subroutine

  ! ------------------------------------------------------------------
  ! Full computation: potential + E-field + Joule heating + FAC.
  ! Grid: 41 latitude bins (50-90 deg) x 25 MLT bins (0-24 hrs)
  ! ------------------------------------------------------------------
  subroutine hmr_full(kp, sublat_deg, f107, &
                      model, nmax, pole2m, pole2d, &
                      ephi, ey, ez, sigma_h, sigma_p, &
                      joule, fac) bind(C, name="hmr_full")
    real(c_float),  value, intent(in) :: kp, sublat_deg, f107
    integer(c_int), value, intent(in) :: model, nmax
    real(c_float),  value, intent(in) :: pole2m, pole2d
    real(c_float),         intent(out) :: ephi(41,25), ey(41,25), ez(41,25)
    real(c_float),         intent(out) :: sigma_h(41,25), sigma_p(41,25)
    real(c_float),         intent(out) :: joule(41,25), fac(41,25)

    real :: SH(41,25), SP(41,25), CZ(41,25), CY(41,25)
    real :: C11(41,25), Y(41)
    real :: PHI, DPDLAT, DPDLT
    real :: GMLAT, GLONG, TLOC, ALAT, GMLT, COLAT, COLATS
    real :: CONJ, CONSUN
    real :: DLY2D, DLY2M, DLZ2M, DLMLT, DLILAT
    real :: YA, CTHE, SKAI
    real :: achg, bchg, dxchg, dychg, ahm, bhm, dxhm, dyhm
    real :: GMLAT2, TLOC2
    integer :: IMLT, ILAT, I, J, IP, IM, JP, JM
    integer :: kp_int, MODEL_idx
    real :: dkp, cutl, cuth
    character(len=512) :: coeff_file
    integer :: ios
    integer :: NMLT, JMLT

    interface
      subroutine EPOT(TLAT,TLON,VALUE,NTAPE,IABC,NNMAX,ACHG,BCHG,DXCHG, &
                      DYCHG,AHM,BHM,DXHM,DYHM,ICHGHM)
        real, intent(in)    :: TLAT, TLON
        real, intent(out)   :: VALUE
        integer, intent(in) :: NTAPE, IABC, NNMAX
        real, intent(in)    :: ACHG, BCHG, DXCHG, DYCHG
        real, intent(in)    :: AHM, BHM, DXHM, DYHM
        integer, intent(in) :: ICHGHM
      end subroutine EPOT
      subroutine PBROT(GMLAT1, GMLT1, ANGLE, DMLT, GMLAT2, GMLT2)
        real, intent(in)  :: GMLAT1, GMLT1, ANGLE, DMLT
        real, intent(out) :: GMLAT2, GMLT2
      end subroutine PBROT
      subroutine PMODEL(RLAT, RLT, POT, PLAT, PLT)
        real, intent(in)  :: RLAT, RLT
        real, intent(out) :: POT, PLAT, PLT
      end subroutine PMODEL
      subroutine CONDUCT(ALAT,ANMLT,KP,DKP,CUTL,CUTH,MODEL_var,CON)
        real, intent(in)    :: ALAT, ANMLT
        integer, intent(in) :: KP
        real, intent(in)    :: DKP, CUTL, CUTH
        integer, intent(in) :: MODEL_var
        real, intent(out)   :: CON
      end subroutine CONDUCT
      subroutine CONDSUN(COLAT_var, GMLT_var, COLATS_var, GMLTS, F107, MODEL_var, CONS)
        real, intent(in)    :: COLAT_var, GMLT_var, COLATS_var, GMLTS, F107
        integer, intent(in) :: MODEL_var
        real, intent(out)   :: CONS
      end subroutine CONDSUN
    end interface

    call hmr_init_common()

    NMLT = 24
    JMLT = NMLT + 1
    DLMLT = 2.0 * hmr_PII / FLOAT(NMLT)
    DLILAT = 1.0 / hmr_RAD
    DLY2D = 2.0 * DLMLT * hmr_RE
    DLZ2M = 2.0 * DLILAT * hmr_RE

    coeff_file = trim(hmr_data_root) // '/hmcoef.dat'
    open(unit=99, file=trim(coeff_file), status='old', iostat=ios)
    if (ios /= 0) then
      ephi = 0.0; ey = 0.0; ez = 0.0
      sigma_h = 0.0; sigma_p = 0.0
      joule = 0.0; fac = 0.0
      return
    endif

    kp_int = int(kp)
    dkp = kp - float(kp_int)
    cutl = 0.01
    cuth = 0.5
    COLATS = (90.0 - sublat_deg) / hmr_RAD

    ! ---- Compute conductivities (Hall=1, Pedersen=2) ----
    DO MODEL_idx = 1, 2
      DO IMLT = 1, JMLT
        TLOC = IMLT - 13
        IF (TLOC .LT. 0.0) TLOC = TLOC + 24.0
        DO ILAT = 1, 41
          ALAT = 91 - ILAT
          CALL CONDUCT(ALAT, TLOC, kp_int, dkp, cutl, cuth, MODEL_idx, CONJ)
          GMLT = (TLOC * 15.0) / hmr_RAD
          COLAT = (90.0 - ALAT) / hmr_RAD
          CALL CONDSUN(COLAT, GMLT, COLATS, hmr_PII, f107, MODEL_idx, CONSUN)
          Y(ILAT) = SQRT(CONJ**2 + CONSUN**2)
          IF (MODEL_idx .EQ. 1) THEN
            sigma_h(ILAT, IMLT) = Y(ILAT)
          ELSE
            sigma_p(ILAT, IMLT) = Y(ILAT)
          ENDIF
        ENDDO
      ENDDO
    ENDDO

    ! ---- Compute electric potential ----
    achg = 0.0; bchg = 0.0; dxchg = 0.0; dychg = 0.0
    ahm = 0.0;  bhm = 0.0;  dxhm = 0.0;  dyhm = 0.0

    DO IMLT = 1, JMLT
      TLOC = IMLT - 13
      DO ILAT = 3, 40
        GLONG = TLOC * 15.0
        GMLAT = FLOAT(91 - ILAT)
        IF (model .LT. 8) THEN
          CALL EPOT(GMLAT, GLONG, PHI, 99, model, nmax, &
                    achg, bchg, dxchg, dychg, &
                    ahm, bhm, dxhm, dyhm, 0)
        ELSE
          CALL PBROT(GMLAT, TLOC, pole2m, pole2d, GMLAT2, TLOC2)
          CALL PMODEL(GMLAT2, TLOC2, PHI, DPDLAT, DPDLT)
        ENDIF
        ephi(ILAT, IMLT) = PHI * 1.0E3
      ENDDO
      ephi(41, IMLT) = ephi(40, IMLT)
    ENDDO

    ! Extrapolate above 88 degrees
    YA = 0.0
    DO J = 1, 24
      YA = YA + ephi(3, J)
    ENDDO
    YA = YA / 24.0
    DO J = 1, 25
      ephi(1, J) = YA
      ephi(2, J) = (ephi(3, J) + YA) / 2.0
    ENDDO

    ! Adjust so low-latitude potential is zero
    YA = 0.0
    DO J = 1, 24
      YA = YA + ephi(41, J)
    ENDDO
    YA = YA / 24.0
    DO J = 1, 25
      DO I = 1, 41
        ephi(I, J) = ephi(I, J) - YA
      ENDDO
    ENDDO

    ! ---- Compute E-field (MV/m) ----
    DO I = 2, 40
      COLAT = FLOAT(I - 1) / hmr_RAD
      DLY2M = DLY2D * SIN(COLAT)
      IP = I + 1
      IM = I - 1
      DO J = 1, JMLT
        JP = J + 1
        JM = J - 1
        IF (J .EQ. 1) JM = JMLT - 1
        IF (J .EQ. JMLT) JP = 2
        ez(I, J) = 1.0E3 * (ephi(IM, J) - ephi(IP, J)) / DLZ2M
        ey(I, J) = 1.0E3 * (ephi(I, JM) - ephi(I, JP)) / DLY2M
      ENDDO
    ENDDO
    DO J = 1, JMLT
      ez(1, J) = ez(2, J)
      ey(1, J) = ey(2, J)
      ez(41, J) = ez(40, J)
      ey(41, J) = ey(40, J)
    ENDDO

    ! ---- Joule heating (mW/m^2) ----
    DO IMLT = 1, JMLT
      DO ILAT = 1, 41
        joule(ILAT, IMLT) = sigma_p(ILAT, IMLT) * &
                            (ey(ILAT, IMLT)**2 + ez(ILAT, IMLT)**2) * 1.0E-3
      ENDDO
    ENDDO

    ! ---- Ionospheric current (A/km) ----
    DO I = 3, 41
      COLAT = FLOAT(I - 1) / hmr_RAD
      CTHE = COS(COLAT)
      SKAI = 2.0 * CTHE / SQRT(1.0 + 3.0 * CTHE * CTHE)
      DO J = 1, JMLT
        CZ(I, J) = sigma_p(I, J) / SKAI * ez(I, J) + sigma_h(I, J) * ey(I, J)
        CY(I, J) = -sigma_h(I, J) * ez(I, J) + sigma_p(I, J) * SKAI * ey(I, J)
      ENDDO
    ENDDO
    DO J = 1, JMLT
      CZ(1, J) = 0.0; CY(1, J) = 0.0
      CZ(2, J) = CZ(3, J) / 2.0
      CY(2, J) = CY(3, J) / 2.0
    ENDDO

    ! ---- Field-aligned current (uA/m^2) ----
    DO I = 2, 40
      COLAT = FLOAT(I - 1) / hmr_RAD
      DLY2M = DLY2D * SIN(COLAT)
      IP = I + 1
      IM = I - 1
      DO J = 1, JMLT
        JP = J + 1
        JM = J - 1
        IF (J .EQ. 1) JM = JMLT - 1
        IF (J .EQ. JMLT) JP = 2
        C11(I, J) = 1.0E3 * ((CZ(IP, J) - CZ(IM, J)) / DLZ2M &
                             + (CY(I, JP) - CY(I, JM)) / DLY2M)
      ENDDO
    ENDDO
    DO J = 1, JMLT
      C11(41, J) = C11(40, J)
    ENDDO

    ! FAC at pole independent of MLT
    YA = 0.0
    DO J = 1, 24
      YA = YA + C11(2, J)
    ENDDO
    YA = YA / 24.0
    DO J = 1, 25
      C11(1, J) = YA
    ENDDO

    DO J = 1, 25
      DO I = 1, 41
        fac(I, J) = C11(I, J)
      ENDDO
    ENDDO

    close(unit=99)
  end subroutine

end module hmr_cshim
