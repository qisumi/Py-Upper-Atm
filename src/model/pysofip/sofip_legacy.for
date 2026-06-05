C SOFIP_LEGACY.FOR — Legacy Fortran 77 subroutines for SOFIP
C
C Contains: TRARA1, TRARA2 (trapped radiation flux interpolation)
C           DSPCTR, SMOOTH  (differential spectrum computation)
C           SOFIP_SOLPRO    (solar proton fluence — renamed to avoid
C                            conflict with the standalone SOLPRO model)
C
C TRARA1/TRARA2 sourced from trmfun.for (RADBELT).
C DSPCTR/SMOOTH/SOFIP_SOLPRO sourced from the CRRES SOFIP distribution.
C
C********************************************************************
C*************** TRARA1, TRARA2 *************************************
C********************************************************************
C
      SUBROUTINE TRARA1(DESCR,MAP,FL,BB0,E,F,N)
C***********************************************************************
C*** TRARA1 FINDS PARTICLE FLUXES FOR GIVEN ENERGIES, MAGNETIC FIELD ***
C*** STRENGTH AND L-VALUE. FUNCTION TRARA2 IS USED TO INTERPOLATE IN ***
C*** B-L-SPACE.                                                      ***
C***   INPUT: DESCR(8)   HEADER OF SPECIFIED TRAPPED RADITION MODEL  ***
C***          MAP(...)   MAP OF TRAPPED RADITION MODEL               ***
C***          N          NUMBER OF ENERGIES                          ***
C***          E(N)       ARRAY OF ENERGIES IN MEV                    ***
C***          FL         L-VALUE                                     ***
C***          BB0        =B/B0  MAGNETIC FIELD STRENGTH NORMALIZED   ***
C***                     TO FIELD STRENGTH AT MAGNETIC EQUATOR       ***
C***  OUTPUT: F(N)       DECADIC LOGARITHM OF INTEGRAL FLUXES IN     ***
C***                     PARTICLES/(CM*CM*SEC)                       ***
C***********************************************************************
      LOGICAL S0,S1,S2
      DIMENSION E(N),F(N),MAP(1)
      INTEGER DESCR(8)
      COMMON/TRA2/FISTEP
      DATA F1,F2/1.001,1.002/
C
      FISTEP=DESCR(7)/DESCR(2)
      ESCALE=DESCR(4)
      FSCALE=DESCR(7)
      XNL=AMIN1(15.6,ABS(FL))
      NL=XNL*DESCR(5)
      IF(BB0.LT.1.) BB0=1.
      NB=(BB0-1.)*DESCR(6)
C
      I1=0
      I2=MAP(1)
      I3=I2+MAP(I2+1)
      L3=MAP(I3+1)
      E1=MAP(I1+2)/ESCALE
      E2=MAP(I2+2)/ESCALE
C
      S1=.TRUE.
      S2=.TRUE.
C
      DO 3 IE=1,N
C
    1 IF((E(IE).LE.E2).OR.(L3.EQ.0)) GOTO 2
        I0=I1
        I1=I2
        I2=I3
        I3=I3+L3
        L3=MAP(I3+1)
        E0=E1
        E1=E2
        E2=MAP(I2+2)/ESCALE
        S0=S1
        S1=S2
        S2=.TRUE.
        F0=F1
        F1=F2
        GOTO 1
C
    2 IF(S1) F1=TRARA2(MAP(I1+3),NL,NB)/FSCALE
      IF(S2) F2=TRARA2(MAP(I2+3),NL,NB)/FSCALE
      S1=.FALSE.
      S2=.FALSE.
C
      F(IE)=F1+(F2-F1)*(E(IE)-E1)/(E2-E1)
      IF(F2.GT.0.0) GOTO 3
      IF(I1.EQ.0)   GOTO 3
C
      IF(S0) F0=TRARA2(MAP(I0+3),NL,NB)/FSCALE
      S0=.FALSE.
      F(IE)=AMIN1(F(IE),F0+(F1-F0)*(E(IE)-E0)/(E1-E0))
