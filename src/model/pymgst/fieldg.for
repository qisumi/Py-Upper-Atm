      SUBROUTINE FIELDG (DLAT,DLONG,ALT,TM,NMX,L,X,Y,Z,F)                     1
      COMMON /COEFFS/TG(18,18)                                                3
      COMMON /FLDCOM/ST,CT,SPH,CPH,R,NMAX,BT,BP,BR,B                          4
      COMMON/SPHRC/G,GT,GTT,J,K,TZERO,AID,MAXN
      DIMENSION G(18,18),GT(18,18),SHMIT(18,18),AID(11)                       5
        DIMENSION GTT(18,18)
      EQUIVALENCE (SHMIT,TG)                                                  2
      A=6378.165                                                             44
      FLAT=1.-1./298.25
      A2=A**2                                                                46
      A4=A**4                                                                47
      B2=(A*FLAT)**2                                                         48
      A2B2=A2*(1.-FLAT**2)                                                   49
      A4B4=A4*(1.-FLAT**4)                                                   50
100   IF(L) 19,1,2
1     IF (TM-TLAST) 17,19,17                                                 52
2     READ (2,3) J,K,TZERO,(AID(I),I=1,11)
3     FORMAT (2I1,1X,F6.1,10A6,A3)                                           54
      WRITE (3,4) J,K,TZERO,(AID(I),I=1,11)
4     FORMAT (2I3,5X6HEPOCH=,F7.1,5X10A6,A3)                                 57
      MAXN=0                                                                 58
      TEMP=0.                                                                59
      DO 901 NN=1,18
      DO 902 MM=1,18
      G(NN,MM)=0.
      GT(NN,MM)=0.
      GTT(NN,MM)=0.
  902 CONTINUE
  901 CONTINUE
5     READ (2,6) N,M,GNM,HNM,GTNM,HTNM,GTTNM,HTTNM
6     FORMAT (2I3,6F11.4)                                                    61
      IF (N.LE.0) GOTO7                                                      62
      MAXN=(MAX0(N,MAXN))                                                    63
      G(N,M)=GNM                                                             64
      GT(N,M)=GTNM                                                           65
      TEMP=AMAX1(TEMP,ABS(GTNM))                                             66
      GTT(N,M)=GTTNM
      IF (M.EQ.1) GOTO5                                                      67
      G(M-1,N)=HNM                                                           68
      GT(M-1,N)=HTNM                                                         69
      GTT(M-1,N)=HTTNM
      GO TO 5                                                                70
7     WRITE(3,70)MAXN
70    FORMAT(72X 5HMAXN=I2)
      IF(L.GT.1) GO TO 120
      WRITE (3,8)
