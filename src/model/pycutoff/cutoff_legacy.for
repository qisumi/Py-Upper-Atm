      SUBROUTINE GDGC (TCD, TSD)
C
C........+.........+.........+.........+.........+.........+.........+..
C     \/ Convert from Geodetic to Geocentric coordinates
C        Adopted from NASA ALLMAG
C         GDLATD = Geodetic   latitude (in degrees)
C         GCLATD = Geocentric latitude (in degrees)
C         GDCLT  = Geodetic co-latitude
C         ERPLSQ is earth radius AT poles   squared = 40408585 (km sq)
C         EREQSQ is earth radius AT equator squared = 40680925 (km sq)
C         ERADPR is earth polar      radius = 6356.774733 (km)
C         ERADER is earth equatorial radius = 6378.160001 (km)
C         ERAD   is earth average    radius = 6371.25     (km)
C         ERADFL is flattening factor = 1.0/298.25
C         ERADFL =  (ERADEQ - factor)/ERADEQ
C         ERECSQ is eccentricity squared = 0.00673966
C         ERECSQ =  EREQSQ/ERPLSQ - 1.0
C........+.........+.........+.........+.........+.........+.........+..
C
CLast Mod 15 Jan 97  Common block SNGLR & SNGLI
C     Mod    Feb 96  Standard reference TJ1V line check
C
C........+.........+.........+.........+.........+.........+.........+..
C     Programmer - Don F. Smart; FORTRAN77
C     Note - The programming adheres to the conventional FORTRAN
C            default standard that variables beginning with
C            'i','j','k','l','m',or 'n' are integer variables
C            Variables beginning with "c" are character variables
C            All other variables are real
C........+........+.........+.........+.........+.........+.........+..
C            Do not mix different type variables in same common block
C            Some computers do not allow this
C........+.........+.........+.........+.........+.........+.........+..
C
      IMPLICIT INTEGER (I-N)
      IMPLICIT REAL * 8(A-B)
      IMPLICIT REAL * 8(D-H)
      IMPLICIT REAL * 8(O-Z)
C
C........+.........+.........+.........+.........+.........+.........+..
C
      COMMON /WRKVLU/ F(6),Y(6),ERAD,EOMC,VEL,BR,BT,BP,B
      COMMON /WRKTSC/ TSY2,TCY2,TSY3,TCY3
      COMMON /TRIG/   PI,RAD,PIO2
      COMMON /GEOID/  ERADPL, ERECSQ
      COMMON /SNGLR/  SALT,DISOUT,GCLATD,GDLATD,GLOND,GDAZD,GDZED,
     *                RY1,RY2,RY3,RHT,TSTEP,PATH
C
C........+.........+.........+.........+.........+.........+.........+..
C
      ERPLSQ = 40408585.0
      EREQSQ = 40680925.0
      ERADPL = SQRT(ERPLSQ)
      ERECSQ = EREQSQ/ERPLSQ - 1.0
C
      GDCLT = PIO2-GDLATD/RAD
      TSGDCLT = SIN(GDCLT)
      TCGDCLT = COS(GDCLT)
      ONE = EREQSQ*TSGDCLT*TSGDCLT
      TWO = ERPLSQ*TCGDCLT*TCGDCLT
      THREE = ONE+TWO
      RHO = SQRT(THREE)
C
C........+.........+.........+.........+.........+.........+.........+..
C     \/ Get geocentric distance from geocenter in kilometers
C........+.........+.........+.........+.........+.........+.........+..
C
      DISTKM = SQRT(SALT*(SALT+2.0*RHO)+(EREQSQ*ONE+ERPLSQ*TWO)/THREE)
C
C........+.........+.........+.........+.........+.........+.........+..
C     TCD and TSD are sine and cosine of the angle the Geodetic vertical
C         must be rotated to form the Geocentric vertical
C........+.........+.........+.........+.........+.........+.........+..
C
      TCD = (SALT+RHO)/DISTKM
      TSD = (EREQSQ-ERPLSQ)/RHO*TCGDCLT*TSGDCLT/DISTKM
      TCY2 = TCGDCLT*TCD-TSGDCLT*TSD
      TSY2 = TSGDCLT*TCD+TCGDCLT*TSD
C
      Y(2) = ACOS(TCY2)
      Y(3) = GLOND/RAD
      Y(1) = DISTKM/ERAD
C
      GCLATD = (PIO2-Y(2))*RAD
C
C     WRITE (*,1200) GDLATD,GDCLT,TSGDCLT,TCGDCLT,ONE,TWO,THREE,RHO
C1200 FORMAT (' 1200',8F15.5)
C     WRITE (*,1200) DISTKM,TCD,TSD,TCY2,TSY2,GCLATD
C
      RETURN
      END
      SUBROUTINE SINGLTJ (PC,IRSLT,INDXPC,Y1GC,Y2GC,Y3GC)
C
C........+.........+.........+.........+.........+.........+.........+..
C     Cosmic-ray trajectory calculations subroutine
C                calculates cosmic ray trajectory at rigidity  PC
C........+.........+.........+.........+.........+.........+.........+..
C        PC     = rigidity in GV
C        IRSLT  = trajectory result
C        INDXPC = index of rigidity in mv (integer)
C                 Y1GC,Y2GC,Y3GC are initial geocentric coorinates
C........+.........+.........+.........+.........+.........+.........+..
C     \/ Step size optimization & look ahead for potential BETA problems
C             monitor accelerating terms and reduce step length
C                     if large increase occurs
C        Restart at smaller step size if BETA error occurs
C........+.........+.........+.........+.........+.........+.........+..
C     Restrictions: Cannot run over N or S pole; will get BETA blowup
C........+.........+.........+.........+.........+.........+.........+..
CLast Mod 17 Feb 99  if (ymax.lt.6.6) IFATE = 3
C     Mod 18 Jan 97  Patch high latitude beta problem
C     Mod    Jan 97  High latitude step size adjust, introduce AHLT
C     Mod    Jun 96  EDIF limit set to 1.0e-5
C     Mod    Jun 96  IERRPT formats, Boundary and look ahead
C     Mod    FEB 96  standard reference TJ1V (line check 17 Feb)

C........+.........+.........+.........+.........+.........+.........+..
C     Programmer - Don F. Smart; FORTRAN77
C     Note - The programming adheres to the conventional FORTRAN
C            default standard that variables beginning with
C            'i','j','k','l','m',or 'n' are integer variables
C            Variables beginning with "c" are character variables
C            All other variables are real
C........+........+.........+.........+.........+.........+.........+..
C            Do not mix different type variables in same common block
C            Some computers do not allow this
C........+.........+.........+.........+.........+.........+.........+..
C
      IMPLICIT INTEGER (I-N)
      IMPLICIT REAL * 8(A-B)
      IMPLICIT REAL * 8(D-H)
      IMPLICIT REAL * 8(O-Z)
C
C........+.........+.........+.........+.........+.........+.........+..
C
      COMMON /WRKVLU/ F(6),Y(6),ERAD,EOMC,VEL,BR,BT,BP,B
      COMMON /WRKTSC/ TSY2,TCY2,TSY3,TCY3
      COMMON /TRIG/   PI,RAD,PIO2
      COMMON /GEOID/  ERADPL, ERECSQ
      COMMON /SNGLR/  SALT,DISOUT,GCLATD,GDLATD,GLOND,GDAZD,GDZED,
     *                RY1,RY2,RY3,RHT,TSTEP,PATH
      COMMON /SNGLI/  LIMIT,NTRAJC,IERRPT
C
C........+.........+.........+.........+.........+.........+.........+..
C
      DIMENSION P(6),Q(6),R(6),S(6),YB(6),FOLD(6),YOLD(6)
C
C........+.........+.........+.........+.........+.........+.........+..
C
      CHARACTER*1 CF,CR
      CHARACTER*6 CNAME
C
      DATA CF,CR / 'F','R'/
      DATA CNAME / '  I95 '/                                            ###
C
C........+.........+.........+.........+.........+.........+.........+..
C
      IF (IERRPT.GT.0) WRITE (16,2000) PC,INDXPC,RY1,RY2,RY3
 2000 FORMAT (' SINGLTJ ',F8.3,I8,3F8.4)
C
      BETAST = 2.0
      LSTEP = 0
      KBF = 0
C
C........+.........+.........+.........+.........+.........+.........+..
C     \/ Runge-Kutta constants
C........+.........+.........+.........+.........+.........+.........+..
C
      RC1O6 = 1.0/6.0
      SR2 = SQRT(2.0)
      TMS2O2 = (2.0-SR2)/2.0
      TPS2O2 = (2.0+SR2)/2.0
C
C........+.........+.........+.........+.........+.........+.........+..
C     \/ Initialize Runge-Kutta variables to zero
C........+.........+.........+.........+.........+.........+.........+..
C
  100 DO 110 I = 1, 6
         YB(I) = 0.0
         S(I) = 0.0
         R(I) = 0.0
         Q(I) = 0.0
         P(I) = 0.0
         F(I) = 0.0
  110 CONTINUE