C
    3 F(IE)=AMAX1(F(IE),0.)
      RETURN
      END
C
      FUNCTION TRARA2(MAP,IL,IB)
C*****************************************************************
C***  TRARA2 INTERPOLATES LINEARLY IN L-B/B0-MAP TO OBTAIN     ***
C***  THE LOGARITHM OF INTEGRAL FLUX AT GIVEN L AND B/B0.      ***
C*****************************************************************
      DIMENSION MAP(1)
      COMMON/TRA2/FISTEP
      FNL=IL
      FNB=IB
      ITIME=0
      I2=0
C
    1 L2=MAP(I2+1)
      IF(MAP(I2+2).GT.IL) GOTO 2
        I1=I2
        L1=L2
        I2=I2+L2
        GOTO 1
    2 CONTINUE
C
      IF((L1.LT.4).AND.(L2.LT.4)) GOTO 50
C
      IF(MAP(I2+3).GT.MAP(I1+3))  GOTO 10
    5   KT=I1
        I1=I2
        I2=KT
        KT=L1
        L1=L2
        L2=KT
C
   10 FLL1=MAP(I1+2)
      FLL2=MAP(I2+2)
      DFL=(FNL-FLL1)/(FLL2-FLL1)
      FLOG1=MAP(I1+3)
      FLOG2=MAP(I2+3)
      FKB1=0.
      FKB2=0.
      IF(L1.LT.4) GOTO 32
C
      DO 17 J2=4,L2
        FINCR2=MAP(I2+J2)
        IF(FKB2+FINCR2.GT.FNB) GOTO 23
        FKB2=FKB2+FINCR2
   17 FLOG2=FLOG2-FISTEP
      ITIME=ITIME+1
      IF(ITIME.EQ.1)GO TO 5
      GO TO 50
   23 IF(ITIME.EQ.1)GO TO 30
      IF(J2.EQ.4)GO TO 28
      SL2=FLOG2/FKB2
      DO 27 J1=4,L1
        FINCR1=MAP(I1+J1)
        FKB1=FKB1+FINCR1
        FLOG1=FLOG1-FISTEP
        FKBJ1=((FLOG1/FISTEP)*FINCR1+FKB1)/((FINCR1/FISTEP)*SL2+1.)
        IF(FKBJ1.LE.FKB1) GOTO 31
   27 CONTINUE
      IF(FKBJ1.LE.FKB2) GOTO 50
   31 IF(FKBJ1.LE.FKB2) GOTO 29
      FKB1=0.
   30 FKB2=0.
   32 J2=4
      FINCR2=MAP(I2+J2)
      FLOG2=MAP(I2+3)
      FLOG1=MAP(I1+3)
   28 FLOGM=FLOG1+(FLOG2-FLOG1)*DFL
      FKBM=0.
      FKB2=FKB2+FINCR2
      FLOG2=FLOG2-FISTEP
      SL2=FLOG2/FKB2
      IF(L1.LT.4) GOTO 35
      J1=4
      FINCR1=MAP(I1+J1)
      FKB1=FKB1+FINCR1
      FLOG1=FLOG1-FISTEP
      SL1=FLOG1/FKB1
      GOTO 15
   29 FKBM=FKBJ1+(FKB2-FKBJ1)*DFL
      FLOGM=FKBM*SL2
      FLOG2=FLOG2-FISTEP
      FKB2=FKB2+FINCR2
      SL1=FLOG1/FKB1
      SL2=FLOG2/FKB2
   15 IF(SL1.LT.SL2) GOTO 20
        FKBJ2=((FLOG2/FISTEP)*FINCR2+FKB2)/((FINCR2/FISTEP)*SL1+1.)
        FKB=FKB1+(FKBJ2-FKB1)*DFL
        FLOG=FKB*SL1
        IF(FKB.GE.FNB) GOTO 60
        FKBM=FKB
        FLOGM=FLOG
        IF(J1.GE.L1) GOTO 50
        J1=J1+1
        FINCR1=MAP(I1+J1)
        FLOG1=FLOG1-FISTEP
        FKB1=FKB1+FINCR1
        SL1=FLOG1/FKB1
        GOTO 15
   20 FKBJ1=((FLOG1/FISTEP)*FINCR1+FKB1)/((FINCR1/FISTEP)*SL2+1.)
      FKB=FKBJ1+(FKB2-FKBJ1)*DFL
      FLOG=FKB*SL2
      IF(FKB.GE.FNB) GOTO 60
        FKBM=FKB
        FLOGM=FLOG
        IF(J2.GE.L2) GOTO 50
        J2=J2+1
        FINCR2=MAP(I2+J2)
        FLOG2=FLOG2-FISTEP
        FKB2=FKB2+FINCR2
        SL2=FLOG2/FKB2
        GOTO 15
   35 FINCR1=0.
      SL1=-900000.
      GOTO 20
   60 IF(FKB.LT.FKBM+1.E-10) GOTO 50
      TRARA2=FLOGM+(FLOG-FLOGM)*((FNB-FKBM)/(FKB-FKBM))
      TRARA2=AMAX1(TRARA2,0.)
      RETURN
   50 TRARA2=0.
      RETURN
      END
