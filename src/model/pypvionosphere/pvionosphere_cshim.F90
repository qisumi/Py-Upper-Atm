module pvionosphere_cshim
  use, intrinsic :: iso_c_binding, only: c_float
  implicit none
contains
  subroutine pvionosphere_eval(alt, sza, density_coeff, temperature_coeff, log_density, log_temperature) &
      bind(C, name="pvionosphere_eval")
    real(c_float), value, intent(in) :: alt, sza
    real(c_float), intent(in) :: density_coeff(26), temperature_coeff(28)
    real(c_float), intent(out) :: log_density, log_temperature
    real(c_float) :: p(26), t(28), pb(4), sin2, adjusted, sinz, shape, calc
    real(c_float) :: s1, c1, s2, c2, s3, c3
    integer :: j, k
    p = density_coeff
    t = temperature_coeff
    sin2 = sin(sza)**2
    adjusted = sza * (1.0_c_float - p(23) * sin2 * &
      exp(-p(24) * sin2 - p(25) * (alt - p(26))**2))
    sinz = sin(p(18) + adjusted)
    shape = p(1) + p(2)/(alt-p(3)) + sinz*p(13) + &
      p(19)*exp(-p(20)*(alt-p(21))**2-p(22)*adjusted**2)
    calc = 1.77245_c_float * shape * erfc(-shape) + exp(-shape*shape) + &
      p(4) + p(5)/(alt-p(6)) + sinz*p(14)
    if (calc <= 0.0_c_float) calc = 1.0e-5_c_float
    log_density = p(7) + p(8)/(alt-p(9)) + sinz*p(15) + &
      (p(10) + p(11)/(alt-p(12)) + sinz*p(16)) * log(calc)

    s1=sin(sza); c1=cos(sza); s2=sin(2.0_c_float*sza)
    c2=cos(2.0_c_float*sza); s3=sin(3.0_c_float*sza); c3=cos(3.0_c_float*sza)
    do j=1,4
      k=j*7
      pb(j)=t(k-6)+t(k-5)*s1+t(k-4)*c1+t(k-3)*s2+t(k-2)*c2+t(k-1)*s3+t(k)*c3
    end do
    log_temperature=pb(1)+pb(2)/(alt+pb(3))**2+pb(4)*alt
  end subroutine pvionosphere_eval
end module pvionosphere_cshim