C
      NMAX = 0
      NMIN = 0
      NSTEP = 0
      NSTEPT = 0
C
      TAU = 0.0
      TU100 = 0.0
      YMAX = RY1
C
C........+.........+.........+.........+.........+.........+.........+..
C     \/ Define initial point at start of trajectory
C........+.........+.........+.........+.........+.........+.........+..
C
      TSY2SQ = SIN(Y(2))**2
      Y(1) = RY1
      Y(2) = RY2
      Y(3) = RY3
      GRNDKM = (ERADPL/SQRT(1.0-ERECSQ*TSY2SQ))
      Y10 = (RHT+GRNDKM)/ERAD
      R120KM = (ERAD+120.0)/ERAD
C
C........+.........+.........+.........+.........+.........+.........+..
C     Rigidity = momentum/charge
C                use oxygen 16 as reference isotope
C     Constants used from Handbook of Physics (7-170)
C                         1 amu = 0.931141  GeV
C........+.........+.........+.........+.........+.........+.........+..
C
      ANUC = 16.0
      ZCHARGE = 8.0
C
      EMCSQ = 0.931141
      TENG = SQRT((PC*ZCHARGE)**2+(ANUC*EMCSQ)**2)
      EOMC = -8987.566297*ZCHARGE/TENG
      GMA = SQRT(((PC*ZCHARGE)/(EMCSQ*ANUC))**2+1.0)
      BETA = SQRT(1.0-1.0/(GMA*GMA))
      PVEL = VEL*BETA
      HMAX = 1.0/PVEL
      disck = disout - 1.1*hmax*pvel
C
C........+.........+.........+.........+.........+.........+.........+..
C     \/ Set max step length ("HMAX") to 1 earth radii
C        PVEL  is particle velocity in earth radii per second
C        DISCK is check for approaching termination boundary
C                 (within 1.1 steps)
C........+.........+.........+.........+.........+.........+.........+..
C
      EDIF = BETA*1.0E-4
      if (edif.lt.1.0-5)  edif = 1.0e-5
      if (beta.lt.0.1)    edif = 1.0e-4
C
      Y(4) = BETA*Y1GC
      Y(5) = BETA*Y2GC
      Y(6) = BETA*Y3GC
C
       azd = gdazd
       zed = gdzed
      IAZ = AZD+0.01
      IZE = ZED+0.01
C
C........+.........+.........+.........+.........+.........+.........+..
C     \/ Set HSTART to about 1 % of the time to complete one gyro-radius
C                            in a 1 Gauss field
C        H = [(2.0*PI*33.333*PC)/(BETA*C)]/0.01
C            if restart after BETA error, set HCK to small value
C        Introduce   AHLT  to control step size at high lat (beta problem)
C                    HCK   - reduce step size when large acceleration
C                    HOLD  - last step size used
C                    HCNG  - only allow 20% max growth in step size
C                    HSNEK - attempt to approach boundary quickly
C        Problem at z=90 at high lat
C                add zen angle in deg to reduce first step
C........+.........+.........+.........+.........+.........+.........+..
C
      PTCY2 = ABS(TCY2)
      AHLT = (1.0 + PTCY2)**2
      HSTART = 6.0E-6*PC/(BETA*AHLT + ZED*PTCY2)
      IF (HSTART.LT.1.0E-6) HSTART = 1.0E-6
      HOLD = HSTART
      HCK  = HSTART
      HCNG = HSTART
C
C     WRITE (16, 2010)  HMAX,HOLD,HCK,HCNG,Y(4),Y(5),Y(6),PVEL, NSTEP
C2010 FORMAT (' 2010 ',18X, 4F9.6, 3F9.4, F9.4,9X,15X,I6)
C
C........+.........+.........+.........+.........+.........+.........+..
C     Start Runge-Kutta
C      \/\/\/\/\/\/\/\/
C        \/\/\/\/\/\/
C          \/\/\/\/
C            \/\/
C             \/
C........+.........+.........+.........+.........+.........+.........+..
C     Change in step size criteria, Aug 97
C            remove cos VxB step size, causes problems in tight loops
C            step size is now only a function of B and BETA
C........+.........+.........+.........+.........+.........+.........+..
C
  130 IF (HCK.LT.1.0E-6) HCK = 1.0E-6
      CALL FGRAD
      HB = 1.6E-5*PC/(B*BETA)
      H = HB/BETAST
C
      IF (KBF.GT.0)  H=H/(FLOAT(KBF*2))
      IF (H.GT.HMAX) H = HMAX
      IF (H.GT.HCNG) H = HCNG
      IF (H.GT.HCK)  H = HCK
C
      DO 140 I = 1, 6
         S(I) = H*F(I)
         P(I) = 0.5*S(I)-Q(I)
         YB(I) = Y(I)
         Y(I) = Y(I)+P(I)
         R(I) = Y(I)-YB(I)
         Q(I) = Q(I)+3.0*R(I)-0.5*S(I)
  140 CONTINUE
C
      CALL FGRAD
C
      DO 150 I = 1, 6
         S(I) = H*F(I)
         P(I) = TMS2O2*(S(I)-Q(I))
         YB(I) = Y(I)
         Y(I) = Y(I)+P(I)
         R(I) = Y(I)-YB(I)
         Q(I) = Q(I)+3.0*R(I)-TMS2O2*S(I)
  150 CONTINUE
C
      CALL FGRAD
C
      DO 160 I = 1, 6
         S(I) = H*F(I)
         P(I) = TPS2O2*(S(I)-Q(I))
         YB(I) = Y(I)
         Y(I) = Y(I)+P(I)
         R(I) = Y(I)-YB(I)
         Q(I) = Q(I)+3.0*R(I)-TPS2O2*S(I)
  160 CONTINUE
C
      CALL FGRAD
C
      DO 170 I = 1, 6
         S(I) = H*F(I)
         P(I) = RC1O6*(S(I)-2.0*Q(I))
         YB(I) = Y(I)
         Y(I) = Y(I)+P(I)
         R(I) = Y(I)-YB(I)
         Q(I) = Q(I)+3.0*R(I)-0.5*S(I)
  170 CONTINUE
C
C........+.........+.........+.........+.........+.........+.........+..
C             /\
C            /\/\
C          /\/\/\/\
C        /\/\/\/\/\/\
C      /\/\/\/\/\/\/\/\
c      One Runge-Kutta
c      step completed
C........+.........+.........+.........+.........+.........+.........+..
C
      NSTEP = NSTEP+1
      NSTEPT = NSTEPT + 1
      TAU = TAU+H
      HOLD = H
      HCNG = H*1.2
      HCK  = HCNG
C
C........+.........+.........+.........+.........+.........+.........+..
C     \/ Emergency diagnostic printout if desired
C........+.........+.........+.........+.........+.........+.........+..
C     WRITE (16, 2030)     H,  Y(1),Y(2),Y(3),   PVEL,B, NSTEP
C     WRITE (16, 2040)  HB,H,HMAX,HOLD,HCK,HCNG,Y(4),Y(5),Y(6),
C    *                  PVEL,B,NSTEP
C2030 FORMAT (' 2030 ',  9X,    F9.6, 36X,    3F9.5,F9.4,F9.5,18X,I6)
C2040 FORMAT (' 2040 ',        6F9.6,         3F9.5,F9.4,F9.5,18X,I6)
C
C........+.........+.........+.........+.........+.........+.........+..
C     \/ Check for altitude less than 100 km
C        if less than 120 km, compute exact altitude above oblate earth
C           and sum time trajectory is below 100 km altitude.
C        set re-entrant altitude at  RHT  km above oblate earth
C               computed from international reference ellipsoid
C     ...+.........+.........+.........+.........+.........+.........+..
C
      IF (Y(1).LT.R120KM) THEN
         TSY2SQ = SIN(Y(2))**2
         GRNDKM = (ERADPL/SQRT(1.0-ERECSQ*TSY2SQ))
         R100KM = (100.0+GRNDKM)/ERAD
         R120KM = (120.0+GRNDKM)/ERAD
         IF (Y(1).LT.R100KM) TU100 = TU100+H
         PSALT = Y(1)*ERAD-GRNDKM
         Y10 = (RHT+GRNDKM)/ERAD
C
         IF (NSTEP.GT.5)  THEN
            IF (Y(1).LT.Y10.OR.PSALT.LE.0.0) THEN
               IF (IERRPT.GT.2)  WRITE (16, 2045) PSALT, Y(1), Y10
               IRT = -1
               GO TO 260
            ENDIF
         ENDIF
      ENDIF
 2045 FORMAT (' 2045 PSALT,Y(1),Y10',F10.6,1PE14.6,E14.6)
