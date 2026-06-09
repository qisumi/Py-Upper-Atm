      BLOCK DATA GSFC_INIT
      COMMON /GSFC_PATH/ DATA_ROOT
      COMMON /GSFC_TLAST_BLK/ TLAST_G
      CHARACTER*256 DATA_ROOT
      REAL TLAST_G
      DATA DATA_ROOT /' '/
      DATA TLAST_G /0./
      END
C
C  Reset all COMMON block state to force clean evaluation.
C  Called from the C shim before each gsfc_eval.
C
      SUBROUTINE GSFC_RESET_TLAST
      COMMON /GSFC_TLAST_BLK/ TLAST_G
      REAL TLAST_G
      TLAST_G=0.0
      RETURN
      END
C
      SUBROUTINE FIDD(MODEL,JJ,DLAT,DLONG,ALT1,TM,X,Y,Z,F)
C-----------------------------------------------------------------------
C  SUBROUTINE "FIDD" IS A DRIVER ROUTINE FOR SUBROUTINE "FID".
C
C  INPUTS TO FID:  MODEL - 0 FOR GSFC80, 1 FOR GSFC83, 2 FOR GSFC87
C		   JJ - SEE BELOW
C		   DLAT - LATITUDE
C                  DLONG - LONGITUDE
C                  ALT1 - ALTITUDE OR GEOCENTRIC RADIUS.
C                  TM - TIME (DECIMAL YEARS, E.G. 1981.234)
C
C  OUTPUTS TO FID: X - X (NORTH) COMPONENT IN NT.
C                  Y - Y (EAST) COMPONENT.
C                  Z - VERTICALLY DOWN COMPONENT.
C                  F - SCALAR MAGNITUDE.
C
C  SET JJ = 0 FOR SURFACE DATA, I.E. DATA REFERENCED TO THE GEODETIC
C  ELLIPSOID.  SET JJ = 1 FOR GEOCENTRIC DATA (USUALLY SPACE DATA), IN
C  SPHERICAL COORDINATES. IF JJ=1, THEN ALT1 SHOULD BE THE GEOCENTRIC
C  RADIUS IN KM.  IF JJ=0, THEN ALT1 SHOULD BE GEODETIC ALTITUDE IN
C  KM.  SET NMX TO THE MAXIMUM DESIRED DEGREE OF THE SPHERICAL HARMONIC
C  FIELD EXPANSION.  THIS OVERULES THE "NMAX" VALUE READ IN ON THE
C  COEFFICIENT FILE (UNIT #5), ONLY IF IT IS LESS THAN NMAX.
C-----------------------------------------------------------------------
C  MAKE TM DOUBLE PRECISION  ------- dkb feb 1998
      DOUBLE PRECISION TM
      COMMON /GSFC_PATH/ DATA_ROOT
      CHARACTER*256 DATA_ROOT
      CHARACTER*512 FULLPATH
      INTEGER TRIMLEN
      DATA 	MM/0/ ,NMX/11/ ,NEXT/5/ ,DST/0.0/ ,IDST/0/ ,LL/1/

      IO=17
C  Build full path: trim(data_root) // '/' // filename
      TRIMLEN = 256
  10  IF (TRIMLEN.LE.1) GO TO 11
      IF (DATA_ROOT(TRIMLEN:TRIMLEN).NE.' ') GO TO 11
      TRIMLEN = TRIMLEN - 1
      GO TO 10
  11  CONTINUE
      IF(MODEL.EQ.0) THEN
        IF (TRIMLEN.GT.1) THEN
          FULLPATH = DATA_ROOT(1:TRIMLEN) // '/GSFC80.DAT'
        ELSE
          FULLPATH = 'GSFC80.DAT'
        ENDIF
	OPEN(UNIT=IO,FILE=FULLPATH,STATUS='OLD',FORM='FORMATTED')
      ELSE IF(MODEL.EQ.1) THEN
        IF (TRIMLEN.GT.1) THEN
          FULLPATH = DATA_ROOT(1:TRIMLEN) // '/GSFC83.DAT'
        ELSE
          FULLPATH = 'GSFC83.DAT'
        ENDIF
	OPEN(UNIT=IO,FILE=FULLPATH,STATUS='OLD',FORM='FORMATTED')
      ELSE
        IF (TRIMLEN.GT.1) THEN
          FULLPATH = DATA_ROOT(1:TRIMLEN) // '/GSFC87.DAT'
        ELSE
          FULLPATH = 'GSFC87.DAT'
        ENDIF
	OPEN(UNIT=IO,FILE=FULLPATH,STATUS='OLD',FORM='FORMATTED')
      ENDIF
      REWIND(IO)
      ALT = ALT1
C  FID mutates L to cache coefficients. Python callers can instantiate
C  multiple GSFC versions in one process, so reload the selected model file.
      LL = 1
      CALL FID(IO,JJ,MM,NEXT,IDST,DLAT,DLONG,ALT,TM,DST,NMX,LL,X,Y,
     *           Z,F)
      CLOSE(IO)
      JJ = 0
      RETURN
      END
C
      SUBROUTINE FID (IU,J,MM,NEXT,IDST,DLAT,DLONG,Q1,TM,DST,NMX,L,X,
     *           Y,Z,F)
C***********************************************************************
C  J.EQ.0    INPUTS LATITUDE & Q1=ALTITUDE (KM) RELATIVE TO ELLIPSOID
C            (GEODETIC COORDINATES)
C  J.EQ.0    OUTPUT FIELD COMPONENTS NORTH,EAST,VERTICAL
C            IN GEODETIC COORDINATES
C
C  J.NE.0    LAT.&LONG IN SPHERICAL COORDINATES,Q1=GEOCENTRIC RADIUS(KM)
C  J.NE.0    OUTPUT FLD COMPONENTS NORTH,EAST,VERTICAL IN SPHERICAL COOR
C
C  MM.EQ.0   USE DEFAULT VALUES AE=6378.16,FLAT=298.25
C  MM.NE.0   INPUT VALUES FOR AE,FLAT     ON FIRST CALL TO FDG
C
C  NEXT.EQ.0 DO NOT READ INPUT VALUES FOR EXTERNAL FIELD PARAMETERS
C            WHEN L IS GREATER THAN 0
C  NEXT.EQ.0 DO NOT EVALUATE EXTERNAL FIELD FROM MODEL
C  NEXT.NE.0 READ INPUT VALUES FOR EXTERNAL FIELD PARAMETERS WHEN
C            L GREATER 0
C  NEXT.NE.0 EVALUATE EXTERNAL FIELD MODEL
C
C  IDST.EQ.0      DO NOT EVALUATE INDUCED COEFFICIENTS
C  IDST.EQ.1      EVALUATE INDUCED COEFFICIENTS
C
C  DLAT      GEODETIC LATITUDE IN DEGREES WHEN J=0
C            GEOCENTRIC LATITUDE IN DEGREES WHEN J=1
C
C  DLONG     LONGITUDE IN DEGREES
C
C  Q1        GEODETIC ALTITUDE (KM) WHEN J=0
C            GEOCENTRIC RADIUS (KM) WHEN J=1
C
C  NMX     MAX DEG OF MODEL EVALUATION
C  DST     DST VALUE
C
C  NMAX      MAXIMUM DEGREE AND ORDER OF CONSTANT TERMS OF FIELD MODEL
C  NMAXT     "      "     "  FIRST ORDER TIME        "    "     "
C  NMAXTT    "      "     "  SECOND   "    "         "    "     "
C  NMXTTT    "      "     "  THIRD    "    "         "    "     "
C
C  K.EQ.0    FIELD MODEL COEFFICIENTS SCHMIDT NORMALIZED
C  K.NE.0    FIELD MODEL COEFFICIENTS GAUSS NORMALIZED
C
C  TZERO     EPOCH TIME FOR FIELD MODEL COEFFICIENTS
C
C  ABAR      MEAN RADIUS USED IN FIELD MODEL POTENTIAL EXPANSION
C            (DEFAULT = 6371.2)
C
C  MODEXT.EQ.0 NO EXTERNAL FIELD SOLVED WITH MODEL
C  MODEXT.NE.0 EXTERNAL FIELD SOLVED WITH MODEL
C
C   MODIND.EQ.0     NO INDUCED COEFFS SOLVED WITH MODEL
C   MODIND.NE.0      INDUCED COEFFS SOLVED WITH MODEL
C  L.EQ.0    EVALUATE FIELD
C  L.GT.0    READ IN FIELD MODEL AND EVALUATE FIELD
C  L.LE.0    EVALUATE FIELD AT OLD TIME
C
C***********************************************************************
C
C  MAKE TM DOUBLE PRECISION
      DOUBLE PRECISION TM
      EQUIVALENCE (SHMIT(1,1),TG(1,1))
      COMMON /COEFFS/TG(31,31)
          COMMON/INDUCE/IIDST,ALFA1,ALFA2,ALFA3,ALFA4,DSTT
      COMMON /FLDCOM/ST,CT,SPH,CPH,R,NMAX,BT,BP,BR,B,
     &ABAR,E1,E2,E3,NEXTF,Q(31,31)
      COMMON /GSFC_TLAST_BLK/ TLAST
      DIMENSION G(31,31),GT(31,31),SHMIT(31,31),AID(33)
      DIMENSION GTTT(8,8),GTT(31,31)
      REAL TLAST
      DATA IFRST/0/
      DATA AE,FLAT/6378.16,298.25/
      DATA TABAR/6371.2/
      IF(IFRST) 110,100,110
C
C        EQUATORIAL EARTH RADIUS AND FLATTENING FACTOR
C        USED IN GEODETIC-GEOCENTRIC COORDINATES.
C
C        THE MODEL ITSELF IS INDEPENDENT OF THOSE
C        PARAMETERS
C
  100 IF(MM.NE.0)READ(IU,101) AE,FLAT
  101 FORMAT(1X,2F6.1)
      IFRST=1
      FLAT=1. -1./FLAT
      E1=0.
      E2=0.
      E3=0.
          ALFA1=0.
          ALFA2=0.
          ALFA3=0.
          ALFA4=0.
      A2=AE**2
      A4=AE**4
      B2=(AE*FLAT)**2
      A2B2=A2*(1.-FLAT**2)
      A4B4=A4*(1.-FLAT**4)
  110 IF (L) 19,1,2
1     IF (TM-TLAST) 17,19,17
2     READ (IU,3) NMAX,NMAXT,NMAXTT,NMXTTT,MODEXT,K,TZERO,ABAR,MODIND,
     &(AID(I),I=1,13)
3     FORMAT(4I2,2I2,2F6.1,I2,12A4,A2)
      IF(ABAR.EQ.0.) ABAR=TABAR
      READ(IU,103) (AID(I),I=14,33)
103   FORMAT(20A4)
      L=0
C  Reloading different GSFC versions in one process requires deterministic
C  coefficient work arrays; uninitialized entries can propagate NaNs.
      DO 35 II=1,31
      DO 35 JJ2=1,31
      G(II,JJ2)=0.0
      GT(II,JJ2)=0.0
      GTT(II,JJ2)=0.0
      SHMIT(II,JJ2)=0.0
      Q(II,JJ2)=0.0
   35 CONTINUE
      DO 36 II=1,8
      DO 36 JJ2=1,8
      GTTT(II,JJ2)=0.0
   36 CONTINUE
      MAXN=0
      TEMP=0.
 5    READ (IU,6) N,M,GNM,HNM,GTNM,HTNM,GTTNM,HTTNM
6     FORMAT (2I3,6F11.4)
C         N=NL + 1
C         M=ML + 1
      IF (N.LE.0) GOTO7
      MAXN=(MAX0(N,MAXN))
      G(N,M)=GNM
      GT(N,M)=GTNM
      GTT(N,M)=GTTNM
      TEMP=AMAX1(TEMP,ABS(GTNM))
      IF (M.EQ.1) GOTO5
      G(M-1,N)=HNM
      GT(M-1,N)=HTNM
      GTT(M-1,N)=HTTNM
      GO TO 5
7     IF(NMXTTT.EQ.0) GO TO 107
106   READ(IU,6)N,M,GTTTNM,HTTTNM
      IF(N.EQ.0) GO TO 107
      IF(N.GT.8) STOP 106
      GTTT(N,M)=GTTTNM
      IF(M.EQ.1) GO TO 106
      GTTT(M-1,N)=HTTTNM
      GO TO 106
107   CONTINUE
C                              READ EXTERNAL FIELD
      IF(MODEXT.NE.0) THEN
 30     READ(IU,6) N,M,QNM,SNM
        IF(N .LE. 0) GO TO 31
        Q(N,M) = QNM
        IF(M .EQ. 1) GO TO 30
        Q(M-1,N) = SNM
        GO TO 30
      END IF
 31   CONTINUE
      IF(MODIND.NE.0.AND.IDST.NE.0) READ(IU,102)ALFA1,ALFA2,ALFA3,
     .      ALFA4
102   FORMAT(6X,4F11.4)
      DO 12 N=2,MAXN
      DO 12 M=1,N
      MI=M-1
      IF (M.EQ.1) GOTO10
      GO TO 12
10    CONTINUE
12    CONTINUE
      IF(MODEXT.NE.0) THEN
          DO 32 N = 2,MODEXT
          DO 32 M = 1,N
            IF(M .EQ. 1) SNM = 0.0
            IF(M .NE. 1) SNM = Q(M-1,N)
 32       CONTINUE
      END IF
 13     FORMAT (1H1)
      IF (TEMP.EQ.0.) L=-1
14    IF (K.NE.0) GOTO17
      SHMIT(1,1)=-1.
      DO 15 N=2,MAXN
      SHMIT(N,1)=SHMIT(N-1,1)*FLOAT(2*N-3)/FLOAT(N-1)
      SHMIT(1,N)=0.
      JJ=2
      DO 15 M=2,N
      SHMIT(N,M)=SHMIT(N,M-1)*SQRT(FLOAT((N-M+1)*JJ)/FLOAT(N+M-2))
      SHMIT(M-1,N)=SHMIT(N,M)
15    JJ=1
      DO 16 N=2,MAXN
      DO 16 M=1,N
      G(N,M)=G(N,M)*SHMIT(N,M)
      GT(N,M)=GT(N,M)*SHMIT(N,M)
      GTT(N,M)=GTT(N,M)*SHMIT(N,M)
      IF(NMXTTT.GT.0.AND.N.LE.8)GTTT(N,M)=GTTT(N,M)*SHMIT(N,M)
      IF (M.EQ.1) GOTO16
      G(M-1,N)=G(M-1,N)*SHMIT(M-1,N)
      GT(M-1,N)=GT(M-1,N)*SHMIT(M-1,N)
      GTT(M-1,N)=GTT(M-1,N)*SHMIT(M-1,N)
      IF(NMXTTT.GT.0.AND.N.LE.8)GTTT(M-1,N)=GTTT(M-1,N)*SHMIT(M-1,N)
16    CONTINUE
      IF(MODEXT .NE. 0) THEN
        DO 33 N = 2,MODEXT
        DO 33 M = 1,N
          Q(N,M) = Q(N,M)*SHMIT(N,M)
          IF(M .EQ. 1) GO TO 33
          Q(M-1,N) = Q(M-1,N)*SHMIT(M-1,N)
 33     CONTINUE
      END IF
17    T=TM-TZERO
      DO 18 N=1,MAXN
      DO 18 M=1,N
      TGX=0.
      THX=0.
      IF(M.EQ.1) GO TO 270
      IF(N.GT.NMXTTT) GO TO 210
      TGX=GTTT(N,M)*T
      THX=GTTT(M-1,N)*T
210   IF(N.GT.NMAXTT) GO TO 220
      TGX=(TGX + GTT(N,M))*T
      THX= (THX + GTT(M-1,N))*T
220   IF(N.GT.NMAXT) GO TO 230
      TGX=(TGX + GT(N,M))*T
      THX=(THX+GT(M-1,N))*T
230   TGX=TGX+G(N,M)
      THX=THX+G(M-1,N)
      TG(N,M)=TGX
      TG(M-1,N)=THX
      GO TO 18
 270  CONTINUE
      IF(N.GT.NMXTTT) GO TO 240
      TGX=GTTT(N,M)*T
240   IF(N.GT.NMAXTT) GO TO 250
      TGX=(TGX+GTT(N,M))*T
250   IF(N.GT.NMAXT) GO TO 260
      TGX=(TGX+GT(N,M))*T
260   TGX= TGX+G(N,M)
      TG(N,M)=TGX
 18   CONTINUE
      TLAST=TM
19    DLATR=DLAT/57.2957795D0
      SINLA=SIN(DLATR)
      RLONG=DLONG/57.2957795D0
      CPH=COS(RLONG)
      SPH=SIN(RLONG)
      IF (J.EQ.0) GOTO20
C
C         Q1 IS GEOCENTRIC RADIUS WHEN J=1
C
      R=Q1
      CT=SINLA
      GO TO 21
20    SINLA2=SINLA**2
C
C         Q1 IS GEODETIC ALTITUDE WHEN J=0
C         ALT=Q1
C
      COSLA2=1.-SINLA2
      DEN2=A2-A2B2*SINLA2
      DEN=SQRT(DEN2)
      FAC=(((Q1*DEN)+A2)/((Q1*DEN)+B2))**2
      CT=SINLA/SQRT(FAC*COSLA2+SINLA2)
      R=SQRT(Q1*(Q1+2.*DEN)+(A4-A4B4*SINLA2)/DEN2)
21    ST=SQRT(1.-CT**2)
      NMAX=MIN0(NMX,MAXN)
      NEXTF=NEXT
          DSTT=DST
          IIDST=IDST
      CALL MAGF
      Y=BP
      F=B
      IF (J) 22,23,22
22    X=-BT
      Z=-BR
      RETURN
C     TRANSFORMS FIELD TO GEODETIC DIRECTIONS
23    SIND=SINLA*ST-SQRT(COSLA2)*CT
      COSD=SQRT(1.0-SIND**2)
      X=-BT*COSD-BR*SIND
      Z=BT*SIND-BR*COSD
      RETURN
      END
C
      SUBROUTINE MAGF
      DIMENSION P(31,31),DP(31,31),CONST(31,31),SP(31),CP(31),FN(31),
     .     FM(31),DXDQ(31,31),DXDS(31,31),DYDQ(31,31),DYDS(31,31),
     .     DZDQ(31,31),DZDS(31,31)
      COMMON /INDUCE/ IDST,ALFA1,ALFA2,ALFA3,ALFA4,DST
      COMMON /COEFFS/ G(31,31)
      COMMON /FCORE/ BRC,BTC,BPC,BC,BNEXT
      COMMON /FLDCOM/ ST,CT,SPH,CPH,R,NMAX,BT,BP,BR,B,ABAR,E1,E2,E3,
     .     NEXT,Q(31,31)
      DATA NCORE/14/
C  Do not depend on persisted local-array state across compilers/runners.
      DO 40 I=1,31
      SP(I)=0.0
      CP(I)=0.0
      FN(I)=0.0
      FM(I)=0.0
      DO 40 J=1,31
      P(I,J)=0.0
      DP(I,J)=0.0
      CONST(I,J)=0.0
      DXDQ(I,J)=0.0
      DXDS(I,J)=0.0
      DYDQ(I,J)=0.0
      DYDS(I,J)=0.0
      DZDQ(I,J)=0.0
      DZDS(I,J)=0.0
   40 CONTINUE
1     P(1,1)=1.
      DP(1,1)=0.
      SP(1)=0.
      CP(1)=1.
      DO 2 N=2,NMAX
      FN(N)=N
      DO 2 M=1,N
      FM(M)=M-1
2     CONST(N,M)=FLOAT((N-2)**2-(M-1)**2)/FLOAT((2*N-3)*(2*N-5))
3     SP(2)=SPH
      CP(2)=CPH
      DO 4 M=3,NMAX
      SP(M)=SP(2)*CP(M-1)+CP(2)*SP(M-1)
4     CP(M)=CP(2)*CP(M-1)-SP(2)*SP(M-1)
      AOR=ABAR/R
      AR=AOR**2
          BTC=0.0
          BPC=0.0
          BRC=0.0
          BC=0.0
      BT=0.
      BP=0.
      BR=0.
          IF(IDST.EQ.0) GO TO 12
          GBAR=G(2,1)
          G(2,1)=GBAR + ALFA1*DST
          E1BAR = Q(2,1)
          E2BAR = Q(2,2)
          E3BAR = Q(1,2)
          Q(2,1) = Q(2,1) + ALFA2*DST
          Q(2,2) = Q(2,2) + ALFA3*DST
          Q(1,2) = Q(1,2) + ALFA4*DST
  12       CONTINUE
          DO 8 N=2,NMAX
      AR=AOR*AR
      DO 8 M=1,N
      IF (N-M) 6,5,6
5     P(N,N)=ST*P(N-1,N-1)
      DP(N,N)=ST*DP(N-1,N-1)+CT*P(N-1,N-1)
      GO TO 7
6     P(N,M)=CT*P(N-1,M)-CONST(N,M)*P(N-2,M)
C
C         NOTE : CONST(2,1)=0
C
      DP(N,M)=CT*DP(N-1,M)-ST*P(N-1,M)-CONST(N,M)*DP(N-2,M)
7     PAR=P(N,M)*AR
      IF (M.EQ.1) GO TO 9
      TEMP=G(N,M)*CP(M)+G(M-1,N)*SP(M)
      BP=BP-(G(N,M)*SP(M)-G(M-1,N)*CP(M))*FM(M)*PAR
      GO TO 10
9     TEMP=G(N,M)*CP(M)
10    BT=BT+TEMP*DP(N,M)*AR
      BR=BR-TEMP*FN(N)*PAR
          IF(N.GT.NCORE) GO TO 8
          BTC=BT
          BRC=BR
          BPC=BP
  8       CONTINUE
      BP=BP/ST
          BPC=BPC/ST
          BNEXT=SQRT(BT*BT + BP*BP + BR*BR)
      IF(NEXT.GT.0) THEN
CCC
          MONO = 2
          SIND = 0.0
          COSD = 1.0
          CX = -BT
          CY =  BP
          CZ = -BR
          ROA= 1.0/AOR
          RB= (ROA)**(2*(MONO-2)+1)
          ROA2= ROA*ROA
        DO 11 N= MONO,NEXT
          FNC= N-1
          RB= RB*ROA2
        DO 11 M= 1,N
          FMC= M-1
          P(N,M)= P(N,M)*RB
          DP(N,M)= DP(N,M)*RB
           TEMP= -FNC*P(N,M)*SIND - DP(N,M)*COSD
          DXDQ(N,M)= TEMP*CP(M)
          DXDS(N,M)= TEMP*SP(M)
           TEMP= FMC*P(N,M)/ST
          DYDQ(N,M)= -TEMP*SP(M)
          DYDS(N,M)= TEMP*CP(M)
           TEMP= -FNC*P(N,M)*COSD + DP(N,M)*SIND
          DZDQ(N,M)= TEMP*CP(M)
          DZDS(N,M)= TEMP*SP(M)
          IF(M .EQ. 1) THEN
            CX= CX + Q(N,M)*DXDQ(N,M)
            CY= CY + Q(N,M)*DYDQ(N,M)
            CZ= CZ + Q(N,M)*DZDQ(N,M)
          ELSE
            CX= CX + Q(N,M)*DXDQ(N,M) + Q(M-1,N)*DXDS(N,M)
            CY= CY + Q(N,M)*DYDQ(N,M) + Q(M-1,N)*DYDS(N,M)
            CZ= CZ + Q(N,M)*DZDQ(N,M) + Q(M-1,N)*DZDS(N,M)
          END IF
  11    CONTINUE
        BRC = BRC + (-CZ - BR)
        BPC = BPC + ( CY - BP)
        BTC = BTC + (-CX - BT)
          BT = -CX
          BP =  CY
          BR = -CZ
CCC
      END IF
          B=SQRT(BT*BT+BP*BP+BR*BR)
          BC=SQRT(BTC*BTC + BRC*BRC + BPC*BPC)
          BTC=BT - BTC
          BPC=BP - BPC
          BRC=BR - BRC
          BC= B - BC
          IF(IDST.EQ.0) RETURN
          Q(2,1) = E1BAR
          Q(2,2) = E2BAR
          Q(1,2) = E3BAR
          G(2,1)=GBAR
          RETURN
          END
