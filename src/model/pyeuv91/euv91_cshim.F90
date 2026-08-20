module euv91_cshim
  use, intrinsic :: iso_c_binding, only: c_float
  implicit none
contains
  subroutine euv91_eval(coeff, proxy, wavelength, photon, energy) bind(C, name="euv91_eval")
    real(c_float), intent(in) :: coeff(12,52), proxy(4), wavelength(39)
    real(c_float), intent(out) :: photon(39), energy(39)
    real(c_float) :: s(4), modeled(52), total, weight, exponent
    integer :: i, j
    s = proxy
    if (s(1) < 1.0e-5_c_float .and. s(2) > 1.0e-5_c_float) s(1) = s(2)
    if (s(1) < 1.0e-5_c_float) s(1) = 8.7e8_c_float * s(3) + 1.9e11_c_float
    if (s(2) < 1.0e-5_c_float) s(2) = s(1)
    do j = 1, 52
      total = 0.0_c_float
      weight = 1.0_c_float
      do i = 1, 4
        if (i <= 2) then
          exponent = max(-88.0_c_float, -s(i) * 1.0e-10_c_float)
        else
          exponent = max(-88.0_c_float, -s(i) * 0.7_c_float)
        end if
        weight = weight * (1.0_c_float + coeff(8+i,j) * exp(exponent))
        total = total + coeff(i+4,j) * s(i)
      end do
      modeled(j) = (coeff(4,j) + total) * weight
    end do
    photon = 0.0_c_float
    photon(1)=modeled(1); photon(2)=modeled(2)+modeled(3); photon(3)=modeled(4)+modeled(5)
    photon(4)=modeled(6)+modeled(7); photon(5)=modeled(8)+modeled(9); photon(6)=modeled(10)+modeled(11)
    photon(7)=modeled(12); photon(8)=modeled(13); photon(9)=modeled(14)+modeled(15); photon(10)=modeled(16)
    photon(11)=modeled(17); photon(12)=modeled(18); photon(13)=modeled(19); photon(14)=modeled(20)+modeled(21)
    photon(15)=modeled(22)+modeled(23); photon(16)=modeled(24); photon(17)=modeled(25)+modeled(26)
    photon(18)=modeled(27)+modeled(28); photon(19)=modeled(29); photon(20)=modeled(30); photon(21)=modeled(31)
    photon(22)=modeled(32); photon(23)=modeled(33); photon(24)=modeled(34)+modeled(35)
    photon(25)=modeled(36)+modeled(37); photon(26)=modeled(38); photon(27)=modeled(39); photon(28)=modeled(40)
    photon(29)=modeled(41); photon(30)=modeled(42); photon(31)=modeled(43)+modeled(44); photon(32)=modeled(45)
    photon(33)=modeled(46); photon(34)=modeled(47); photon(35)=modeled(48); photon(36)=modeled(49)
    photon(37)=modeled(50); photon(38)=modeled(51); photon(39)=modeled(52)
    do i = 1, 39
      energy(i) = photon(i) * (12400.0_c_float * 1.6022e-12_c_float) / wavelength(i)
    end do
  end subroutine euv91_eval
end module euv91_cshim