C
C........+.........+.........+.........+.........+.........+.........+..
C     \/ Begin error checks
C        (1) Check for unacceptable changes in BETA
C........+.........+.........+.........+.........+.........+.........+..
C
      RCKBETA = SQRT(Y(4)*Y(4)+Y(5)*Y(5)+Y(6)*Y(6))
      TBETA = BETA-RCKBETA
      IF (ABS(TBETA).GT.EDIF) THEN
         KBF = KBF+1
         BETAST = BETAST + AHLT
         EDIF = 2.0*EDIF
         IF (RCKBETA.GT.(1.0+EDIF)) THEN
             BETAST = BETAST+FLOAT(KBF)*(1.0+AHLT)
             WRITE (*,2050) KBF,BETA,RCKBETA
             WRITE (*,2060) Y,H,PC,NSTEP
             WRITE (16,2050) KBF,BETA,RCKBETA
             WRITE (16,2060) Y,H,PC,NSTEP
         ENDIF
C
         WRITE (16,2070)  PC,BETA,KBF,RCKBETA,NSTEP,TBETA,Y,H
         WRITE ( *,2070)  PC,BETA,KBF,RCKBETA,NSTEP,TBETA,Y,H
C
C        +.........+.........+.........+.........+.........+.........+..
C        \/ Check for irrecoverable beta error
C           if KBF > 4, set fate to failed and start next rigidity
C        +.........+.........+.........+.........+.........+.........+..
C
         IF (KBF.lt.5) THEN
            GO TO 100
         ELSE
            IRT = 0
            PATH = -PVEL*TAU
            ISALT = SALT+0.0001
            WRITE (*,2080)
            GO TO 280
         ENDIF
      ENDIF
C
 2050 FORMAT (' 2050 ','KBF=',i5,5x,' error, the velocity of the ',
     *   'particle (BETA) has exceeded the velocity of light'/
     *   '          BETA at start of trajectory was ',F10.7/
     *   '          BETA now equals                 ',F10.7/
     *   '          reduce step size and try again    ')
 2060 FORMAT (' 2060 ','Y,H,PC,NSTEP=',8F12.6,I10)
 2070 FORMAT (' 2070 ','ERROR, Particle BETA changed;',
     *        ' PC = ',F10.6,' GV'/
     *     6x,' Beta at start was ',F10.7,17X,'KBF=',I6/
     *     6x,' Beta new equals   ',F10.7,10X,'step number',I6/
     *     6x,' Beta difference   ',F10.7/
     *     6x,' step length reduced and trajectory recalculated '/,
     *     6x,'Y=',6F12.6,6X,' H=',F15.7)
 2080    FORMAT (' 2080 ','Irrecoverable BETA error problem'/6x,
     *      ' Set fate to Failed & make path length negative'/6x,
     *      ' Terminate this trajectory & continue with program')
C
C     ...+.........+.........+.........+.........+.........+.........+..
C     \/ Continue status checks
C       (2) Compute composite acceleration
C     ...+.........+.........+.........+.........+.........+.........+..
C
      ACCER = SQRT(F(4)*F(4)+F(5)*F(5)+F(6)*F(6))
C
      IF (IERRPT.GT.3) WRITE (16,2090) Y, F, ACCER, H, NSTEP
 2090 FORMAT (' Y,F,A,H ',f7.4,5f7.3,1x,1pe8.1,5e8.1,1x,e8.1, e9.2,I6)
C
C     ...+.........+.........+.........+.........+.........+.........+..
C     \/ Continue status checks, make adjustment latitude dependant
C        (3) Monitor change in composite acceleration
C            If composite acceleration (new-old) change > 5
C            If composite acceleration (new/old) ratio  > 2
C               change step size to a smaller value
C    ....+.........+.........+.........+.........+.........+.........+..
C
      IF (NSTEP.GE.2) THEN
         IF (ACCER.GT.ACCOLD) THEN
            DELACC = ACCER-ACCOLD
            IF (DELACC.GT.5.0)  THEN
               HCK = HCK/(1.0+AHLT)
               IF (IERRPT.GT.2) WRITE (16,2100)
     *                          H,HCK,y(1),DELACC,PC,NSTEP
               RFA = ACCER/ACCOLD
               IF (RFA.GT.2.0) THEN
                  HCK = HCK/(1.0+AHLT)
                  IF (IERRPT.GT.2) WRITE (16,2110)
     *                             H,HCK,Y(1),RFA,PC,NSTEP
               ENDIF
            ENDIF
         ENDIF
C
 2100    FORMAT (' 2100 ','H-REDUCE',2x,'H=',F8.6,2x,'HCK=',F8.6,2x,
     *    'Y(1)=',f7.4,2X,'DELACC=',F6.2,4X,'PC=',F8.3,4x,'NSTEP=',I8)
 2110    FORMAT (' 2110 ','H-REDUCE',2x,'H=',F8.6,2x,'HCK=',F8.6,2x,
     *    'Y(1)=',f7.4,4X,' RFA=',F6.2,4X,'PC=',F8.3,4x,'NSTEP=',I8)
C
C     ...+.........+.........+.........+.........+.........+.........+..
C     \/ Continue status checks, make adjustment latitude dependant
C        (4) Monitor change in acceleration components
C            If change in any acceleration component is more than
C               a factor of 3, reduce step length
C     ...+.........+.........+.........+.........+.........+.........+..
C
         DO 200 ICK = 4, 6
            AFOLD = ABS(FOLD(ICK))
            IF (AFOLD.GT.3.0) THEN
               RFCK = ABS(F(ICK)/AFOLD)
               IF (RFCK.GT.3.0) THEN
                  HCK = HCK/(1.0+AHLT)
                  IF (IERRPT.GT.2)  THEN
                      WRITE (16,2120)  H,HCK,Y(1),NMAX,ICK,F(ICK),
     &                       ICK,FOLD(ICK),PC,NSTEP
                  ENDIF
               ENDIF
            ENDIF
  200    CONTINUE
      ENDIF
C
 2120 FORMAT (' 2120 ','H-reduce',2X,'H=',F8.6,2X,'HCK=',F8.6,2X,
     *        'Y(1)=',F7.4,2X,'NAMX=',I4,2X,'F(',I1,')=',F6.2,2X,
     *        'FOLD(',I1,')=',F6.2,2X,'PC=',F6.3,2X,'NSTEP=',I6)
C
      ACCOLD = ACCER
C
C........+.........+.........+.........+.........+.........+.........+..
C     /\ Error checks complete
C
C     \/ Find if a max or a min has occurred
C........+.........+.........+.........+.........+.........+.........+..
C
      IF (NSTEP.GT.1) THEN
         IF (YOLD(4).LE.0.0.AND.Y(4).GT.0.0) NMIN = NMIN+1
         IF (YOLD(4).GE.0.0.AND.Y(4).LT.0.0) NMAX = NMAX+1
      ENDIF
C
      IF (Y(1).GT.YMAX) YMAX = Y(1)
C
C........+.........+.........+.........+.........+.........+.........+..
C     \/ Check for termination conditions
C         Allowed    - radial distance exceeded disout
C         Failed     - number of steps exceeded
C         Re-entrant - trajectory is below "top" of atmosphere
C
C     ...+.........+.........+.........+.........+.........+.........+..
C     \/ (1) Check for step limit exceeded
C     ...+.........+.........+.........+.........+.........+.........+..
C
      IF (NSTEP.GE.LIMIT) THEN
         IRT = 0
         GO TO 260
      ENDIF
C
C     ...+.........+.........+.........+.........+.........+.........+..
C     \/  (2) Check if y(1) within 1.1 max step lengths of disout.
C                   if so, reduce step size and
C                          approach boundary at smaller step
C     ...+.........+.........+.........+.........+.........+.........+..
C
      IF (Y(1).GT.DISCK) THEN
         DISTR = ABS(DISOUT - Y(1))
         HSNEK = DISTR/PVEL
         HCNG = HCNG/2.0
         HCK  = HCK/2.0
         IF (HSNEK .LT. HCNG)  HCNG = HSNEK
         IF (HSNEK .LT. HCK)   HCK  = HSNEK
         DISCK = DISOUT - DISTR/2.0
         IF (DISCK.GE.DISOUT)  THEN
            DISCK = 24.999
             GO TO  210
         ENDIF
         IF (H.LT.1.0E-5 .OR. HCK.LT.1.0E-5 .OR. HCNG.LT.1.0E-5)  THEN
            H    = 1.0E-5
            HCK  = 1.0E-5
            HCNG = 1.0E-5
         ENDIF
C
         IF (IERRPT.GT.3) WRITE (16,2130) Y(1),DISCK,PVEL,H,HSNEK,NSTEP
C
  210    IF (Y(1).GT.DISOUT) THEN
            IF (H.LE.1.0E-5)  THEN
               IRT = 1
               GO TO 260
            ENDIF
            TAU = TAU - H
            DO 220 I = 1, 6
               Y(I) = YOLD(I)
               F(I) = FOLD(I)
  220       CONTINUE
         endif
         GO TO 130
      ENDIF
 2130 FORMAT (' 2130 ',2X,'Y(1),DISCK,PVEL,H,HSNEK',
     *        4X,1PE12.6,4X,E12.6,4X,E12.6,4X,2E9.2,22X,I6)
C
C     +.........+.........+.........+.........+.........+.........+..
c     \/ Have penetrated boundary if you are here.
c          if large step size, go back one step and
c             reduce step length (and adjust "TAU")
C     +.........+.........+.........+.........+.........+.........+..
C
  230    IF (Y(1).GT.DISOUT) THEN