C
C********************************************************************
C*************** DIFFERENTIAL SPECTRUM *******************************
C********************************************************************
C
C CALCULATES FIRST DERIVATIVES OF INPUT SPECTRUM DEFINED BY FF VS XX
C INPUT:  XX - 30 INTEGRAL THRESHOLD ENERGIES, IN MEV         (R*4)
C         FF - ALOG OF THE INTEGRAL FLUXES FOR THE 30 ENERGY  (R*4)
C              LEVELS, IN PARTICLES/CM**2/SEC
C OUTPUT: DD - DIFFERENTIAL FLUXES OBTAINED FROM THE INTEGRAL (R*4)
C              FLUXES, IN PARTICLES/CM**2/SEC/KEV
C
      SUBROUTINE DSPCTR(FF,XX,DD)
      IMPLICIT REAL*8(A-H,O-Z)
      REAL*4 DD,FF,XX
      DIMENSION F(30),X(30),D(30),H(500),FF(30),XX(30),DD(30)
      DATA EPSLN,OMEGA/1.D-6,1.0717968D0/
C
      M=0
      DO 5 L=1,30
    5 DD(L)=0.0
C
      DO 10 K=1,30
      IF(FF(K).EQ.0.) GOTO 15
      M=K-1
      F(K)=FF(K)+DLOG(1000.D0)
      X(K)=XX(K)*1000.D0
   10 D(K)=X(K)
   15 K=M+1
      IF(K.LT.10) GOTO 170
C
      CALL SMOOTH(X,F,M)
C
      DO 30 I=1,M
         H(I)=X(I+1)-X(I)
   30    H(K+I)=(F(I+1)-F(I))/H(I)
      DO 40 I=2,M
         H(2*K+I)=H(I-1)+H(I)
         H(3*K+I)=.5*H(I-1)/H(2*K+I)
         H(4*K+I)=(H(K+I)-H(K+I-1))/H(2*K+I)
         H(5*K+I)=H(4*K+I)+H(4*K+I)
   40    H(6*K+I)=H(5*K+I)+H(4*K+I)
      H(5*K+1)=0.
      H(6*K)=0.
C
      KCOUNT=0
   50 ETA=0.
      KCOUNT=KCOUNT+1
      DO 70 I=2,M
         W=(H(6*K+I)-H(3*K+I)*H(5*K+I-1)-(.5-H(3*K+I))
     $   *H(5*K+I+1)-H(5*K+I)*OMEGA)
         IF(DABS(W).LE.ETA) GOTO 60
         ETA=DABS(W)
   60    H(5*K+I)=H(5*K+I)+W
   70 CONTINUE
      IF(KCOUNT.GT.5*K) GOTO 170
      IF(ETA.GE.EPSLN) GOTO 50
