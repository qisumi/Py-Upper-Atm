! jensen_cshim.F90 — C ABI shim for Jensen & Cain geomagnetic field model
!
!  Exposes:
!    void jensen_set_data_root(const char *path)
!    void jensen_eval(float dlat, float dlong, float alt, float tm,
!                     int nmx, float *x, float *y, float *z, float *f)
!
!  Wraps the FIELDG subroutine for use via ctypes / C callers.
!  Field components are in nT.
!
module jensen_cshim
  use, intrinsic :: iso_c_binding, only: c_int, c_float, c_char, c_null_char
  implicit none

  character(len=256) :: jensen_data_root = ''

contains

  ! ------------------------------------------------------------------
  ! Set the directory containing Jensen-Cain coefficient .dat files.
  ! Called once during Model.__init__.
  ! ------------------------------------------------------------------
  subroutine jensen_set_data_root(path) bind(C, name="jensen_set_data_root")
    character(kind=c_char), intent(in) :: path(*)
    integer :: i

    jensen_data_root = ''
    do i = 1, len(jensen_data_root)
      if (path(i) == c_null_char) exit
      jensen_data_root(i:i) = achar(iachar(path(i)))
    enddo
  end subroutine

  ! ------------------------------------------------------------------
  ! Compute geomagnetic field components at one point.
  !
  ! Inputs (all pass-by-value):
  !   dlat  — geodetic latitude in degrees (north positive)
  !   dlong — geodetic longitude in degrees (east positive)
  !   alt   — altitude in km above sea level
  !   tm    — decimal year (e.g. 1960.0)
  !   nmx   — maximum degree and order (default 6)
  !
  ! Outputs (all pass-by-reference):
  !   x — north component of B (nT)
  !   y — east  component of B (nT)
  !   z — down  component of B (nT, positive downward)
  !   f — total field strength |B| (nT)
  ! ------------------------------------------------------------------
  subroutine jensen_eval(dlat, dlong, alt, tm, nmx, &
                         x, y, z, f) bind(C, name="jensen_eval")
    real(c_float), value, intent(in)  :: dlat, dlong, alt, tm
    integer(c_int), value, intent(in) :: nmx
    real(c_float),        intent(out) :: x, y, z, f

    character(len=512) :: coeff_file
    integer :: ios
    integer :: l_flag

    interface
      subroutine FIELDG(DLAT, DLONG, ALT, TM, NMX, L, X, Y, Z, F)
        real, intent(in)    :: DLAT, DLONG, ALT, TM
        integer, intent(in) :: NMX
        integer, intent(inout) :: L
        real, intent(out)   :: X, Y, Z, F
      end subroutine FIELDG
    end interface

    ! Build full path to coefficient file
    coeff_file = trim(jensen_data_root) // '/jensen_cain_62.dat'

    ! Open unit 2 for coefficient file (FIELDG reads from unit 2)
    open(unit=2, file=trim(coeff_file), status='old', iostat=ios)
    if (ios /= 0) then
      x = 0.0
      y = 0.0
      z = 0.0
      f = 0.0
      return
    endif

    ! Open unit 3 for diagnostic output (FIELDG writes to unit 3).
    ! A scratch file is portable across Linux and Windows CI.
    open(unit=3, status='scratch', iostat=ios)

    ! L=1 tells FIELDG to read coefficients from unit 2
    l_flag = 1

    ! Call FIELDG to compute field components
    call FIELDG(dlat, dlong, alt, tm, nmx, l_flag, x, y, z, f)

    ! Close units
    close(unit=2)
    close(unit=3)

  end subroutine

end module jensen_cshim
