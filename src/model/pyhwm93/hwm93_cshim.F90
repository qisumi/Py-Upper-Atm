! cshim.F90 — C ABI shim for HWM93 so it can be called from Python (ctypes)
!
! Exposes: void hwm93_eval(int iyd, float sec, float alt, float glat, float glon,
!                          float stl, float f107a, float f107,
!                          const float ap[2], float w_out[2])
!
! Types are 32‑bit to match the original hwm93.f (integer(4), real(4)).
!
module hwm93_cshim
  use, intrinsic :: iso_c_binding, only: c_int, c_float
  implicit none
contains
  subroutine hwm93_eval(iyd,sec,alt,glat,glon,stl,f107a,f107,ap,w_out) bind(C, name="hwm93_eval")
    ! C‑callable wrapper with a stable symbol name.
    integer(c_int),  value      :: iyd
    real(c_float),   value      :: sec,alt,glat,glon,stl,f107a,f107
    real(c_float),   intent(in) :: ap(2)
    real(c_float),   intent(out):: w_out(2)
    
    ! 声明HWM93的GWS5子例程接口
    interface
      subroutine GWS5(IYD,SEC,ALT,GLAT,GLONG,STL,F107A,F107,AP,W)
        integer, intent(in) :: IYD
        real, intent(in) :: SEC,ALT,GLAT,GLONG,STL,F107A,F107
        real, intent(in) :: AP(2)
        real, intent(OUT) :: W(2)
      end subroutine GWS5
    end interface

    ! 调用HWM93的主函数
    call GWS5(iyd,sec,alt,glat,glon,stl,f107a,f107,ap,w_out)
  end subroutine hwm93_eval
end module hwm93_cshim