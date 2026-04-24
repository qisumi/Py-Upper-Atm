! msis_cshim.F90 — C ABI wrapper aligned to your internal signature
module msis_cshim
  use, intrinsic :: iso_c_binding
  use msis_calc, only: msiscalc          ! 直接 use 你提供的过程
  implicit none
contains
  ! C 原型：
  ! void msiscalc(float day, float utsec, float z_km,
  !               float lat_deg, float lon_deg,
  !               float f107a, float f107,
  !               const float ap7[7],
  !               float* t_local, float dn10[10], float* t_exo);
  subroutine msiscalc_c(day, utsec, z, lat, lon, sfluxavg, sflux, ap7, &
                        t_local, dn10, t_exo) bind(C, name="msiscalc")
    use iso_c_binding, only: c_float
    implicit none
    real(c_float),  value :: day, utsec, z, lat, lon, sfluxavg, sflux
    real(c_float), intent(in)  :: ap7(7)
    real(c_float), intent(out) :: t_local
    real(c_float), intent(out) :: dn10(10)
    real(c_float), intent(out) :: t_exo

    ! 你的内部过程参数顺序：day,utsec,z,lat,lon,sfluxavg,sflux,ap(1:7),tn,dn(1:10),[tex]
    call msiscalc(day, utsec, z, lat, lon, sfluxavg, sflux, ap7, t_local, dn10, t_exo)
  end subroutine msiscalc_c
end module msis_cshim
