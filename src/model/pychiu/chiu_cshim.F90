! chiu_cshim.F90 — C ABI shim for Chiu ionospheric electron density model
!
! Exposes: subroutine chiu_eval(indata, outdata)
!   indata(8)  : Z, RZUR, PHI, TMO, RLT, RLTM, RLGM, DIP
!   outdata(4) : QTOT, QI_E, QI_F1, QI_F2
!
! All values are single-precision floats (c_float).
! See chiu.for header for parameter descriptions.
!
module chiu_cshim
  use, intrinsic :: iso_c_binding, only: c_float
  implicit none
contains
  subroutine chiu_eval(indata, outdata) bind(C, name="chiu_eval")
    real(c_float), intent(in)  :: indata(8)
    real(c_float), intent(out) :: outdata(4)

    interface
      subroutine IONDEN(QTOT, QI, Z, RZUR, PHI, TMO, RLT, RLTM, RLGM, DIP)
        real, intent(out) :: QTOT
        real, intent(out) :: QI(3)
        real, intent(in)  :: Z, RZUR, PHI, TMO, RLT, RLTM, RLGM, DIP
      end subroutine IONDEN
    end interface

    real :: qt, qi(3)

    call IONDEN(qt, qi, indata(1), indata(2), indata(3), indata(4), &
                indata(5), indata(6), indata(7), indata(8))

    outdata(1) = qt
    outdata(2) = qi(1)
    outdata(3) = qi(2)
    outdata(4) = qi(3)
  end subroutine chiu_eval
end module chiu_cshim
