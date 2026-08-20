module pvthermosphere_cshim
  use, intrinsic :: iso_c_binding, only: c_float
  implicit none
contains
  subroutine pvthermosphere_eval(alt, lat, local_time, f107a, f107, density, temperature) &
      bind(C, name="pvthermosphere_eval")
    real(c_float), value, intent(in) :: alt, lat, local_time, f107a, f107
    real(c_float), intent(out) :: density(7), temperature(2)
    real :: d(7), t(2), z, latitude, hour, average_flux, daily_flux
    integer :: mass
    z=alt; latitude=lat; hour=local_time; average_flux=f107a; daily_flux=f107; mass=48
    call VTS3(z, 0.0, latitude, hour, average_flux, daily_flux, mass, d, t)
    density=real(d, kind=c_float)
    temperature=real(t, kind=c_float)
  end subroutine pvthermosphere_eval
end module pvthermosphere_cshim
