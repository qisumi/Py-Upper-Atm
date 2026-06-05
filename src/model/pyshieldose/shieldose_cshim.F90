! C ABI shim for SHIELDOSE radiation dose model.
! Data is loaded from Python; Fortran handles computation only.

module shieldose_data
  use, intrinsic :: iso_c_binding, only: c_int, c_float, c_double
  implicit none

  ! Lookup table dimensions
  integer(c_int) :: g_mpmax, g_lpmax, g_kmax
  integer(c_int) :: g_memax, g_lemax, g_mbmax, g_lbmax

  ! Proton data (stored in log-space) - with padding for spline extrapolation
  real(c_double) :: g_ep(31), g_rp(31)
  real(c_double) :: g_dp(31, 52)

  ! Electron data (stored in log-space)
  real(c_double) :: g_er(81), g_re(81)
  real(c_double) :: g_ee(11)
  real(c_double) :: g_de(11, 42, 2)

  ! Bremsstrahlung data (stored in log-space)
  real(c_double) :: g_zb(61)
  real(c_double) :: g_eb(11)
  real(c_double) :: g_db(11, 61, 2)

  logical :: g_loaded = .false.
end module shieldose_data


module shieldose_cshim
  use, intrinsic :: iso_c_binding, only: c_int, c_float, c_double, c_char, c_null_char
  use shieldose_data
  implicit none

