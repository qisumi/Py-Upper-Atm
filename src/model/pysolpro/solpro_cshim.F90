! solpro_cshim.F90 — C ABI shim for SOLPRO solar proton fluence model
!
! Exposes: subroutine solpro_eval(tau, iq, f, inale)
!   tau    (c_float, value, in)  — mission duration in months
!   iq     (c_int,   value, in)  — confidence level in percent
!   f(10)  (c_float, out)        — integral fluence for E = 10,20,...,100 MeV
!   inale  (c_int,   out)        — number of Anomalously Large events
!
module solpro_cshim
  use, intrinsic :: iso_c_binding, only: c_float, c_int
  implicit none
contains
  subroutine solpro_eval(tau, iq, f, inale) bind(C, name="solpro_eval")
    real(c_float), value, intent(in)  :: tau
    integer(c_int), value, intent(in)  :: iq
    real(c_float), intent(out) :: f(10)
    integer(c_int), intent(out) :: inale

    interface
      subroutine SOLPRO(TAU, IQ, F, INALE)
        real :: TAU, F(10)
        integer :: IQ, INALE
      end subroutine
    end interface

    call SOLPRO(tau, iq, f, inale)
  end subroutine solpro_eval
end module solpro_cshim