C
         IF (IERRPT.GT.3)  WRITE (16, 2140) y(1),disck,pvel,H,nstep
C
         if (h.lt.1.0e-5 .or. hck.lt.1.0e-5 .or. hcng.lt.1.0e-5)  then
            IRT = 1
            go to 260
         else
            hck  = hck/2.0
            hcng = hcng/2.0
            TAU = TAU - H
            DO 240 I = 1, 6
               Y(I) = YOLD(I)
               F(I) = FOLD(I)
  240       CONTINUE
            GO TO 130
         ENDIF
      ENDIF
C
 2140 FORMAT (' 2140 ',2x,'y(1),disck,pvel,H',
     *        4x,1pe12.6,4x,e12.6,4x,e12.6,4x,e9.2,27x,i6)
C
C........+.........+.........+.........+.........+.........+.........+..
C     \/ Store values of  Y  and  F  as  FOLD & YOLD
C........+.........+.........+.........+.........+.........+.........+..
C
      DO 250 I = 1, 6
         YOLD(I) = Y(I)
         FOLD(I) = F(I)
  250 CONTINUE
C
      GO TO 130
C
C........+.........+.........+.........+.........+.........+.........+..
C*********************************************************************
C        **********          **********          **********
C                  **********          **********
C                           **********
C                 TRAJECTORY COMPLETE IF YOU ARE HERE
C........+.........+.........+.........+.........+.........+.........+..
C
  260 CONTINUE
C
      IF (Y(1).GE.DISOUT)  IRT = 1
      PATH  = PVEL*TAU
      ISALT = SALT+0.0001
      LSTEP = BETAST - 1.9
C
C........+.........+.........+.........+.........+.........+.........+..
C     \/ Write out results
C        IRT     +1     ALLOWED          (FATE = 0)
C        IRT      0     FAILED           (FATE = 2)
C        IRT     -1     RE-ENTRANT       (FATE = 1)
C........+.........+.........+.........+.........+.........+.........+..
C
      IF (IRT.GT.0) THEN
         TCY2 = COS(Y(2))
         TSY2 = SIN(Y(2))
         YDA5 = Y(5)*TCY2+Y(4)*TSY2
         ATRG1 = Y(4)*TCY2-Y(5)*TSY2
         ATRG2 = SQRT(Y(6)*Y(6)+YDA5*YDA5)
         FASLAT = 0.0
         IF (ATRG1.NE.0.0.AND.ATRG2.NE.0.0) FASLAT =
     *                                      ATAN2(ATRG1,ATRG2)*RAD
         FASLON = Y(3)*RAD
         IF (Y(6).NE.0.0.AND.YDA5.NE.0.0) FASLON = (Y(3)+ATAN2(Y(6),
     *                                    YDA5))*RAD
         IF (FASLON.LT.0.0)    FASLON = FASLON+360.0
         IF (FASLON.GT.360.0)  FASLON = FASLON-360.0
C
         WRITE (8,2150) GDLATD,GCLATD,GLOND,IZE,IAZ,PC,FASLAT,FASLON,
     *                  PATH,NMAX,NSTEP,TU100,YMAX,LSTEP,SALT,CNAME
C
         IFATE = 0
         WRITE (7,2160) GDLATD,GLOND,PC,ZED,AZD,ISALT,FASLAT,FASLON,
     *                  NSTEP,IFATE,CNAME
      ENDIF
 2150 FORMAT (2F7.2,F9.2,I5,I4,F10.3,2F8.2,F11.5,I4,I7,F9.5,F9.4,
     *        I4,F11.1,1X,A6,13X)
 2160 FORMAT (F7.2,F8.2,F9.3,2F6.1,I7,F7.2,F8.2,I7,3X,I3,3X,A6)
C
      IF (IRT.LT.0) THEN
         RENLAT = (PIO2-Y(2))*RAD
         RENLON = Y(3)*RAD
C
         WRITE (8,2170) GDLATD,GCLATD,GLOND,IZE,IAZ,PC,CR,CR,PATH,NMAX
     *      ,NSTEP,TU100,YMAX,LSTEP,SALT,CNAME,RENLAT,RENLON
C
         IFATE = 1
         WRITE (7,2180) GDLATD,GLOND,PC,ZED,AZD,ISALT,NSTEP,IFATE,CNAME
      ENDIF
 2170 FORMAT (2F7.2,F9.2,I5,I4,F10.3,5X,A1,2X,5X,A1,2X,F11.5,I4,I7,
     *        F9.5,F9.4,I4,F11.1,1X,A6,F6.1,F7.1)
 2180 FORMAT (F7.2,F8.2,F9.3,2F6.1,I7,4X,'R',7X,'R',I9,3X,I3,3X,A6)
C
  280 IF (IRT.EQ.0) THEN
C
         WRITE (8,2190) GDLATD,GCLATD,GLOND,IZE,IAZ,PC,CF,CF,PATH,
     *                  NMAX,NSTEP,TU100,YMAX,LSTEP,SALT,CNAME
C
         IFATE = 2
         IF (YMAX.LT.6.6) IFATE = 3
         WRITE (7,2200) GDLATD,GLOND,PC,ZED,AZD,ISALT,NSTEP,IFATE,CNAME
      ENDIF
 2190 FORMAT (2F7.2,F9.2,I5,I4,F10.3,5X,A1,2X,5X,A1,2X,F11.5,I4,I7,
     *        F9.5,F9.5,I4,F11.1,1X,A6,13X)
 2200 FORMAT (F7.2,F8.2,F9.3,2F6.1,I7,4X,'F',7X,'F',I9,3X,I3,3X,A6)
C
      NTRAJC = NTRAJC+1
      TSTEP = TSTEP+FLOAT(NSTEP)
C
C     ...+.........+.........+.........+.........+.........+.........+..
C     \/ Comment out to reduce IO
C     ...+.........+.........+.........+.........+.........+.........+..
C
C     WRITE (*,2210) PC, ZED, AZD, NSTEP, IFATE
C2210 FORMAT (1H+, 22X, 3F7.2,7x,2I6)
C
      IRSLT = IRT
      RETURN
      END
      SUBROUTINE FGRAD
C
C........+.........+.........+.........+.........+.........+.........+..
C     Mod    Feb 96  standard reference TJ1V (line check 17 Feb)
C     Mod 27 Jan 1999  Change MAGNEW to NEWMAG95                        ###
C........+.........+.........+.........+.........+.........+.........+..
C     Programmer   -  Don F. Smart; FORTRAN77
C     Note -  The programming adheres to the conventional FORTRAN
C             default standard that variables beginning with
C            'i','j','k','l','m',or 'n' are integer variables
C             Variables beginning with "c" are character variables
C             All other variables are real
C........+.........+.........+.........+.........+.........+.........+..
C        Do not mix different type variables in same common block
C           Some computers do not allow this
C........+.........+.........+.........+.........+.........+.........+..
C
      IMPLICIT INTEGER (I-N)
      IMPLICIT REAL * 8(A-B)
      IMPLICIT REAL * 8(D-H)
      IMPLICIT REAL * 8(O-Z)
C
C........+.........+.........+.........+.........+.........+.........+..
C
      COMMON /WRKVLU/ F(6),Y(6),ERAD,EOMC,VEL,BR,BT,BP,B
      COMMON /WRKTSC/ TSY2,TCY2,TSY3,TCY3
C
C........+.........+.........+.........+.........+.........+.........+..
C
      F(1) = VEL*Y(4)
      F(2) = VEL*Y(5)/Y(1)
      TSY2 = SIN(Y(2))
      TCY2 = COS(Y(2))
      F(3) = VEL*Y(6)/(Y(1)*TSY2)
      SQY6 = Y(6)*Y(6)/Y(1)
      Y5OY1 = Y(5)/Y(1)
      TAY2 = TSY2/TCY2
      CALL MAGNEW95                                                     ###
      F(4) = EOMC*(Y(5)*BP-Y(6)*BT)+VEL*(Y(5)*Y5OY1+SQY6)
      F(5) = EOMC*(Y(6)*BR-Y(4)*BP)+VEL*(SQY6/TAY2-Y5OY1*Y(4))
      F(6) = EOMC*(Y(4)*BT-Y(5)*BR)-VEL*((Y5OY1*Y(6))/TAY2+Y(4)*Y(6)/
     *       Y(1))
      RETURN
C
C........+.........+.........+.........+.........+.........+.........+..
C     Y(1) is R coordinate         Y(2) is THETA coordinate
C     Y(3) is PHI coordinate       Y(4) is V(R)
C     Y(5) is V(THETA)             Y(6) is V(PHI)
C     F(1) is R dot                F(2) is THETA dot
C     F(3) is PHI dot              F(4) is R dot dot
C     F(5) is THETA dot dot        F(6) is PHI dot dot
C     BR   is B(R)                 BT   is B(THETA)
C     BP   is B(PHI)               B    is magnitude of magnetic field
C........+.........+.........+.........+.........+.........+.........+..
C
      END
      SUBROUTINE MAGNEW95                                               ###