C
      DO 80 I=1,M
   80    H(7*K+I)=(H(5*K+1+I)-H(5*K+I))/H(I)
      DO 140 J=1,K
         I=1
         IF(D(J).EQ.X(1)) GOTO 130
         IF(D(J)-X(K)) 100,110,110
   90    IF(D(J)-X(I)) 120,130,100
  100    I=I+1
         GOTO 90
  110    I=K
  120    I=I-1
  130    HT1=D(J)-X(I)
         HT2=D(J)-X(I+1)
         PROD=HT1*HT2
         H(8*K+J)=H(5*K+I)+HT1*H(7*K+I)
         DELSQS=(H(5*K+I)+H(5*K+1+I)+H(8*K+J))/6.
  140    D(J)=-(H(K+I)+(HT1+HT2)*DELSQS
     $         +PROD*H(7*K+I)*.1666667D0)
C
      CALL SMOOTH(X,D,M)
C
      DO 160 I=1,K
      F(I)=2.718281828D0**(F(I)-DLOG(1000.D0))
  160 DD(I)=D(I)*F(I)
  170 RETURN
      END
C
C SMOOTH DATA BY 3-POINT AVERAGING OVER EQUAL INTERVALS
C
      SUBROUTINE SMOOTH(X,F,M)
      IMPLICIT REAL*8(A-H,O-Z)
      DIMENSION X(30),F(30)
      FINTER(X1,X2,X3,Y1,Y2,Y3,XIN)=Y1*(XIN-X2)*(XIN-X3)/
     $((X1-X2)*(X1-X3)) + Y2*(XIN-X1)*(XIN-X3)/((X2-X1)*(X2-X3))
     $                  + Y3*(XIN-X1)*(XIN-X2)/((X3-X1)*(X3-X2))
C
      FI = F(1)
      DO 20 I=2,M
        SIZE1 = X(I) - X(I-1)
        SIZE2 = X(I+1) - X(I)
        IF(DABS(SIZE1-SIZE2).LT.0.001) GO TO 200
        IF(SIZE2.GT.SIZE1) GO TO 210
        F2 = F(I+1)
        XINTER = X(I) - SIZE2
        F1 = FINTER(X(I-1),X(I),X(I+1),FI,F(I),F2,XINTER)
        GO TO 300
  210   F1 = FI
        XINTER = X(I) + SIZE1
        F2 = FINTER(X(I-1),X(I),X(I+1),F1,F(I),F(I+1),XINTER)
        GO TO 300
  200   F1 = FI
        F2 = F(I+1)
  300   FNEW = (F1+2.0*F(I)+F2)/4.
        FI = F(I)
        F(I) = FNEW
   20 CONTINUE
      RETURN
      END
