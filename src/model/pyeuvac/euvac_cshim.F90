module euvac_cshim
  use, intrinsic :: iso_c_binding, only: c_float
  implicit none
contains
  subroutine euvac_eval(f107, f107a, flux) bind(C, name="euvac_eval")
    real(c_float), value, intent(in) :: f107, f107a
    real(c_float), intent(out) :: flux(37)
    real(c_float), parameter :: reference(37) = [ &
      1.20,0.450,4.800,3.100,0.460,0.210,1.679,0.8,6.900,0.965, &
      0.650,0.314,0.383,0.290,0.285,0.452,0.720,1.270,0.357,0.530, &
      1.590,0.342,0.230,0.360,0.141,0.170,0.260,0.702,0.758,1.625, &
      3.537,3.000,4.400,1.475,3.500,2.100,2.467 ]
    real(c_float), parameter :: scale(37) = [ &
      1.0017e-2,7.1250e-3,1.3375e-2,1.9450e-2,2.7750e-3,1.3768e-1, &
      2.6467e-2,2.5000e-2,3.3333e-3,2.2450e-2,6.5917e-3,3.6542e-2, &
      7.4083e-3,7.4917e-3,2.0225e-2,8.7583e-3,3.2667e-3,5.1583e-3, &
      3.6583e-3,1.6175e-2,3.3250e-3,1.1800e-2,4.2667e-3,3.0417e-3, &
      4.7500e-3,3.8500e-3,1.2808e-2,3.2750e-3,4.7667e-3,4.8167e-3, &
      5.6750e-3,4.9833e-3,3.9417e-3,4.4167e-3,5.1833e-3,5.2833e-3, &
      4.3750e-3 ]
    real(c_float) :: factor
    integer :: i
    do i = 1, 37
      factor = max(0.8_c_float, 1.0_c_float + scale(i) * &
        (0.5_c_float * (f107 + f107a) - 80.0_c_float))
      flux(i) = reference(i) * factor * 1.0e9_c_float
    end do
  end subroutine euvac_eval
end module euvac_cshim