C
C........+.........+.........+.........+.........+.........+.........+..
C     Compute Magnetic field
C     Derived from NASA (NSSDC) routine NEWMAG version of December 1965
C             modified for 10 order field
C     Coefficients for IGRF 1995 loaded into this subroutine            ###
C     Coefficients obtained from program CNGMAGN
C........+.........+.........+.........+.........+.........+.........+..
CLast Mod 27 Jan 1999  IGRF 95 coefficients                             ###
C     Mod    Feb 1996  standard reference TJ1V (line check 17 Feb)
C     Mod    Nov 1980  for arguments in labeled common
C........+.........+.........+.........+.........+.........+.........+..
C........+.........+.........+.........+.........+.........+.........+..
C     Programmer - Don F. Smart; FORTRAN77
C     Note - The programming adheres to the conventional FORTRAN
C            default standard that variables beginning with
C            'i','j','k','l','m',or 'n' are integer variables
C            Variables beginning with "c" are character variables
C            All other variables are real
C........+........+.........+.........+.........+.........+.........+..
C            Do not mix different type variables in same common block
C            Some computers do not allow this
C........+.........+.........+.........+.........+.........+.........+..
C
      IMPLICIT INTEGER (I-N)
      IMPLICIT REAL * 8(A-B)
      IMPLICIT REAL * 8(D-H)
      IMPLICIT REAL * 8(O-Z)
C
C........+.........+.........+.........+.........+.........+.........+..
C
      COMMON /WRKVLU/ F(6),Y(6),ERAD,EOMC,VEL,BR,BT,BP,B
      COMMON /WRKTSC/ TSY2,TCY2,TSY3,TCY3
C
C........+.........+.........+.........+.........+.........+.........+..
C
      DIMENSION     G(11,11),BM(11)
C
C........+.........+.........+.........+.........+.........+.........+..
C
C     \/ Load in data constants if this is the first time called
C        otherwise, skip to evaluation of magnetic field
C          designed to drop high order terms if contribution
C                   would be less then "BERR"
C           also designed so the maximum order of expansion
C               can be specified
C........+.........+.........+.........+.........+.........+.........+..
C
      IF (JDATA.EQ.77) GO TO 120
C
C........+.........+.........+.........+.........+.........+.........+..
C     Gauss normalized Schmidt coefficients ordered for fast computation
C
Cards for FORTRAN
C     1995.00     Coef in CNGMAG format                             IGRF95
      DATA(G(N, 1),N=1,11)/   0.000000E+00
     c,   0.296820E+05,   0.329550E+04,  -0.332250E+04,  -0.411687E+04
     c,   0.165375E+04,  -0.952875E+03,  -0.209137E+04,  -0.120656E+04
     c,  -0.379844E+03,
     c   0.541277E+03/
      DATA(G(N, 2),N=1,11)/  -0.531800E+04
     c,   0.178900E+04,  -0.532432E+04,   0.694430E+04,  -0.432758E+04
     c,  -0.357864E+04,  -0.120980E+04,   0.237646E+04,  -0.268125E+03
     c,  -0.114663E+04,
     c   0.973144E+03/
      DATA(G(N, 3),N=1,11)/   0.408071E+04
     c,   0.368061E+03,  -0.145925E+04,  -0.241868E+04,  -0.113872E+04
     c,  -0.182140E+04,  -0.971375E+03,  -0.289608E+02,   0.560824E+02
     c,  -0.108650E+03,
     c  -0.421384E+03/
      DATA(G(N, 4),N=1,11)/   0.805270E+03
     c,  -0.584820E+03,   0.320971E+03,  -0.607948E+03,   0.880585E+03
     c,   0.574158E+03,   0.171361E+04,  -0.593873E+03,   0.372776E+03
     c,   0.995794E+03,
     c   0.826402E+03/
      DATA(G(N, 5),N=1,11)/  -0.144990E+04
     c,   0.907844E+03,  -0.204982E+03,   0.222593E+03,  -0.857832E+02
     c,   0.370495E+03,  -0.109137E+02,  -0.493957E+02,   0.374307E+03
     c,  -0.507382E+03,
     c   0.233742E+03/
      DATA(G(N, 6),N=1,11)/  -0.447330E+03
     c,  -0.120658E+04,   0.715344E+03,   0.141986E+03,  -0.694545E+02
     c,   0.182406E+02,  -0.395558E+02,  -0.493957E+02,  -0.593223E+02
     c,   0.134764E+03,
     c  -0.295662E+03/
      DATA(G(N, 7),N=1,11)/   0.302450E+03
     c,  -0.115071E+04,  -0.667509E+03,   0.311041E+03,  -0.930726E+01
     c,  -0.188074E+02,   0.631392E+02,  -0.242182E+02,  -0.343261E+02
     c,   0.347959E+02,
     c  -0.123960E+03/
      DATA(G(N, 8),N=1,11)/   0.273116E+04
     c,   0.724020E+03,  -0.614352E+02,  -0.271676E+03,  -0.987915E+02
     c,   0.557020E+02,   0.194178E+01,   0.129452E+01,   0.000000E+00
     c,  -0.527347E+02,
     c  -0.200432E+02/
      DATA(G(N, 9),N=1,11)/  -0.804375E+03
     c,   0.112165E+04,  -0.289937E+03,   0.561461E+03,  -0.177967E+03
     c,  -0.686523E+02,   0.426161E+02,   0.626707E+01,   0.438695E+01
     c,   0.000000E+00,
     c  -0.245478E+02/
      DATA(G(N,10),N=1,11)/   0.242067E+04
     c,  -0.162975E+04,  -0.912811E+03,   0.394630E+03,   0.235837E+03
     c,  -0.156581E+03,  -0.527347E+02,   0.206718E+02,  -0.609049E+00
     c,   0.365430E+01,
     c  -0.796435E+01/
      DATA(G(N,11),N=1,11)/  -0.486572E+03
     c,  -0.210692E+03,  -0.495841E+03,  -0.701225E+03,   0.295662E+03
     c,   0.000000E+00,   0.400864E+02,  -0.245478E+02,   0.265478E+01
     c,   0.356177E+01,
     c   0.000000E+00/
      DATA JMAG/ 0/,MGNMAX/    11/,GSUM/  -0.885846E+05/
      DATA BM/   0.100078E+06
     c,   0.100078E+06,   0.396633E+05,   0.253449E+05,   0.134069E+05
     c,   0.684114E+04,   0.360156E+04,   0.197007E+04,   0.913524E+03
     c,   0.489229E+03,
     c   0.152640E+03/
C     1995.00     Coef in CNGMAG format                             IGRF95
C
C   ******************************************************************
C   *    The array G contains Gauss normalized Schmidt coefficients
c   *    the array G contains both the G and H coefficients
C   *     G(1,1) = 0.0
C   *Schmidt G(N,M) corresponds to -G(NN+1,MM+1) Gauss normalized coef
C   *Schmidt H(N,M) corresponds to -G( MI ,NN+1) Gauss normalized coef
C   *                            where MI = M
C   ******************************************************************
C
      GMSUM = 0.0
      IF (GMSUM.EQ.0) GO TO 110
      P22 = 0.
      BERR = 0.0001
      AR = 0.
      DO 100 L = 1, MGNMAX
         DO 100 M = 1, MGNMAX
            AR = AR+1.
            P22 = P22+AR*G(M,L)
  100 CONTINUE
      GMSUM = (GMSUM-P22)/GMSUM
C
C........+.........+.........+.........+.........+.........+.........+..
C**** \/ Note following print and stop statements
C........+.........+.........+.........+.........+.........+.........+..
C
      IF (ABS(GMSUM).GT.1.E-4) THEN
         WRITE (*, 2200) GMSUM
         WRITE (7, 2200) GMSUM
         WRITE (8, 2200) GMSUM
         STOP
      ENDIF
 2200 FORMAT (' DATA WRONG IN MAGNEW',E15.6)
C
  110 CONTINUE
C
      GMSUM = 0.
      JDATA = 77
C
  120 CONTINUE
      P21 = TCY2
      P22 = TSY2
      AR = 1.0/Y(1)
C
C........+.........+.........+.........+.........+.........+.........+..
C     \/ N= 2
C........+.........+.........+.........+.........+.........+.........+..
C
      DP22 = P21
      TSY3 = SIN(Y(3))
      TCY3 = COS(Y(3))
      TSP2 = TSY3
      TCP2 = TCY3
      DP21 = -P22
      AOR = AR*AR*AR
      RC2 = G(2,2)*TCP2+G(1,2)*TSP2
      BR = -(AOR+AOR)*(G(2,1)*P21+RC2*P22)
      BT = AOR*(G(2,1)*DP21+RC2*DP22)
      BP = AOR*(G(1,2)*TCP2-G(2,2)*TSP2)*P22