C
C********************************************************************
C*************** SOLAR PROTON FLUENCE *******************************
C********************************************************************
C
C Renamed from SOLPRO to SOFIP_SOLPRO to avoid linker conflict with
C the standalone pysolpro model.
C
C INTERPLANETARY SOLAR PROTON FLUX AT 1 AU (FROM E>10 TO E>200 MEV
C FOR ANOMALOUSLY LARGE (AL) EVENTS AND FROM E>10 TO E>100 MEV FOR
C ORDINARY (OR) EVENTS)
C
C INPUT:  TAU   MISSION DURATION IN MONTHS (REAL*4)
C         IQ    CONFIDENCE LEVEL THAT FLUENCE WILL NOT BE EXCEEDED
C               (INTEGER*4, 80-99)
C OUTPUT: F(N)  SPECTRUM OF INTEGRAL SOLAR PROTON FLUENCE
C               ENERGIES E>10*N (1<=N<=20) FOR AL EVENTS
C               ENERGIES E>10*N (1<=N<=10) FOR OR EVENTS
C         INALE # OF AL EVENTS FOR GIVEN TAU AND Q
C
      SUBROUTINE SOFIP_SOLPRO(TAU,IQ,F,INALE)
      REAL NALE,NALECF(7,20)/-.1571,.2707,-.1269E-1,.4428E-3,
     $-.8185E-5,.7754E-7,-.2939E-9,-.1870,.1951,-.6559E-2,
     $.1990E-3,-.3618E-5,.3740E-7,-.1599E-9,-.2007,.1497,
     $-.3179E-2,.5730E-4,-.4664E-6,.1764E-8,0.,-.1882,.1228,
     $-.1936E-2,.2660E-4,-.1022E-6,2*0.,-.2214,.1149,-.1871E-2,
     $.2695E-4,-.1116E-6,2*0.,-.2470,.1062,-.1658E-2,.2367E-4,
     $-.9465E-7,2*0.,-.2509,.8710E-1,-.8300E-3,.8438E-5,3*0.,
     $-.2923,.8932E-1,-.1023E-2,.1029E-4,3*0.,-.3222,.8648E-1,
     $-.9992E-3,.9935E-5,3*0.,-.3518,.8417E-1,-.1000E-2,
     $.9956E-5,3*0.,-.3698,.7951E-1,-.8983E-3,.8940E-5,3*0.,
     $-.2771,.5473E-1,-.1543E-4,4*0.,-.2818,.5072E-1,.2511E-4,
     $4*0.,-.2845,.4717E-1,.5664E-4,4*0.,-.2947,.4405E-1,
     $.8507E-4,4*0.,-.2923,.4111E-1,.1106E-3,4*0.,-.2981,
     $.3853E-1,.1312E-3,4*0.,-.3002,.3585E-1,.1529E-3,4*0.,
     $-.3001,.3312E-1,.1781E-3,4*0.,-.3141,.3248E-1,.1654E-3,
     $4*0./,F(20),G(20)
      REAL ORFLXC(5,9)/.154047E3,-.522258E4,.714275E5,-.432747E6,
     $.955315E6,.198004E3,-.448788E4,.438148E5,-.196046E6,
     $.32552E6,.529120E3,-.122227E5,.112869E6,-.465084E6,
     $.710572E6,.121141E4,-.266412E5,.226778E6,-.85728E6,
     $.120444E7,.452062E4,-.103248E6,.896085E6,-.346028E7,
     $.499852E7,.272028E4,-.499088E5,.35305E6,-.111929E7,
     $.133386E7,.275597E4,-.469718E5,.314729E6,-.960383E6,
     $.11165E7,.570997E4,-.799689E5,.381074E6,-.610714E6,0.,
     $.101E3,4*0./
      INTEGER INDEX(20)/2*7,6,3*5,5*4,9*3/
C
      IF(TAU.GT.72..OR.IQ.LT.80)GO TO 500
      IP=100-IQ
      M=INDEX(IP)
      NALE=0.
      DO 300 J=1,M
  300 NALE=NALE+NALECF(J,IP)*TAU**(J-1)
      INALE=NALE+1.0001
      IF(INALE.GT.0) GO TO 400
C *** OR-EVENT CONDITIONS
      IT=TAU
      IF(IT.EQ.1.AND.IP.GT.16) GO TO 700
      P=FLOAT(IP)/100.
      OF=0.
      DO 100 J=1,5
  100 OF=OF+ORFLXC(J,IT)*P**(J-1)*1.E7
      E=10.
      DO 200 N=1,10
      G(N)=EXP(.0158*(30.-E))
      F(N)=OF*G(N)
  200 E=E+10.
      GO TO 800
C *** AL-EVENT CONDITIONS
  400 E=10.
      DO 600 N=1,20
      F(N)=7.9E9*EXP((30.-E)/26.5)*INALE
  600 E=E+10.
      GO TO 800
  700 CONTINUE
      DO 710 N=1,20
  710 F(N)=0.0
      GO TO 800
  500 CONTINUE
      DO 510 N=1,20
  510 F(N)=0.0
  800 RETURN
      END
