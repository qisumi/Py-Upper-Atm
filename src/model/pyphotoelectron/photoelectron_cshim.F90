module photoelectron_cshim
  use, intrinsic :: iso_c_binding, only: c_float, c_int
  implicit none
contains
  subroutine photoelectron_eval(alt, sza, te, tn, oxygen, oxygen2, nitrogen2, electrons, &
      n2d, op2d, f107, use_f107, euv_input, flux, attenuation) bind(C, name="photoelectron_eval")
    real(c_float), value, intent(in) :: alt, sza, te, tn, oxygen, oxygen2, nitrogen2
    real(c_float), value, intent(in) :: electrons, n2d, op2d, f107
    integer(c_int), value, intent(in) :: use_f107
    real(c_float), intent(in) :: euv_input(9)
    real(c_float), intent(out) :: flux(100), attenuation
    real :: xn(3), euv(9), uvfac(59), peflux(100), afac
    real :: z, angle, electron_temperature, neutral_temperature
    real :: electron_density, n2d_density, op2d_density, radio_flux
    z=alt; angle=sza; electron_temperature=te; neutral_temperature=tn
    xn=[real(oxygen), real(oxygen2), real(nitrogen2)]
    electron_density=electrons; n2d_density=n2d; op2d_density=op2d
    euv=real(euv_input); radio_flux=f107
    if (use_f107 /= 0) then
      call FACEUV(radio_flux, uvfac)
      euv=uvfac(1:9)
    end if
    call FLXCAL(z, angle, electron_temperature, neutral_temperature, euv, xn, &
      electron_density, n2d_density, op2d_density, peflux, afac)
    flux=real(peflux, kind=c_float)
    attenuation=real(afac, kind=c_float)
  end subroutine photoelectron_eval
end module photoelectron_cshim