C
C........+.........+.........+.........+.........+.........+.........+..
C     \/ N = 3
C........+.........+.........+.........+.........+.........+.........+..
C
      IF (MGNMAX.LT.3) GO TO 130
      AOR = AOR*AR
      ERR = BERR*SQRT((BP/P22)**2+BR**2+BT**2)
      IF ((BM(3)*AOR).LT.ERR) GO TO 130
      TSP3 = (TSP2+TSP2)*TCP2
      TCP3 = (TCP2+TSP2)*(TCP2-TSP2)
      P31 = P21*P21-0.333333333
      P32 = P21*P22
      P33 = P22*P22
      DP31 = -P32-P32
      DP32 = P21*P21-P33
      DP33 = -DP31
      RC2 = G(3,2)*TCP2+G(1,3)*TSP2
      RC3 = G(3,3)*TCP3+G(2,3)*TSP3
      BR = BR-3.0*AOR*(G(3,1)*P31+RC2*P32+RC3*P33)
      BT = BT+AOR*(G(3,1)*DP31+RC2*DP32+RC3*DP33)
      BP = BP-AOR*((G(3,2)*TSP2-G(1,3)*TCP2)*P32+
     *     2.0*(G(3,3)*TSP3-G(2,3)*TCP3)*P33)
C
C........+.........+.........+.........+.........+.........+.........+..
C     \/ N = 4
C........+.........+.........+.........+.........+.........+.........+..
C
      IF (MGNMAX.LT.4) GO TO 130
      AOR = AOR*AR
      IF ((BM(4)*AOR).LT.ERR) GO TO 130
      TSP4 = TSP2*TCP3+TCP2*TSP3
      TCP4 = TCP2*TCP3-TSP2*TSP3
      P41  = P21*P31-0.26666666*P21
      DP41 = P21*DP31+DP21*P31-0.26666666*DP21
      P42  = P21*P32-0.20000000*P22
      DP42 = P21*DP32+DP21*P32-0.20000000*DP22
      P43  = P21*P33
      DP43 = P21*DP33+DP21*P33
      P44  = P22*P33
      DP44 = 3.0*P43
      RC2 = G(4,2)*TCP2+G(1,4)*TSP2
      RC3 = G(4,3)*TCP3+G(2,4)*TSP3
      RC4 = G(4,4)*TCP4+G(3,4)*TSP4
      BR = BR-4.0*AOR*(G(4,1)*P41+RC2*P42+RC3*P43+RC4*P44)
      BT = BT+AOR*(G(4,1)*DP41+RC2*DP42+RC3*DP43+RC4*DP44)
      BP = BP-AOR*((G(4,2)*TSP2-G(1,4)*TCP2)*P42+
     *     2.0*(G(4,3)*TSP3-G(2,4)*TCP3)*P43+
     *     3.0*(G(4,4)*TSP4-G(3,4)*TCP4)*P44)
C
C........+.........+.........+.........+.........+.........+.........+..
C     \/ N = 5
C........+.........+.........+.........+.........+.........+.........+..
C
      IF (MGNMAX.LT.5) GO TO 130
      AOR = AOR*AR
      IF ((BM(5)*AOR).LT.ERR) GO TO 130
      TSP5 = (TSP3+TSP3)*TCP3
      TCP5 = (TCP3+TSP3)*(TCP3-TSP3)
      P51  = P21*P41-0.25714285*P31
      DP51 = P21*DP41+DP21*P41-0.25714285*DP31
      P52  = P21*P42-0.22857142*P32
      DP52 = P21*DP42+DP21*P42-0.22857142*DP32
      P53  = P21*P43-0.14285714*P33
      DP53 = P21*DP43+DP21*P43-0.14285714*DP33
      P54  = P21*P44
      DP54 = P21*DP44+DP21*P44
      P55  = P22*P44
      DP55 = 4.0*P54
      RC2 = G(5,2)*TCP2+G(1,5)*TSP2
      RC3 = G(5,3)*TCP3+G(2,5)*TSP3
      RC4 = G(5,4)*TCP4+G(3,5)*TSP4
      RC5 = G(5,5)*TCP5+G(4,5)*TSP5
      BR = BR-5.0*AOR*(G(5,1)*P51+RC2*P52+RC3*P53+RC4*P54+RC5*P55)
      BT = BT+AOR*(G(5,1)*DP51+RC2*DP52+RC3*DP53+RC4*DP54+RC5*DP55)
      BP = BP-AOR*((G(5,2)*TSP2-G(1,5)*TCP2)*P52+2.0*(G(5,3)*TSP3-
     *     G(2,5)*TCP3)*P53+3.0*(G(5,4)*TSP4-
     *     G(3,5)*TCP4)*P54+4.0*(G(5,5)*TSP5-
     *     G(4,5)*TCP5)*P55)
C
C........+.........+.........+.........+.........+.........+.........+..
C     \/ N = 6
C........+.........+.........+.........+.........+.........+.........+..
C
      IF (MGNMAX.LT.6) GO TO 130
      AOR = AOR*AR
      IF ((BM(6)*AOR).LT.ERR) GO TO 130
      TSP6 = TSP2*TCP5+TCP2*TSP5
      TCP6 = TCP2*TCP5-TSP2*TSP5
      P61 =  P21*P51-0.25396825*P41
      DP61 = P21*DP51+DP21*P51-0.25396825*DP41
      P62 =  P21*P52-0.23809523*P42
      DP62 = P21*DP52+DP21*P52-0.23809523*DP42
      P63 =  P21*P53-0.19047619*P43
      DP63 = P21*DP53+DP21*P53-0.19047619*DP43
      P64 =  P21*P54-0.11111111*P44
      DP64 = P21*DP54+DP21*P54-0.11111111*DP44
      P65 =  P21*P55
      DP65 = P21*DP55+DP21*P55
      P66 =  P22*P55
      DP66 = 5.0*P65
      RC2 = G(6,2)*TCP2+G(1,6)*TSP2
      RC3 = G(6,3)*TCP3+G(2,6)*TSP3
      RC4 = G(6,4)*TCP4+G(3,6)*TSP4
      RC5 = G(6,5)*TCP5+G(4,6)*TSP5
      RC6 = G(6,6)*TCP6+G(5,6)*TSP6
      BR = BR-6.0*AOR*(G(6,1)*P61+RC2*P62+RC3*P63+RC4*P64+RC5*P65
     *       +RC6*P66)
      BT = BT+AOR*(G(6,1)*DP61+RC2*DP62+RC3*DP63+RC4*DP64+RC5*DP65
     *       +RC6*DP66)
      BP = BP-AOR*((G(6,2)*TSP2-G(1,6)*TCP2)*P62+2.0*(G(6,3)*TSP3
     *       -G(2,6)*TCP3)*P63+3.0*(G(6,4)*TSP4
     *       -G(3,6)*TCP4)*P64+4.0*(G(6,5)*TSP5
     *       -G(4,6)*TCP5)*P65+5.0*(G(6,6)*TSP6-G(5,6)*TCP6)*P66)
C
C........+.........+.........+.........+.........+.........+.........+..
C     \/ N = 7
C........+.........+.........+.........+.........+.........+.........+..
C
      IF (MGNMAX.LT.7) GO TO 130
      AOR = AOR*AR
      IF ((BM(7)*AOR).LT.ERR) GO TO 130
      TSP7 = (TSP4+TSP4)*TCP4
      TCP7 = (TCP4+TSP4)*(TCP4-TSP4)
      P71  = P21*P61-0.25252525*P51
      DP71 = P21*DP61+DP21*P61-0.25252525*DP51
      P72  = P21*P62-0.24242424*P52
      DP72 = P21*DP62+DP21*P62-0.24242424*DP52
      P73  = P21*P63-0.21212121*P53
      DP73 = P21*DP63+DP21*P63-0.21212121*DP53
      P74  = P21*P64-0.16161616*P54
      DP74 = P21*DP64+DP21*P64-0.16161616*DP54
      P75  = P21*P65-0.09090909*P55
      DP75 = P21*DP65+DP21*P65-0.09090909*DP55
      P76  = P21*P66
      DP76 = P21*DP66+DP21*P66
      P77  = P22*P66
      DP77 = 6.0*P76
      RC2  = G(7,2)*TCP2+G(1,7)*TSP2
      RC3 = G(7,3)*TCP3+G(2,7)*TSP3
      RC4 = G(7,4)*TCP4+G(3,7)*TSP4
      RC5 = G(7,5)*TCP5+G(4,7)*TSP5
      RC6 = G(7,6)*TCP6+G(5,7)*TSP6
      RC7 = G(7,7)*TCP7+G(6,7)*TSP7
      BR = BR-7.0*AOR*(G(7,1)*P71+RC2*P72+RC3*P73+RC4*P74+RC5*P75
     *       +RC6*P76+RC7*P77)
      BT = BT+AOR*(G(7,1)*DP71+RC2*DP72+RC3*DP73+RC4*DP74+RC5*DP75
     *       +RC6*DP76+RC7*DP77)
      BP = BP-AOR*((G(7,2)*TSP2-G(1,7)*TCP2)*P72+2.0*(G(7,3)*TSP3
     *       -G(2,7)*TCP3)*P73+3.0*(G(7,4)*TSP4
     *       -G(3,7)*TCP4)*P74+4.0*(G(7,5)*TSP5
     *       -G(4,7)*TCP5)*P75+5.0*(G(7,6)*TSP6
     *       -G(5,7)*TCP6)*P76+6.0*(G(7,7)*TSP7-G(6,7)*TCP7)*P77)