8     FORMAT (6H  N  M,6X1HG,10X1HH,11X2HGT,9X2HHT,8X3HGTT8X3HHTT//)
      DO 12 N=2,MAXN                                                         73
      DO 12 M=1,N                                                            74
      MI=M-1                                                                 75
      IF (M.EQ.1) GOTO10                                                     76
      WRITE (3,9) N,M,G(N,M),G(MI,N),GT(N,M),GT(MI,N),GTT(N,M),GTT(MI,N)
9     FORMAT(2I3,2F11.1,2F11.2,2F11.3)
      GO TO 12                                                               79
10    WRITE (3,11) N,M,G(N,M),GT(N,M),GTT(N,M)
11    FORMAT (2I3,F11.1,11X,F11.2,11XF11.3)
12    CONTINUE                                                               82
120   WRITE (3,13)                                                           83
13    FORMAT (1H0)
      L=0                                                                    55
      IF (TEMP.EQ.0.) L=-1                                                   85
14    IF (K.NE.0) GOTO17                                                     86
      SHMIT(1,1)=-1.                                                         87
      DO 15 N=2,MAXN                                                         88
      SHMIT(N,1)=SHMIT(N-1,1)*FLOAT(2*N-3)/FLOAT(N-1)                        89
      JJ=2                                                                   91
      DO 15 M=2,N                                                            92
      SHMIT(N,M)=SHMIT(N,M-1)*SQRT(FLOAT((N-M+1)*JJ)/FLOAT(N+M-2))           93
      SHMIT(M-1,N)=SHMIT(N,M)                                                94
15    JJ=1                                                                   95
      DO 16 N=1,MAXN
      DO 16 M=1,MAXN
      G(N,M)=G(N,M)*SHMIT(N,M)                                               98
      GT(N,M)=GT(N,M)*SHMIT(N,M)                                             99
16    GTT(N,M)=GTT(N,M)*SHMIT(N,M)
17    T=TM-TZERO                                                            103
      TLAST=TM                                                              110
      DO 18 N=1,MAXN                                                        104
      DO 18 M=1,MAXN
18    TG(N,M)=G(N,M)+T*(GT(N,M)+GTT(N,M)*T)
19    SINLA=SIN(DLAT/57.2957795)                                            111
      RLONG=DLONG/57.2957795                                                112
      CPH=COS(RLONG)                                                        113
      SPH=SIN(RLONG)                                                        114
      IF (J.EQ.0) GOTO20                                                    115
      R=ALT+6371.2                                                          116
      CT=SINLA                                                              117
      GO TO 21                                                              118
20    SINLA2=SINLA**2                                                       119
      COSLA2=1.-SINLA2                                                      120
      DEN2=A2-A2B2*SINLA2                                                   121
      DEN=SQRT(DEN2)                                                        122
      FAC=(((ALT*DEN)+A2)/((ALT*DEN)+B2))**2                                123
      CT=SINLA/SQRT(FAC*COSLA2+SINLA2)                                      124
      R=SQRT(ALT*(ALT+2.*DEN)+(A4-A4B4*SINLA2)/DEN2)                        125
21    ST=SQRT(1.-CT**2)                                                     126
      NMAX=MIN0(NMX,MAXN)                                                   127
      CALL FIELD                                                            128
      Y=BP
      F=B
      IF (J) 22,23,22                                                       129
22    X=-BT                                                                 130
      Z=-BR                                                                 131
      RETURN                                                                132
C     TRANSFORMS FIELD TO GEODETIC DIRECTIONS                               133
23    SIND=SINLA*ST-SQRT(COSLA2)*CT                                         134
      COSD=SQRT(1.0-SIND**2)                                                135
      X=-BT*COSD-BR*SIND                                                    136
      Z=BT*SIND-BR*COSD                                                     137
      RETURN                                                                138
      END
      SUBROUTINE FIELD                                                        1
      COMMON /COEFFS/G(18,18)                                                 2
      COMMON/FLDCOM/ST,CT,SPH,CPH,R,NMAX,BT,BP,BR,B                           3
      DIMENSION P(18,18),DP(18,18),CONST(18,18),SP(18),CP(18),FN(18),FM(      4
     118)                                                                     41
      DO 901 N=1,18
      SP(N)=0.
      CP(N)=0.
      FN(N)=0.
      FM(N)=0.
      DO 902 M=1,18
      P(N,M)=0.
      DP(N,M)=0.
      CONST(N,M)=0.
  902 CONTINUE
  901 CONTINUE
      P(1,1)=1.                                                               6
      DP(1,1)=0.                                                              7
      SP(1)=0.                                                                8
      CP(1)=1.                                                                9
      DO 2 N=2,18                                                            10
      FN(N)=N                                                                11
      DO 2 M=1,N                                                             12
      FM(M)=M-1                                                              13
2     CONST(N,M)=FLOAT((N-2)**2-(M-1)**2)/FLOAT((2*N-3)*(2*N-5))             14
3     SP(2)=SPH                                                              16
      CP(2)=CPH                                                              17
      DO 4 M=3,NMAX                                                          18
      SP(M)=SP(2)*CP(M-1)+CP(2)*SP(M-1)                                      19
4     CP(M)=CP(2)*CP(M-1)-SP(2)*SP(M-1)                                      20
      AOR=6371.2/R                                                           21
      AR=AOR**2                                                              22
      BT=0.                                                                  23
      BP=0.                                                                  24
      BR=0.                                                                  25
      DO 8 N=2,NMAX                                                          26
      AR=AOR*AR                                                              27
      DO 8 M=1,N                                                             28
      IF (N-M) 6,5,6                                                         29
5     P(N,N)=ST*P(N-1,N-1)                                                   30
      DP(N,N)=ST*DP(N-1,N-1)+CT*P(N-1,N-1)                                   31
      GO TO 7                                                                32
6     P(N,M)=CT*P(N-1,M)-CONST(N,M)*P(N-2,M)                                 33
      DP(N,M)=CT*DP(N-1,M)-ST*P(N-1,M)-CONST(N,M)*DP(N-2,M)                  34
7     PAR=P(N,M)*AR                                                          35
      IF (M.EQ.1) GO TO 9                                                    36
      TEMP=G(N,M)*CP(M)+G(M-1,N)*SP(M)                                       361
      BP=BP-(G(N,M)*SP(M)-G(M-1,N)*CP(M))*FM(M)*PAR                          37
      GO TO 10                                                               371
9     TEMP=G(N,M)*CP(M)                                                      38
      BP=BP-(G(N,M)*SP(M))*FM(M)*PAR                                         381
10    BT=BT+TEMP*DP(N,M)*AR                                                  39
8     BR=BR-TEMP*FN(N)*PAR                                                   391
      BP=BP/ST                                                               40
      B=SQRT(BT*BT+BP*BP+BR*BR)                                              41
      RETURN                                                                 42
      END                                                                    43
      BLOCK DATA
      COMMON/SPHRC/G(18,18),GT(18,18),GTT(18,18),J,K,TZERO,AID(11),MAXN
      DATA J,K,TZERO,MAXN/2*0,1965.,9/
      DATA AID/6HIGRF(1,6H0/68) ,6HFROM W,6HASHING,6HTON WM,6HS MEET,
     X 6HING   ,4*6H       /
      DATA G/0.,-30339.,-1654.,1297.,958.,-223.,47.,71.,10.,9*0.,
     2 5758.,-2123.,2994.,-2036.,805.,357.,60.,-54.,9.,9*0.,
     3 -2006.,130.,1567.,1289.,492.,246.,4.,0.,-3.,9*0.,
     4 -403.,242.,-176.,843.,-392.,-26.,-229.,12.,-12.,9*0.,
     5 149.,-280.,8.,-265.,256.,-161.,3.,-25.,-4.,9*0.,
     6 16.,125.,-123.,-107.,77.,-51.,-4.,-9.,7.,9*0.,
     7 -14.,106.,68.,-32.,-10.,-13.,-112.,13.,-5.,9*0.,
     8  -57.,-27.,-8.,9.,23.,-19.,-17.,-2.,12.,9*0.,
     9 3.,-13.,5.,-17.,4.,22.,-3.,-16.,6.,171*0./
      DATA GT/0.,15.3,-24.4,.2,-.7,1.9,-.1,-.5,.1,9*0.,
     2 -2.3,8.7,.3,-10.8,.2,1.1,-.3,-.3,.4,9*0.,
     3 -11.8,-16.7,-1.6,.7,-3.,2.9,1.1,-.7,.6,9*0.,
     4 4.2,.7,-7.7,-3.8,-.1,.6,1.9,-.5,10*0.,
     5 -.1,1.6,2.9,-4.2,-2.1,0.,-.4,.3,10*0.,
     6 2.3,1.7,-2.4,.8,-.3,1.3,-.4,0.,-.1,9*0.,
     7 -.9,-.4,2.,-1.1,.1,.9,-.2,-.2,.3,9*0.,
     8 -1.1,.3,.4,.2,.4,.2,.3,-.6,-.3,9*0.,
     9 .1,-.2,-.3,-.2,-.3,-.4,-.3,-.3,-.5,171*0./
      DATA GTT/324*0./
      END
