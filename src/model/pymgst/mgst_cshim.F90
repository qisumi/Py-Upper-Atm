! mgst_cshim.F90 — C ABI shim for MGST geomagnetic field models
!
!  Exposes:
!    void mgst_set_data_root(const char *path)
!    void mgst_eval(int version, float dlat, float dlong, float alt,
!                   float tm, int nmx, float *x, float *y, float *z, float *f)
!
!  Wraps the FIELDG subroutine for use via ctypes / C callers.
!  Field components are in nT.
!
!  version = 80 for MGST(6/80), version = 81 for MGST(4/81)
!
module mgst_cshim
  use, intrinsic :: iso_c_binding, only: c_int, c_float, c_char, c_null_char
  implicit none

  character(len=256) :: mgst_data_root = ''

contains

  ! ------------------------------------------------------------------
  ! Set the directory containing MGST coefficient .dat files.
  ! Called once during Model.__init__.
  ! ------------------------------------------------------------------
  subroutine mgst_set_data_root(path) bind(C, name="mgst_set_data_root")
    character(kind=c_char), intent(in) :: path(*)
    integer :: i

    mgst_data_root = ''
    do i = 1, len(mgst_data_root)
      if (path(i) == c_null_char) exit
      mgst_data_root(i:i) = achar(iachar(path(i)))
    enddo
  end subroutine

  ! ------------------------------------------------------------------
  ! Compute geomagnetic field components at one point.
  !
  ! Inputs (all pass-by-value):
  !   version — 80 for MGST(6/80), 81 for MGST(4/81)
  !   dlat    — geodetic latitude in degrees (north positive)
  !   dlong   — geodetic longitude in degrees (east positive)
  !   alt     — altitude in km above sea level
  !   tm      — decimal year (e.g. 1979.85)
  !   nmx     — maximum degree and order (default 13)
  !
  ! Outputs (all pass-by-reference):
  !   x — north component of B (nT)
  !   y — east  component of B (nT)
  !   z — down  component of B (nT, positive downward)
  !   f — total field strength |B| (nT)
  ! ------------------------------------------------------------------
  subroutine mgst_eval(version, dlat, dlong, alt, tm, nmx, &
                       x, y, z, f) bind(C, name="mgst_eval")
    integer(c_int), value, intent(in) :: version
    real(c_float),  value, intent(in) :: dlat, dlong, alt, tm
    integer(c_int), value, intent(in) :: nmx
    real(c_float),         intent(out) :: x, y, z, f

    character(len=512) :: coeff_file
    character(len=512) :: line
    character(len=512) :: stripped
    integer :: ios
    integer :: l_flag
    integer :: src_unit

    interface
      subroutine FIELDG(DLAT, DLONG, ALT, TM, NMX, L, X, Y, Z, F)
        real, intent(in)    :: DLAT, DLONG, ALT, TM
        integer, intent(in) :: NMX
        integer, intent(inout) :: L
        real, intent(out)   :: X, Y, Z, F
      end subroutine FIELDG
    end interface

    ! Select coefficient file based on version
    if (version == 80) then
      coeff_file = trim(mgst_data_root) // '/mgst380.dat'
    else
      coeff_file = trim(mgst_data_root) // '/mgst481.dat'
    endif

    ! FIELDG expects a strict file layout: one header line followed directly
    ! by fixed-width coefficient rows. Some archived MGST files include an
    ! extra prose metadata line, so copy only FIELDG-readable lines to a
    ! scratch unit and let the original routine read from unit 2.
    src_unit = 20
    open(unit=src_unit, file=trim(coeff_file), status='old', iostat=ios)
    if (ios /= 0) then
      x = 0.0
      y = 0.0
      z = 0.0
      f = 0.0
      return
    endif
    open(unit=2, status='scratch', action='readwrite', iostat=ios)
    if (ios /= 0) then
      close(unit=src_unit)
      x = 0.0
      y = 0.0
      z = 0.0
      f = 0.0
      return
    endif

    read(src_unit, '(A)', iostat=ios) line
    if (ios /= 0) then
      close(unit=src_unit)
      close(unit=2)
      x = 0.0
      y = 0.0
      z = 0.0
      f = 0.0
      return
    endif
    write(2, '(A)') trim(line)

    do
      read(src_unit, '(A)', iostat=ios) line
      if (ios /= 0) exit
      stripped = adjustl(line)
      if (len_trim(stripped) == 0) exit
      if (stripped(1:1) >= '0' .and. stripped(1:1) <= '9') then
        write(2, '(A)') trim(line)
      endif
    enddo
    write(2, '(A)') ''
    close(unit=src_unit)
    rewind(unit=2)

    ! Open unit 3 for diagnostic output (FIELDG writes to unit 3)
    open(unit=3, status='scratch', iostat=ios)

    ! L=1 tells FIELDG to read coefficients from unit 2
    l_flag = 1

    ! Call FIELDG to compute field components
    call FIELDG(dlat, dlong, alt, tm, nmx, l_flag, x, y, z, f)

    ! Close units
    close(unit=2)
    close(unit=3)

  end subroutine

end module mgst_cshim