C
C........+.........+.........+.........+.........+.........+.........+..
C     \/ N = 8
C........+.........+.........+.........+.........+.........+.........+..
C
      IF (MGNMAX.LT.8) GO TO 130
      AOR = AOR*AR
      IF ((BM(8)*AOR).LT.ERR) GO TO 130
      TSP8 = TSP2*TCP7+TCP2*TSP7
      TCP8 = TCP2*TCP7-TSP2*TSP7
      P81  = P21*P71-0.25174825*P61
      DP81 = P21*DP71+DP21*P71-0.25174825*DP61
      P82  = P21*P72-0.24475524*P62
      DP82 = P21*DP72+DP21*P72-0.24475524*DP62
      P83  = P21*P73-0.22377622*P63
      DP83 = P21*DP73+DP21*P73-0.22377622*DP63
      P84  = P21*P74-0.18881118*P64
      DP84 = P21*DP74+DP21*P74-0.18881118*DP64
      P85  = P21*P75-0.13986013*P65
      DP85 = P21*DP75+DP21*P75-0.13986013*DP65
      P86  = P21*P76-0.07692307*P66
      DP86 = P21*DP76+DP21*P76-0.07692307*DP66
      P87  = P21*P77
      DP87 = P21*DP77+DP21*P77
      P88  = P22*P77
      DP88 = 7.0*P87
      RC2 = G(8,2)*TCP2+G(1,8)*TSP2
      RC3 = G(8,3)*TCP3+G(2,8)*TSP3
      RC4 = G(8,4)*TCP4+G(3,8)*TSP4
      RC5 = G(8,5)*TCP5+G(4,8)*TSP5
      RC6 = G(8,6)*TCP6+G(5,8)*TSP6
      RC7 = G(8,7)*TCP7+G(6,8)*TSP7
      RC8 = G(8,8)*TCP8+G(7,8)*TSP8
      BR = BR-8.0*AOR*(G(8,1)*P81+RC2*P82+RC3*P83+RC4*P84+RC5*P85
     *       +RC6*P86+RC7*P87+RC8*P88)
      BT = BT+AOR*(G(8,1)*DP81+RC2*DP82+RC3*DP83+RC4*DP84+RC5*DP85
     *       +RC6*DP86+RC7*DP87+RC8*DP88)
      BP = BP-AOR*((G(8,2)*TSP2-G(1,8)*TCP2)*P82
     *       +2.0*(G(8,3)*TSP3-G(2,8)*TCP3)*P83
     *       +3.0*(G(8,4)*TSP4-G(3,8)*TCP4)*P84
     *       +4.0*(G(8,5)*TSP5-G(4,8)*TCP5)*P85
     *       +5.0*(G(8,6)*TSP6-G(5,8)*TCP6)*P86
     *       +6.0*(G(8,7)*TSP7-G(6,8)*TCP7)*P87
     *       +7.0*(G(8,8)*TSP8-G(7,8)*TCP8)*P88)
C
C........+.........+.........+.........+.........+.........+.........+..
C     \/ N = 9
C........+.........+.........+.........+.........+.........+.........+..
C
      IF (MGNMAX.LT.9) GO TO 130
      AOR = AOR*AR
      IF ((BM(9)*AOR).LT.ERR) GO TO 130
      TSP9 = (TSP5+TSP5)*TCP5
      TCP9 = (TCP5+TSP5)*(TCP5-TSP5)
      P91  = P21*P81-0.25128205*P71
      DP91 = P21*DP81+DP21*P81-0.25128205*DP71
      P92  = P21*P82-0.24615384*P72
      DP92 = P21*DP82+DP21*P82-0.24615384*DP72
      P93  = P21*P83-0.23076923*P73
      DP93 = P21*DP83+DP21*P83-0.23076923*DP73
      P94  = P21*P84-0.20512820*P74
      DP94 = P21*DP84+DP21*P84-0.20512820*DP74
      P95  = P21*P85-0.16923076*P75
      DP95 = P21*DP85+DP21*P85-0.16923076*DP75
      P96  = P21*P86-0.12307692*P76
      DP96 = P21*DP86+DP21*P86-0.12307692*DP76
      P97  = P21*P87-0.06666666*P77
      DP97 = P21*DP87+DP21*P87-0.06666666*DP77
      P98  = P21*P88
      DP98 = P21*DP88+DP21*P88
      P99  = P22*P88
      DP99 = 8.0*P98
      RC2 = G(9,2)*TCP2+G(1,9)*TSP2
      RC3 = G(9,3)*TCP3+G(2,9)*TSP3
      RC4 = G(9,4)*TCP4+G(3,9)*TSP4
      RC5 = G(9,5)*TCP5+G(4,9)*TSP5
      RC6 = G(9,6)*TCP6+G(5,9)*TSP6
      RC7 = G(9,7)*TCP7+G(6,9)*TSP7
      RC8 = G(9,8)*TCP8+G(7,9)*TSP8
      RC9 = G(9,9)*TCP9+G(8,9)*TSP9
      BR = BR-9.0*AOR*(G(9,1)*P91+RC2*P92+RC3*P93+RC4*P94+RC5*P95
     *       +RC6*P96+RC7*P97+RC8*P98+RC9*P99)
      BT = BT+AOR*(G(9,1)*DP91+RC2*DP92+RC3*DP93+RC4*DP94+RC5*DP95
     *       +RC6*DP96+RC7*DP97+RC8*DP98+RC9*DP99)
      BP = BP-AOR*((G(9,2)*TSP2-G(1,9)*TCP2)*P92+2.0*(G(9,3)*TSP3
     *       -G(2,9)*TCP3)*P93+3.0*(G(9,4)*TSP4
     *       -G(3,9)*TCP4)*P94+4.0*(G(9,5)*TSP5
     *       -G(4,9)*TCP5)*P95+5.0*(G(9,6)*TSP6
     *       -G(5,9)*TCP6)*P96+6.0*(G(9,7)*TSP7
     *       -G(6,9)*TCP7)*P97+7.0*(G(9,8)*TSP8
     *       -G(7,9)*TCP8)*P98+8.0*(G(9,9)*TSP9-G(8,9)*TCP9)*P99)
C
C........+.........+.........+.........+.........+.........+.........+..
C     \/ N = 10
C........+.........+.........+.........+.........+.........+.........+..
C
      IF (MGNMAX.LT.10) GO TO 130
      AOR = AOR*AR
      IF ((BM(10)*AOR).LT.ERR) GO TO 130
      TSP10  = TSP2*TCP9+TCP2*TSP9
      TCP10  = TCP2*TCP9-TSP2*TSP9
      P101   = P21*P91-0.25098039*P81
      DP101  = P21*DP91+DP21*P91-0.25098039*DP81
      P102   = P21*P92-0.24705882*P82
      DP102  = P21*DP92+DP21*P92-0.24705882*DP82
      P103   = P21*P93-0.23529411*P83
      DP103  = P21*DP93+DP21*P93-0.23529411*DP83
      P104   = P21*P94-0.21568627*P84
      DP104  = P21*DP94+DP21*P94-0.21568627*DP84
      P105   = P21*P95-0.18823529*P85
      DP105  = P21*DP95+DP21*P95-0.18823529*DP85
      P106   = P21*P96-0.15294117*P86
      DP106  = P21*DP96+DP21*P96-0.15294117*DP86
      P107   = P21*P97-0.10980392*P87
      DP107  = P21*DP97+DP21*P97-0.10980392*DP87
      P108   = P21*P98-0.05882352*P88
      DP108  = P21*DP98+DP21*P98-0.05882352*DP88
      P109   = P21*P99
      DP109  = P21*DP99+DP21*P99
      P1010  = P22*P99
      DP1010 = 9.0*P109
      RC2 = G(10,2)*TCP2+G(1,10)*TSP2
      RC3 = G(10,3)*TCP3+G(2,10)*TSP3
      RC4 = G(10,4)*TCP4+G(3,10)*TSP4
      RC5 = G(10,5)*TCP5+G(4,10)*TSP5
      RC6 = G(10,6)*TCP6+G(5,10)*TSP6
      RC7 = G(10,7)*TCP7+G(6,10)*TSP7
      RC8 = G(10,8)*TCP8+G(7,10)*TSP8
      RC9 = G(10,9)*TCP9+G(8,10)*TSP9
      RC10 = G(10,10)*TCP10+G(9,10)*TSP10
      BR = BR-10.0*AOR*(G(10,1)*P101+RC2*P102+RC3*P103+RC4*P104
     *       +RC5*P105+RC6*P106+RC7*P107+RC8*P108+RC9*P109+RC10*P1010)
      BT = BT+AOR*(G(10,1)*DP101+RC2*DP102+RC3*DP103+RC4*DP104
     *       +RC5*DP105+RC6*DP106+RC7*DP107+RC8*DP108+RC9*DP109
     *       +RC10*DP1010)
      BP = BP-AOR*((G(10,2)*TSP2-G(1,10)*TCP2)*P102+2.0*(G(10,3)*TSP3
     *       -G(2,10)*TCP3)*P103+3.0*(G(10,4)*TSP4
     *       -G(3,10)*TCP4)*P104+4.0*(G(10,5)*TSP5
     *       -G(4,10)*TCP5)*P105+5.0*(G(10,6)*TSP6
     *       -G(5,10)*TCP6)*P106+6.0*(G(10,7)*TSP7
     *       -G(6,10)*TCP7)*P107+7.0*(G(10,8)*TSP8
     *       -G(7,10)*TCP8)*P108+8.0*(G(10,9)*TSP9
     *       -G(8,10)*TCP9)*P109+9.0*(G(10,10)*TSP10
     *       -G(9,10)*TCP10)*P1010)