contains

  ! =====================================================================
  ! Load data from Python-parsed arrays.
  ! =====================================================================
  subroutine shieldose_set_data( &
      mpmax, lpmax, kmax, memax, lemax, mbmax, lbmax, &
      ep_in, rp_in, dp_in, &
      er_in, re_in, ee_in, de_in, &
      zb_in, eb_in, db_in) &
      bind(C, name="shieldose_set_data")

    integer(c_int), value, intent(in) :: mpmax, lpmax, kmax
    integer(c_int), value, intent(in) :: memax, lemax, mbmax, lbmax
    real(c_double), intent(in) :: ep_in(mpmax), rp_in(mpmax), dp_in(lpmax, mpmax)
    real(c_double), intent(in) :: er_in(kmax), re_in(kmax)
    real(c_double), intent(in) :: ee_in(memax), de_in(lemax, 2, memax)
    real(c_double), intent(in) :: zb_in(lbmax), eb_in(mbmax)
    real(c_double), intent(in) :: db_in(lbmax, 2, mbmax)

    integer :: m, i, n

    g_mpmax = mpmax
    g_lpmax = lpmax
    g_kmax = kmax
    g_memax = memax
    g_lemax = lemax
    g_mbmax = mbmax
    g_lbmax = lbmax

    ! Store proton data (already in log-space from Python)
    do m = 1, mpmax
      g_ep(m) = ep_in(m)
      g_rp(m) = rp_in(m)
      do i = 1, lpmax
        g_dp(m, i) = dp_in(i, m)
      end do
    end do
    ! Initialize padding for spline extrapolation
    g_ep(mpmax + 1) = g_ep(mpmax) + 1.0d0
    g_rp(mpmax + 1) = g_rp(mpmax)

    ! Store electron data
    do i = 1, kmax
      g_er(i) = er_in(i)
      g_re(i) = re_in(i)
    end do
    g_er(kmax + 1) = g_er(kmax) + 1.0d0
    g_re(kmax + 1) = g_re(kmax)
    do m = 1, memax
      g_ee(m) = ee_in(m)
      do n = 1, 2
        do i = 1, lemax
          g_de(m, i, n) = de_in(i, n, m)
        end do
      end do
    end do
    g_ee(memax + 1) = g_ee(memax) + 1.0d0

    ! Store bremsstrahlung data
    do i = 1, lbmax
      g_zb(i) = zb_in(i)
    end do
    g_zb(lbmax + 1) = g_zb(lbmax) + 1.0d0
    do m = 1, mbmax
      g_eb(m) = eb_in(m)
      do n = 1, 2
        do i = 1, lbmax
          g_db(m, i, n) = db_in(i, n, m)
        end do
      end do
    end do
    g_eb(mbmax + 1) = g_eb(mbmax) + 1.0d0

    g_loaded = .true.
  end subroutine shieldose_set_data


  ! =====================================================================
  ! Compute dose for given depths, detector, and spectra.
  ! =====================================================================
  subroutine shieldose_calc_dose( &
      depths, ndepth, idet, iunt, &
      solar_energies, solar_flux, nsolar, &
      prot_energies, prot_flux, nprot, &
      elec_energies, elec_flux, nelec, &
      eunit, tinter, &
      dose_slab, dose_semi, dose_sphere) &
      bind(C, name="shieldose_calc_dose")

    real(c_float), intent(in)    :: depths(*)
    integer(c_int), value, intent(in) :: ndepth
    integer(c_int), value, intent(in) :: idet, iunt
    real(c_float), intent(in)    :: solar_energies(*), solar_flux(*)
    integer(c_int), value, intent(in) :: nsolar
    real(c_float), intent(in)    :: prot_energies(*), prot_flux(*)
    integer(c_int), value, intent(in) :: nprot
    real(c_float), intent(in)    :: elec_energies(*), elec_flux(*)
    integer(c_int), value, intent(in) :: nelec
    real(c_float), value, intent(in) :: eunit, tinter
    real(c_float), intent(out)   :: dose_slab(ndepth, 5)
    real(c_float), intent(out)   :: dose_semi(ndepth, 5)
    real(c_float), intent(out)   :: dose_sphere(ndepth, 5)

    real(c_double) :: z(50), zl(50)
    integer :: imax, i, j, n, np, ne
    integer :: isol, itrp, ilec
    integer :: nptsp, nptse
    integer :: nfsts, nlsts, nlens, nfstp, nlstp, nlenp
    real(c_double) :: zcon, zmcon, radcon
    real(c_double) :: emins, emaxs, eminp, emaxp, emine, emaxe
    real(c_double) :: eminu, emaxu, dep, dele
    real(c_double) :: eminul, eminel, dee, deple
    real(c_double) :: eunit_d, tinter_d
    real(c_double) :: deltas, deltap, deltae
    real(c_double) :: zp(51), ze(41)

    ! Working arrays
    real(c_double) :: tpl(301), tp(301), rinp(301)
    real(c_double) :: tel(101), te(101), rine(101)
    real(c_double) :: sol(301), spg(301), seg(101)
    real(c_double) :: eps(101), s(101), g(301)
    real(c_double) :: din(60, 301), gp(301, 50)
    real(c_double) :: ge(101, 50, 2), gb(101, 50, 2)
    real(c_double) :: dosol(50, 2), dosp(50, 2)
    real(c_double) :: dose(50, 2, 2), dosb(50, 2, 2)
    real(c_double) :: ans

    if (.not. g_loaded) then
      dose_slab = 0.0
      dose_semi = 0.0
      dose_sphere = 0.0
      return
    end if

    imax = min(ndepth, 50)

    ! Unit conversions
    zcon = 0.001d0 * 2.540005d0 * 2.70d0
    zmcon = 10.0d0 / 2.70d0
    radcon = 1.6021892d-08

    ! Convert depths to g/cm2
    do i = 1, imax
      select case (iunt)
      case (1)
        z(i) = zcon * real(depths(i), c_double)
      case (3)
        z(i) = real(depths(i), c_double) / zmcon
      case default
        z(i) = real(depths(i), c_double)
      end select
      zl(i) = log(z(i))
    end do

    ! Energy unit and time interval
    eunit_d = real(eunit, c_double)
    tinter_d = real(tinter, c_double)
    if (eunit_d <= 0.0d0) eunit_d = 1.0d0
    if (tinter_d <= 0.0d0) tinter_d = 1.0d0

    ! Default energy grid parameters
    nptsp = 151
    nptse = 101
    eminp = 0.1d0
    emaxp = 400.0d0
    emine = 0.01d0
    emaxe = 10.0d0
    emins = 1.0d0
    emaxs = 100.0d0

    ! Proton depth fractions
    do i = 1, g_lpmax
      zp(i) = dble(i - 1) / dble(g_lpmax - 1)
    end do

    ! Electron depth fractions
    do i = 1, g_lemax
      ze(i) = dble(i - 1) / dble(g_lemax - 1)
    end do

    ! Energy grid setup
    eminu = min(eminp, emins)
    emaxu = max(emaxp, emaxs)
    dep = log(emaxu / eminu) / dble(nptsp - 1)
    nfsts = nint(log(emins / eminu) / dep) + 1
    nlsts = nint(log(emaxs / eminu) / dep) + 1
    nlens = nlsts - nfsts + 1
    nfstp = nint(log(eminp / eminu) / dep) + 1
    nlstp = nint(log(emaxp / eminu) / dep) + 1
    nlenp = nlstp - nfstp + 1
    eminul = log(eminu)
    deple = dep / 3.0d0

    ! Proton energy grid and range interpolation
    do np = 1, nptsp
      tpl(np) = eminul + dble(np - 1) * dep
      tp(np) = exp(tpl(np))
      call spol(tpl(np), g_ep, g_rp, g_mpmax, ans)
      rinp(np) = exp(ans)
    end do

    ! Interpolate proton dose data onto energy grid
    do i = 1, g_lpmax
      do np = 1, nptsp
        if (tpl(np) >= g_ep(g_mpmax)) then
          din(i, np) = g_dp(g_mpmax, i)
        else if (tpl(np) <= g_ep(1)) then
          din(i, np) = g_dp(1, i)
        else
          call spol(tpl(np), g_ep, g_dp(1, i), g_mpmax, din(i, np))
        end if
      end do
    end do

    ! Proton dose-response function
    do np = 1, nptsp
      do i = 1, imax
        if (z(i) / rinp(np) >= 1.0d0) then
          gp(np, i) = 0.0d0
        else
          call spol(z(i) / rinp(np), zp, din(1, np), g_lpmax, ans)
          if (ans < 0.0d0) then
            gp(np, i) = 0.0d0
          else
            gp(np, i) = tp(np) * ans / rinp(np)
          end if
        end if
      end do
    end do

    ! Electron energy grid
    eminel = log(emine)
    dee = (log(emaxe) - eminel) / dble(nptse - 1)
    dele = dee / 3.0d0

    do ne = 1, nptse
      tel(ne) = eminel + dble(ne - 1) * dee
      te(ne) = exp(tel(ne))
      call spol(tel(ne), g_er, g_re, g_kmax, ans)
      rine(ne) = exp(ans)
    end do

    ! Electron and bremsstrahlung dose-response functions
    do n = 1, 2
      ! Electron dose
      do i = 1, g_lemax
        do ne = 1, nptse
          if (tel(ne) >= g_ee(g_memax)) then
            din(i, ne) = g_de(g_memax, i, n)
          else if (tel(ne) <= g_ee(1)) then
            din(i, ne) = g_de(1, i, n)
          else
            call spol(tel(ne), g_ee, g_de(1, i, n), g_memax, din(i, ne))
          end if
        end do
      end do
      do ne = 1, nptse
        do i = 1, imax
          if (z(i) / rine(ne) >= 1.0d0) then
            ge(ne, i, n) = 0.0d0
          else
            call spol(z(i) / rine(ne), ze, din(1, ne), g_lemax, ans)
            if (ans < 0.0d0) then
              ge(ne, i, n) = 0.0d0
            else
              ge(ne, i, n) = te(ne) * ans / rine(ne)
            end if
          end if
        end do
      end do

      ! Bremsstrahlung dose
      do i = 1, g_lbmax
        do ne = 1, nptse
          if (tel(ne) >= g_eb(g_mbmax)) then
            din(i, ne) = g_db(g_mbmax, i, n)
          else if (tel(ne) <= g_eb(1)) then
            din(i, ne) = g_db(1, i, n)
          else
            call spol(tel(ne), g_eb, g_db(1, i, n), g_mbmax, din(i, ne))
          end if
        end do
      end do
      do ne = 1, nptse
        do i = 1, imax
          call spol(log(z(i) / te(ne)), g_zb, din(1, ne), g_lbmax, ans)
          gb(ne, i, n) = te(ne) * exp(ans)
        end do
      end do
    end do

    ! Process spectra
    isol = 2
    itrp = 2
    ilec = 2

    ! Solar proton spectrum
    if (nsolar >= 3) then
      isol = 1
      do j = 1, nsolar
        eps(j) = real(solar_energies(j), c_double)
        s(j) = real(solar_flux(j), c_double)
      end do
      call spectr_proc(nsolar, eps, s, eunit_d, deple, nlens, &
                       tp(nfsts), tpl(nfsts), sol(nfsts))
    end if

    ! Trapped proton spectrum
    if (nprot >= 3) then
      itrp = 1
      do j = 1, nprot
        eps(j) = real(prot_energies(j), c_double)
        s(j) = real(prot_flux(j), c_double)
      end do
      call spectr_proc(nprot, eps, s, eunit_d, deple, nlenp, &
                       tp(nfstp), tpl(nfstp), spg(nfstp))
    end if

    ! Electron spectrum
    if (nelec >= 3) then
      ilec = 1
      do j = 1, nelec
        eps(j) = real(elec_energies(j), c_double)
        s(j) = real(elec_flux(j), c_double)
      end do
      call spectr_proc(nelec, eps, s, eunit_d, dele, nptse, te, tel, seg)
    end if

    ! Compute doses
    deltas = radcon * deple / 4.0d0
    deltap = tinter_d * radcon * deple / 4.0d0
    deltae = tinter_d * radcon * dele / 4.0d0

    ! Solar proton dose
    if (isol == 2) then
      do np = nfsts, nlsts
        sol(np) = 0.0d0
      end do
      do j = 1, 2
        do i = 1, imax
          dosol(i, j) = 0.0d0
        end do
      end do
    else
      do i = 1, imax
        do np = nfsts, nlsts
          g(np) = sol(np) * gp(np, i)
        end do
        call simpson_int(deltas, g(nfsts), nlens, dosol(i, 1))
      end do
      call sphere_conv(zl, dosol(1, 1), imax, dosol(1, 2))
    end if

    ! Trapped proton dose
    if (itrp == 2) then
      do np = nfstp, nlstp
        spg(np) = 0.0d0
      end do
      do j = 1, 2
        do i = 1, imax
          dosp(i, j) = 0.0d0
        end do
      end do
    else
      do i = 1, imax
        do np = nfstp, nlstp
          g(np) = spg(np) * gp(np, i)
        end do
        call simpson_int(deltap, g(nfstp), nlenp, dosp(i, 1))
      end do
      call sphere_conv(zl, dosp(1, 1), imax, dosp(1, 2))
    end if

    ! Electron and bremsstrahlung dose
    if (ilec == 2) then
      do j = 1, 2
        do n = 1, 2
          do i = 1, imax
            dose(i, n, j) = 0.0d0
            dosb(i, n, j) = 0.0d0
          end do
        end do
      end do
    else
      do n = 1, 2
        do i = 1, imax
          do ne = 1, nptse
            g(ne) = seg(ne) * ge(ne, i, n)
            spg(ne) = seg(ne) * gb(ne, i, n)
          end do
          call simpson_int(deltae, g, nptse, dose(i, n, 1))
          call simpson_int(deltae, spg, nptse, dosb(i, n, 1))
        end do
        if (n == 1) then
          call sphere_conv(zl, dose(1, n, 1), imax, dose(1, n, 2))
          call sphere_conv(zl, dosb(1, n, 1), imax, dosb(1, n, 2))
        end if
      end do
    end if

    ! Pack output arrays
    do i = 1, imax
      ! Slab geometry (N=1, J=1)
      dose_slab(i, 1) = real(dose(i, 1, 1), c_float)
      dose_slab(i, 2) = real(dosb(i, 1, 1), c_float)
      dose_slab(i, 3) = real(dose(i, 1, 1) + dosb(i, 1, 1), c_float)
      dose_slab(i, 4) = real(dosp(i, 1), c_float)
      dose_slab(i, 5) = real(dosol(i, 1), c_float)

      ! Semi-infinite medium (N=2, J=1)
      dose_semi(i, 1) = real(dose(i, 2, 1), c_float)
      dose_semi(i, 2) = real(dosb(i, 2, 1), c_float)
      dose_semi(i, 3) = real(dose(i, 2, 1) + dosb(i, 2, 1), c_float)
      dose_semi(i, 4) = real(dosp(i, 1), c_float)
      dose_semi(i, 5) = real(dosol(i, 1), c_float)

      ! Sphere center (N=2, J=2)
      dose_sphere(i, 1) = real(dose(i, 2, 2), c_float)
      dose_sphere(i, 2) = real(dosb(i, 2, 2), c_float)
      dose_sphere(i, 3) = real(dose(i, 2, 2) + dosb(i, 2, 2), c_float)
      dose_sphere(i, 4) = real(dosp(i, 2), c_float)
      dose_sphere(i, 5) = real(dosol(i, 2), c_float)
    end do

  end subroutine shieldose_calc_dose


  ! =====================================================================
  ! Check if data has been loaded.
  ! =====================================================================
  function shieldose_is_loaded() bind(C, name="shieldose_is_loaded") result(res)
    integer(c_int) :: res
    if (g_loaded) then
      res = 1
    else
      res = 0
    end if
  end function shieldose_is_loaded


  ! =====================================================================
  ! Internal subroutines (double precision re-implementations)
  ! =====================================================================

  !---------------------------------------------------------------------
  ! Spectrum processing.
  !---------------------------------------------------------------------
  subroutine spectr_proc(jmax, eps_in, s_in, eunit, delta, npts, t, tl, sp)
    integer, intent(in) :: jmax, npts
    real(c_double), intent(inout) :: eps_in(*), s_in(*)
    real(c_double), intent(in) :: eunit, delta, t(*), tl(*)
    real(c_double), intent(out) :: sp(*)
    real(c_double) :: eps_loc(101), s_loc(101)
    integer :: n, j

    if (eps_in(1) > 0.0d0) then
      do j = 1, jmax
        eps_loc(j) = log(eps_in(j))
        s_loc(j) = log(eunit * s_in(j))
      end do
      do n = 1, npts
        call spol(tl(n), eps_loc, s_loc, jmax, sp(n))
        sp(n) = t(n) * exp(sp(n))
      end do
    else
      block
        real(c_double) :: alpha, beta
        alpha = s_in(1)
        beta = s_in(2)
        if (beta <= 0.0d0) beta = 1.0d0
        beta = beta / alpha
        do n = 1, npts
          sp(n) = t(n) * beta * exp(-t(n) / alpha)
        end do
      end block
    end if

  end subroutine spectr_proc


  !---------------------------------------------------------------------
  ! Cubic spline interpolation with parabolic runout.
  !---------------------------------------------------------------------
  subroutine spol(s, x, y, n, t)
    real(c_double), intent(in) :: s, x(*), y(*)
    integer, intent(in) :: n
    real(c_double), intent(out) :: t
    real(c_double) :: e(301), u(301)
    real(c_double) :: b1, c1, b2, c2, b, d, c, p
    integer :: j, k, kk, n1, idir, mlb, mub, ml, mu, mav

    n1 = n - 1
    e(1) = 1.0d0
    u(1) = 0.0d0
    b1 = x(2) - x(1)
    c1 = (y(2) - y(1)) / b1

    do j = 2, n1
      b2 = x(j + 1) - x(j)
      c2 = (y(j + 1) - y(j)) / b2
      b = x(j + 1) - x(j - 1)
      d = (c2 - c1) / b
      c = b1 / b
      b1 = b2
      c1 = c2
      p = c * e(j - 1) + 2.0d0
      e(j) = (c - 1.0d0) / p
      u(j) = (d - c * u(j - 1)) / p
    end do

    e(n) = u(n1) / (1.0d0 - e(n1))
    do kk = 1, n1
      k = n - kk
      e(k) = e(k) * e(k + 1) + u(k)
    end do

    if (x(1) <= x(n)) then
      idir = 0
      mlb = 0
      mub = n
    else
      idir = 1
      mlb = n
      mub = 0
    end if

    if (s >= x(mub + idir)) then
      mu = mub + 2 * idir
    else if (s <= x(mlb + 1 - idir)) then
      mu = mlb + 2 * (1 - idir)
    else
      ml = mlb
      mu = mub
      do while (abs(mu - ml) > 1)
        mav = (ml + mu) / 2
        if (s < x(mav)) then
          mu = mav
        else
          ml = mav
        end if
      end do
      mu = mu + idir
    end if

    t = (e(mu - 1) * ((x(mu) - s)**3) + e(mu) * ((s - x(mu - 1))**3) + &
         (y(mu - 1) - e(mu - 1) * ((x(mu) - x(mu - 1))**2)) * (x(mu) - s) + &
         (y(mu) - e(mu) * ((x(mu) - x(mu - 1))**2)) * (s - x(mu - 1))) / &
        (x(mu) - x(mu - 1))

  end subroutine spol


  !---------------------------------------------------------------------
  ! Numerical integration (Simpson's rule variants).
  !---------------------------------------------------------------------
  subroutine simpson_int(delta, g, n, result)
    real(c_double), intent(in) :: delta, g(*)
    integer, intent(in) :: n
    real(c_double), intent(out) :: result
    real(c_double) :: sigma, sum4, sum2, sig6
    integer :: k, nl1, nl2

    nl1 = n - 1
    nl2 = n - 2

    if (mod(n, 2) == 1) then
      select case (n)
      case (1)
        sigma = 0.0d0
      case (3)
        sigma = g(1) + 4.0d0 * g(2) + g(3)
      case default
        sum4 = 0.0d0
        do k = 2, nl1, 2
          sum4 = sum4 + g(k)
        end do
        sum2 = 0.0d0
        do k = 3, nl2, 2
          sum2 = sum2 + g(k)
        end do
        sigma = g(1) + 4.0d0 * sum4 + 2.0d0 * sum2 + g(n)
      end select
    else
      select case (n)
      case (2)
        sigma = 1.5d0 * (g(1) + g(2))
      case (4)
        sigma = 1.125d0 * (g(1) + 3.0d0 * g(2) + 3.0d0 * g(3) + g(4))
      case (6)
        sigma = g(1) + 3.875d0 * g(2) + 2.625d0 * g(3) + &
                2.625d0 * g(4) + 3.875d0 * g(5) + g(6)
      case (8)
        sigma = g(1) + 3.875d0 * g(2) + 2.625d0 * g(3) + &
                2.625d0 * g(4) + 3.875d0 * g(5) + 2.0d0 * g(6) + &
                4.0d0 * g(7) + g(8)
      case default
        sig6 = g(1) + 3.875d0 * g(2) + 2.625d0 * g(3) + &
               2.625d0 * g(4) + 3.875d0 * g(5) + g(6)
        sum4 = 0.0d0
        do k = 7, nl1, 2
          sum4 = sum4 + g(k)
        end do
        sum2 = 0.0d0
        do k = 8, nl2, 2
          sum2 = sum2 + g(k)
        end do
        sigma = sig6 + g(6) + 4.0d0 * sum4 + 2.0d0 * sum2 + g(n)
      end select
    end if

    result = delta * sigma
  end subroutine simpson_int


  !---------------------------------------------------------------------
  ! Slab-to-sphere dose conversion.
  !---------------------------------------------------------------------
  subroutine sphere_conv(zl, dose_in, imax, dosph)
    real(c_double), intent(in) :: zl(*)
    real(c_double), intent(in) :: dose_in(*)
    integer, intent(in) :: imax
    real(c_double), intent(out) :: dosph(*)
    real(c_double) :: dosl(50), derv(50)
    integer :: i, imix, imix1

    imix = imax
    do i = 1, imax
      if (dose_in(i) <= 0.0d0) then
        imix = i - 1
        exit
      end if
      dosl(i) = log(dose_in(i))
    end do

    if (imix >= 3) then
      call spldrv(zl, dosl, derv, imix)
      do i = 1, imix
        dosph(i) = dose_in(i) * (1.0d0 - derv(i))
      end do
    end if

    imix1 = imix + 1
    if (imix1 <= imax) then
      do i = imix1, imax
        dosph(i) = 0.0d0
      end do
    end if

  end subroutine sphere_conv


  !---------------------------------------------------------------------
  ! Cubic spline derivative computation.
  !---------------------------------------------------------------------
  subroutine spldrv(x, y, u, n)
    real(c_double), intent(in) :: x(*), y(*)
    real(c_double), intent(out) :: u(*)
    integer, intent(in) :: n
    real(c_double) :: e(101), b1, c1, b2, c2, b, d, c, p
    integer :: j, k, kk, n1

    n1 = n - 1
    e(1) = 1.0d0
    u(1) = 0.0d0
    b1 = x(2) - x(1)
    c1 = (y(2) - y(1)) / b1

    do j = 2, n1
      b2 = x(j + 1) - x(j)
      c2 = (y(j + 1) - y(j)) / b2
      b = x(j + 1) - x(j - 1)
      d = (c2 - c1) / b
      c = b1 / b
      b1 = b2
      c1 = c2
      p = c * e(j - 1) + 2.0d0
      e(j) = (c - 1.0d0) / p
      u(j) = (d - c * u(j - 1)) / p
    end do

    e(n) = u(n1) / (1.0d0 - e(n1))
    do kk = 1, n1
      k = n - kk
      e(k) = e(k) * e(k + 1) + u(k)
      b2 = x(k + 1) - x(k)
      u(k) = (y(k + 1) - y(k)) / b2 - b2 * (2.0d0 * e(k) + e(k + 1))
    end do
    u(n) = (y(n) - y(n1)) / b2 + b2 * (2.0d0 * e(n) + e(n1))

  end subroutine spldrv

end module shieldose_cshim