C
C........+.........+.........+.........+.........+.........+.........+..
C     \/ N = 11
C........+.........+.........+.........+.........+.........+.........+..
C
      IF (MGNMAX.LT.11) GO TO 130
      AOR = AOR*AR
      IF ((BM(11)*AOR).LT.ERR) GO TO 130
      TSP11  = (TSP6+TSP6)*TCP6
      TCP11  = (TCP6+TSP6)*(TCP6-TSP6)
      P111   = P21*P101-0.25077399*P91
      DP111  = P21*DP101+DP21*P101-0.25077399*DP91
      P112   = P21*P102-0.24767801*P92
      DP112  = P21*DP102+DP21*P102-0.24767801*DP92
      P113   = P21*P103-0.23839009*P93
      DP113  = P21*DP103+DP21*P103-0.23839009*DP93
      P114   = P21*P104-0.22291021*P94
      DP114  = P21*DP104+DP21*P104-0.22291021*DP94
      P115   = P21*P105-0.20123839*P95
      DP115  = P21*DP105+DP21*P105-0.20123839*DP95
      P116   = P21*P106-0.17337461*P96
      DP116  = P21*DP106+DP21*P106-0.17337461*DP96
      P117   = P21*P107-0.13931888*P97
      DP117  = P21*DP107+DP21*P107-0.13931888*DP97
      P118   = P21*P108-0.09907120*P98
      DP118  = P21*DP108+DP21*P108-0.09907120*DP98
      P119   = P21*P109-0.05263157*P99
      DP119  = P21*DP109+DP21*P109-0.05263157*DP99
      P1110  = P21*P1010
      DP1110 = P21*DP1010+DP21*P1010
      P1111  = P22*P1010
      DP1111 = 10.0*P1110
      RC2  = G(11,2)*TCP2+G(1,11)*TSP2
      RC3  = G(11,3)*TCP3+G(2,11)*TSP3
      RC4  = G(11,4)*TCP4+G(3,11)*TSP4
      RC5  = G(11,5)*TCP5+G(4,11)*TSP5
      RC6  = G(11,6)*TCP6+G(5,11)*TSP6
      RC7  = G(11,7)*TCP7+G(6,11)*TSP7
      RC8  = G(11,8)*TCP8+G(7,11)*TSP8
      RC9  = G(11,9)*TCP9+G(8,11)*TSP9
      RC10 = G(11,10)*TCP10+G(9,11)*TSP10
      RC11 = G(11,11)*TCP11+G(10,11)*TSP11
      BR = BR-11.0*AOR*(G(11,1)*P111+RC2*P112+RC3*P113+RC4*P114
     *       +RC5*P115+RC6*P116+RC7*P117+RC8*P118+RC9*P119+RC10*P1110
     *       +RC11*P1111)
      BT = BT+AOR*(G(11,1)*DP111+RC2*DP112+RC3*DP113+RC4*DP114
     *       +RC5*DP115+RC6*DP116+RC7*DP117+RC8*DP118+RC9*DP119
     *       +RC10*DP1110+RC11*DP1111)
      BP = BP-AOR*((G(11,2)*TSP2-G(1,11)*TCP2)*P112+2.0*(G(11,3)*TSP3
     *       -G(2,11)*TCP3) *P113 + 3.0 *(G(11,4)*TSP4
     *       -G(3,11)*TCP4) *P114 + 4.0 *(G(11,5)*TSP5
     *       -G(4,11)*TCP5) *P115 + 5.0 *(G(11,6)*TSP6
     *       -G(5,11)*TCP6) *P116 + 6.0 *(G(11,7)*TSP7
     *       -G(6,11)*TCP7) *P117 + 7.0 *(G(11,8)*TSP8
     *       -G(7,11)*TCP8) *P118 + 8.0 *(G(11,9)*TSP9
     *       -G(8,11)*TCP9) *P119 + 9.0 *(G(11,10)*TSP10
     *       -G(9,11)*TCP10)*P1110+10.0*(G(11,11)*TSP11
     *       -G(10,11)*TCP11)*P1111)
C
C........+.........+.........+.........+.........+.........+.........+..
C     \/ Convert to units of Gauss
C........+.........+.........+.........+.........+.........+.........+..
C
  130 BP = BP/P22*1.E-5
      BT = BT*1.E-5
      BR = BR*1.E-5
      B = SQRT(BR*BR+BT*BT+BP*BP)
      RETURN
C
C........+.........+.........+.........+.........+.........+.........+..
C     Y(1) is R coordinate         Y(2) is THETA coordinate
C     Y(3) is PHI coordinate       Y(4) is V(R)
C     Y(5) is V(THETA)             Y(6) is V(PHI)
C     F(1) is R dot                F(2) is THETA dot
C     F(3) is PHI dot              F(4) is R dot dot
C     F(5) is THETA dot dot        F(6) is PHI dot dot
C     BR   is B(R)                 BT   is B(THETA)
C     BP   is B(PHI)               B    is magnitude of magnetic field
C........+.........+.........+.........+.........+.........+.........+..
C
      END
      subroutine azrgeg (na,nz,pamu,rigin,epn,beta)
c
c........+.........+.........+.........+.........+.........+.........+..
c     subroutine to convert rigidity to energy and visa versa
cLast mod 17 March 94
c........+.........+.........+.........+.........+.........+.........+..
c     Programmed by Don F. Smart  (sssrc@msn.com)
c     Note - programming adheres to convention that variables beginning
c            with i, j, k, l, m, n   are integer values,
c            variables beginning with c are character variables
c            all other variables are real*4
c........+.........+.........+.........+.........+.........+.........+..
c
      implicit integer (i-n)
      implicit REAl*8 (a-b)
      implicit REAl*8 (d-h)
      implicit REAl*8 (o-z)
c
c........+.........+.........+.........+.........+.........+.........+..
c
c     write (*,6010) na,nz,pamu,rigin,epn                               ! diag
c6010 format (' azrgeg1 ',2i5,3f15.3)                                   ! diag
c
c........+.........+.........+.........+.........+.........+.........+..
c     Check, if na, nz, or pamu not specified, put in default for protons
c            epamu is rest mass energy per atomic mass unit
c........+.........+.........+.........+.........+.........+.........+..
c
      if (pamu.le.0.0)  pamu = 1.0081451
      if (na.le.0)      na = 1
      if (nz.le.0)      nz = 1
c
      epamu = 931.141
c
      anuc = na
      zcharg = nz
      rsmspn = (pamu/anuc)*epamu
c
      trig = rigin
c
c........+.........+.........+.........+.........+.........+.........+..
c     \/ if trig .le. 0.0    do energy   to rigidity conversion
c        if trig .gt. 0.0    do rigidity to energy conversion
c........+.........+.........+.........+.........+.........+.........+..
c
      if (trig.le.0.0)  then
c                                          Energy to Rigidity conversion
         gmaeg = (anuc*epn+anuc*rsmspn)/(anuc*rsmspn)
         gmaegg = (epn+rsmspn)/rsmspn
         rigin = dsqrt(gmaeg*gmaeg-1.0)*rsmspn*anuc/zcharg
         relgma = gmaeg
      else
c                                          Rigidity to Energy conversion
         gmarg = dsqrt(((rigin*zcharg)/(rsmspn*anuc))**2+1.0)
         epn = (gmarg-1.0)*rsmspn
         relgma = gmarg
      endif
c
c     write (*,6020) anuc,zcharg,rsmspn,rigin,epn,gmaeg,gmaegg,gmarg    ! diag
c     write (*,6030) na,nz,pamu,rigin,epn                               ! diag
c6020 format (' azrgeg2 ',8f10.3)                                       ! diag
c6030 format (' azrgeg3 ',2i5,3f15.5)                                   ! diag
c
      beta = dsqrt(1.0-1.0/(relgma*relgma))
c
      return
c
c          beta is v/c (speed as fraction of light speed)
c          energy in MeV
c          epamu is mass-energy conversion = 931.141 MeV per amu
c          epn is kinetic energy per nucleon
c          na is atomic number
c          nz is charge
c          pamu is rest mass in physical atomic mass units
c          relgam is relativistic factor 'gamma'
c          rigidity in mv
c          rsmspn is rest mass per nucleon in MeV
c
      end
