C.........................<PESIMP.FOR>......................3 APR 92
C------ Reference driver retained as a non-exported subroutine. The library
C------ wrapper calls FLXCAL directly and performs no console or file I/O.
      SUBROUTINE PHOTOELECTRON_REFERENCE_DRIVER()
C...... This test driver demonstrates how to call the model and
C...... how to calculate electron heating rate and 3371 excitation rate.
C------ References and a sample output file are appended to this file
C
       DIMENSION EUV(9),XN(3),PEFLUX(100),UVFAC(59)
C
C------ ALT = altitude (km)  { 120 -> 500 }
C------ SZADEG = solar zenith angle {0 -> 90 degrees}
C------ TE, TN = electron, neutral temperatures (K)
C------ EUV = multiplication factors for bins 1-9 Torr et al. solar EUV
C------ F107 = Solar 10.7 cm flux
C------ XN, XNE = O, O2, N2, and electron densities  (cm-3)
C------ XN2D, XOP2D = N(2D) and O+(2D) densities for electron quenching
C------ (cm-3). You may put these to ZERO if not available.
C
C------ The following data are for orbit 458(D) of AE-E at 296 km
      DATA  ALT , SZADEG ,   TE ,   TN ,  EUV,  F107
     >   /  296.,   78.  , 2000., 850., 9*1.0 ,  71. /
      DATA              XN,           XNE  ,  XN2D  , XOP2D
     >   / 4.0E8 , 2.3E6 , 6.1E7 ,   3.0E5 ,  2.0E5 , 1.0E3/
C
C------ The following data are for orbit 458(D) of AE-E at 148 km
      DATA  ALT , SZADEG ,  TE , TN  ,  EUV,  F107
     >   /  148 ,   53.  , 577., 577., 9*1.0 ,  71. /
      DATA              XN,           XNE  ,  XN2D , XOP2D
     >   / 1.6E10 , 2.3E9 , 3.1E10 , 2.0E5 ,  2.6E3, 4.0E-2/
C
C----- To read data from a file, uncomment the following line.
C....      READ(1,*)  ALT,SZADEG,TE,TN,F107,XN,XNE,XN2D,XOP2D
C
C     WRITE(6,85)
C
 85   FORMAT(/5X,'****************************************************'
     > ,//5X,'The 1992 simple photoelectron model by Phil Richards.'
     > ,//5X,'Before publishing papers using results from this model,'
     > ,//5X,'please consult Phil Richards about an appropriate level'
     > ,//5X,'of acknowlegement for his contribution'
     > ,//5X,'****************************************************'
     > ,//5x,' OUTPUT is on unit 2')
C
C********************************************************************
C----- A crude scaling of solar EUV with F10.7 that works pretty well
      IF(F107.GT.60.0) THEN
         CALL FACEUV(F107,UVFAC)
         DO 10 I=1,9
           EUV(I)=UVFAC(I)
 10      CONTINUE
      ENDIF
C
C********************************************************************
C....... Go and get the photoelectron fluxes
       CALL FLXCAL(ALT,SZADEG,TE,TN,EUV,XN,XNE,XN2D,XOP2D,PEFLUX,AFAC)
C
C------ PEFLUX = photoelectron flux to be returned (eV cm2 sec)-1
C------ AFAC = the solar EUV attenuation warning flag
C
C********************************************************************
C----- Check altitude not dominated by transport
C      IF(ALT.GT.350) WRITE(6,96)
 96    FORMAT(/2X,' **** Altitude above 350km - beware transport'/)
C
C----- Check the attenuation. 1.0E-22 to avoid divide by 0
C     IF(AFAC.LT.0.14) WRITE(6,97) 1.0/(AFAC+1.0E-22)
  97  FORMAT(/2X,' **** EUV attenuation =',1P,E9.2,' is too large'/)
C
C********************************************************************
C-------- Write headers and diagnostics into output file
C
C     WRITE(2,89)
 89   FORMAT(/9X,'Output from Richards simple photoelectron model'
     > ,//4X,'ALT',5X,'SZA',5X,'TE',5X,'TN',6X,'[O]',7X,'[O2]',7X,
     >  '[N2]',5X,'[e]',4X,'AFAC')
C     WRITE(2,90) ALT,SZADEG,TE,TN,XN,XNE,AFAC
C
C     WRITE(2,94) (EUV(I),I=1,9)
 94   FORMAT(/5X,'EUV flux factors (1-9)',9F5.1/)
C
C     WRITE(2,88)
 88   FORMAT(//3X,'E',3X,'FLX/4PI',3X,'PEFLUX',5X,'SIGOX',5X,'SIGN2'
     > ,5X,'EHEAT',5X,'EM3371')
C
C********************************************************************
C........ sample calculation of production rates. EHEAT=electron heating
      EHEAT=0.0
      EM3371=0.0
      DO 20 I=1,100
      E=I-0.5
      CALL SIGEXS(E,TE,XNE,SIGOX,SIGN2,SIGEE)
      EHEAT=EHEAT+PEFLUX(I)*SIGEE*XNE
C........  approximate 3371 A  emission rate x-section
      IF(E.GE.14.5) S3371=7.6E-17*EXP(-0.133*E)
      IF(E.LT.14.5) S3371=1.1199E-24*EXP(1.14*E)
      IF(E.LE.11.0) S3371=0.0
      EM3371=EM3371+PEFLUX(I)*S3371*XN(3)
C
      PEFLX=PEFLUX(I)/12.57
C     WRITE(2,91) E,PEFLX,PEFLUX(I),SIGOX,SIGN2,EHEAT,EM3371
 20   CONTINUE
      RETURN
 90   FORMAT(4F8.2,1P,9E9.1)
 91   FORMAT(F6.1,1P,22E10.2)
      END
C::::::::::::::::::::::::::::: END TEST DRIVER ::::::::::::::::::::::::::
C
C:::::::::::::::::::::::::: PHOTOELECTRON MODEL  ::::::::::::::::::::::::
      SUBROUTINE FLXCAL(ALT,SZADEG,TE,TN,EUV,XN,XNE,XN2D,XOP2D
     >   ,PEFLUX,AFAC)
C....... This subroutine evaluates the photoelectron flux using the concept
C.......  production frequencies developed by Phil Richards at Utah
C....... State University March 1984. It supercedes the model described in
C....... JGR, p2155, 1983.
C------- Some minor updates in April 1992 indicated by C----
C....... I would appreciate any feedback on bugs or clarity and if it
C....... contributes substantially to a paper, I would appreciate the
C....... appropriate acknowledgement.
C......       **************** WARNING ****************
C...... This program is constructed to produce reasonable agreement with
C...... the Atmosphere Explorer-E PES fluxes of John Doering (Lee et al.
C...... PSS 1980, page 947). It will NOT give good fluxes if the EUV
C...... attenuation is greater than about a factor of 7 (AFAC < 0.14).
C...... The model accurately reproduces the measured fluxes very closely
C...... for the case in the test driver at 148 km SZA=53 when AFAC=0.19.
C...... You should compare the output against the Lee et al. 1980 fluxes
C...... periodically as a check. It is doubtful below 140km during the
C...... day and below 200km near sunset. Between 200km & 350km, it should
C...... be good for solar zenith angles < 90 degrees. Above 350 km there
C...... is considerable uncertainty due to neglect of transport but most
C...... models have similar uncertainties at high altitudes due to the
C...... uncertainty in the conjugate photoelectron flux, and the pitch
C...... angle distribution.
C
C------ ALT = altitude (km)  { 120 -> 500 }
C------ SZADEG = solar zenith angle  {0 -> 90 degrees ? }
C------ TE, TN = electron, neutral temperatures (K)
C------ EUV = multiplication factors for bins 1-9 Torr et al. solar EUV
C------ XN, XNE = O, O2, N2, and electron densities  (cm-3)
C------ XN2D, XOP2D = N(2D) and O+(2D) densities for electron quenching
C------ (cm-3). You may put these to ZERO if not available.
C------ PEFLUX = photoelectron flux to be returned (eV cm2 sec)-1
C------ AFAC = the solar EUV attenuation warning flag
C
      DIMENSION RJOX(100),RJN2(100),XN(3),COLUM(3),EUV(9),PEFLUX(100)
C
C------ MIN, MAX = minimum and maximum photoelectron energies {1,100}
      DATA MIN,MAX/1,100/
C....... photoelectron production frequencies by 1.0E9. Renormalized below
C------- Note that the EUV fluxes below 250A are doubled (see refs)
      DATA RJOX/10*19,15,18,14,10,13,9,13,9,7,11,6,26,6,31,6,5,22,4,4,5
     > ,3,5.4,3.4,3.4,5,2.9,2.5,3.2,2.3,1.9,1.8,1.8,1.8,1.5,2.6,1.5,2.5
     > ,2.8,2,2.6,2.1,3.2,1.3,2.5,1.5,1.8,1.3,.3,1,.4,4*.2,.3,.2,.3,.1
     > ,.2,.2,.1,.1,.1,.2,.2, 25*.1/
      DATA RJN2/6*40,43,35,35,28,29,21,25,19,19,13,19,16,12,11,7,18,8,46
     > ,27,5*5,4.3,7.4,5.6,4.3,5.1,4.3,2.8,2.7,2.7,2.1,2.1,1.7,1.6,1.3
     > ,2.5,2,2.1,2.6,2.4,2,1.3,2.2,1.6,2,1,1.4,1.1,.5,4*.3,6*.2,32*.1/
C
C----- convert solar zenith angle to radians
       SZA = SZADEG/57.29578
C-----  check upper and lower energy indices in range
      IF(MAX.GT.100) MAX=100
      IF(MIN.LT.1) MIN=1
C
C----- 2.5eV production from electron quenching of N2D
      PN2D=XN2D*XNE*6.0E-10*SQRT(TE/300.0)
C----- 3.3eV production from electron quenching of O+(2D)
      POP2D=XOP2D*XNE*6.6E-8*SQRT(300./TE)
C
C------ Initialize electron flux
      DO 122 IE=MIN,MAX
        PEFLUX(IE)=0.0
 122  CONTINUE
      CASEL=0.0
C....... evaluate column density for attenuation factor AFAC
      CALL RCOLUM(I,SZA,ALT,TN,XN,COLUM)
C
C.......... begin flux calculation loop............................
      DO 133 IE=1,MAX
      I=MAX+1-IE
      IF(I.LT.MIN) GO TO 55
C
C....... evaluate energy of photon responsible for electron at energy EE
      EE=I-0.5
      EP=EE+17
      IF(EE.LT.22) EP=45
      IF(EE.GE.22.AND.EE.LT.28) EP=41
      IF(EE.GE.28.AND.EE.LT.38) EP=49
C
C..... evaluate total photoionization cross sections for photon energy EP
      CALL PHOSIG(EP,XSOXT,XSO2T,XSN2T)
C
C....... evaluate EUV attenuation factor AFAC
      TAU=COLUM(1)*XSOXT+COLUM(2)*XSO2T+COLUM(3)*XSN2T
      AFAC=EXP(-TAU)
C
C......... low energy cascade production from O(1D) and N2* impact
      CASOX=0.0
      IF(EE.LT.10) CASOX=PEFLUX(I+2)*SIGOX*XN(1)
      CASN2=0.0
      IF(EE.LT.6) CASN2=PEFLUX(I+1)*SIGN2*XN(3)
C
C......... cascade production from thermal electron degradation
      CASEL=0.0
      IF(I.LT.MAX) CASEL=PEFLUX(I+1)*SIGEE*XNE
C
C....... Production from electron quenching of metastables
      EPN2D=0.0
      IF(NINT(EE).EQ.3) EPN2D=PN2D
      EPOP2D=0.0
      IF(NINT(EE).EQ.4) EPOP2D=POP2D
C
C........ evaluate cross sections (must be after cascade production)
      CALL SIGEXS(EE,TE,XNE,SIGOX,SIGN2,SIGEE)
C
C......... adjust production rate for different period of solar cycle
      CALL FACFLX(EE,EUV,FFAC)
C
C......... Production of pe's at energy EE, taking into account
C......... attenuation and EUV variation, and renormalize frequencies
C
      PRODOX=RJOX(I)*XN(1)*AFAC*FFAC*1.0E-9
      PRODN2=RJN2(I)*XN(3)*AFAC*FFAC*1.0E-9
C
C......... Sum all the production rates
      PROD=PRODOX+PRODN2+CASEL+CASOX+CASN2+EPN2D+EPOP2D
C
C....      WRITE(3,90) EE,PRODOX,PRODN2,CASEL,CASOX,CASN2,EPN2D,EPOP2D
 90   FORMAT(1X,F6.1,1P,11E8.1)
C
C........ total loss through collisions
      RLOSS=SIGOX*XN(1)+SIGN2*XN(3)+SIGEE*XNE
C
C........... evaluate photoelectron flux
      PEFLUX(I)=PROD/RLOSS
 133   CONTINUE
C
 55   RETURN
      END
C::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
      SUBROUTINE PHOSIG(EP,XSOXT,XSO2T,XSN2T)
C....... Total photoionization cross sections (good for 0-400A).
C....... These could easily be updated
C------- XSOXT is Samson and Pareek O cross section
      XSOXT=3.10E-17*EXP(-0.033*EP)
      XSO2T=4.44E-17*EXP(-0.027*EP)
      XSN2T=4.13E-17*EXP(-0.030*EP)
      RETURN
      END
C::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
      SUBROUTINE FACFLX(EE,EUV,FFAC)
C....... solar EUV factors. Correspond to the first 9 wavelengths
C....... TORR et al.[1979] GRL page 771 table 3. EUV(9) is for 304A
      DIMENSION EUV(9)
      FFAC=(7*EUV(9)+EUV(8)+0.2*EUV(6))/8.2
      IF(EE.GT.30.AND.EE.LE.38) FFAC=(2*EUV(7)+.5*EUV(5))/2.5
      IF(EE.GT.38.AND.EE.LE.45) FFAC=EUV(4)
      IF(EE.GT.45.AND.EE.LE.66) FFAC=EUV(3)
      IF(EE.GT.66.AND.EE.LE.108) FFAC=EUV(2)
      IF(EE.GT.108) FFAC=EUV(1)
      RETURN
      END
C::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
      SUBROUTINE RCOLUM(J,CHI,ALT,TNJ,XN,COLUM)
C+++++++ this routine evaluates the neutral column density Smith & Smith
C+++++++ JGR 1972 p 3592. Not valid for CHI > 1.57 because there is no
C+++++++ density at grazing altitude.
      DIMENSION XN(3),VERTCL(3),COLUM(3),SN(5),M(3)
      DATA RE,GE,EM,M/6.371E8,980,1.662E-24,16,32,28/
      DATA A,B,C,D,F,G/1.0606963,0.55643831,1.0619896,1.7245609
     >  ,0.56498823,0.06641874/
C
      Z=ALT*1.0E5
C----is sza>90.0 degrees
      IF(CHI.LT.1.5708)GO  TO 2938
C----calculate grazing incidence parameters
      ALTG=(RE+Z)*SIN(3.1416-CHI)-RE
C----if grazing height<120km.,production is zero --- make colum
C---- large to achieve this
      IF(ALTG.GT.120.E5)GO TO 2938
      DO 20 I=1,3
20    COLUM(I)=1.E+22
      RETURN
C
2938      CONTINUE
      GR=GE*(RE/(RE+Z))**2
      RP=RE+Z
      DO 10 I=1,3
      SH=(1.38E-16*TNJ)/(EM*M(I)*GR)
      XP=RP/SH
      Y=SQRT(0.5*XP)*ABS(COS(CHI))
      IF(Y.GT.8) ERFY2=F/(G+Y)
      IF(Y.LT.8) ERFY2=(A+B*Y)/(C+D*Y+Y*Y)
    4 IF(CHI.GT.1.5708)GO  TO 2
      CHAPFN=SQRT(0.5*3.1416*XP)*ERFY2
      COLUM(I)=XN(I)*SH*CHAPFN
        GO TO 10
C........ column density for large solar zenith angle CHI
    2 RG=RP*SIN(3.1416-CHI)
      HG=1.38E-16*TNJ/(EM*M(I)*GE*(RE/(RE+ALTG))**2)
      XG=RG/HG
      SN(I)=XN(I)*EXP((Z-ALTG)/HG)
      COLUM(I)=SQRT(0.5*3.1416*XG)*HG*(2.0*SN(I)-XN(I)*ERFY2)
10       CONTINUE
      RETURN
      END
C::::::::::::::::::::::::::::::::::::::::::::::::::::::::
      SUBROUTINE SIGEXS(E,TE,XNE,SIGOX,SIGN2,SIGEE)
C..... Program for evaluating the total inelastic cross sections
C
C........ loss to thermal electrons ....
      ET=8.618E-5*TE
      SIGEE=(3.37E-12/E**0.94/XNE**0.03)*((E-ET)/
     >   (E-(0.53*ET)))**2.36
C
C...... cross section for o(1d)
      SIGO1D=0.0
      IF(E.GT.1.96) SIGO1D=4E-16*(1-1.96/E)**2/E
C...... total excitation cross section for O excluding O(1D)
      IF(E.LT.25) SIGO=(0.4*E-5)*1.4E-17
      IF(E.GE.25) SIGO=7.0E-17
      IF(SIGO.LT.0.0) SIGO=0.0
C
C...... total excitation cross section for N2......
      IF(E.LT.12) SIGN2=(15.5*E-104.8)*1.7E-18
      IF(E.LT.4.0) SIGN2=5.0E-9*(1-1.4/E)**9 * (1.4/E)**16
      IF(E.GT.11.5) SIGN2=1.4E-16
      IF(SIGN2.LT.0.0) SIGN2=0.0
C
C........ total ionization cross sections from Keiffer and Dunn ....
      SIGION=0.0
      AL=ALOG10(E)
      IF(AL.LT.2.7.AND.AL.GE.1.2) SIGION=-3.6E-16*(AL-1.2)*(AL-3)
      IF(AL.GT.2.7) SIGION=1.2E-14*EXP(-AL*1.6)
      IF(E.LT.50) SIGION=1.0E-16*(0.068*E-1.06)
      IF(SIGION.LE.0.0) SIGION=0.0
C
      SIGOX=SIGO1D+SIGO+0.5*SIGION
      SIGN2=SIGN2+SIGION
      RETURN
      END
C::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
      SUBROUTINE FACEUV(F107,UVFAC)
C........ The EUV flux is scaled linearly with F107 flux. The 37 intervals
C........ of Torr et al. GRL, 1979 p771 are used. The flux factors are 1 for
C........ day 74113 when F107=71. Ratios from day 78348 (F107=206) are used to
C........ complete the scaling.
      DIMENSION UVFAC(59),EUV206(37)
      DATA EUV206/2.6,2.4,1.8,3,1.9,15.7,4.4,3,1.8,4.5,2,4.8,2.9,2.1
     > ,4.3,2.7,1.8,2.7,2.4,3.2,2.0,2.8,2.0,1.8,2.4,2.1,3.0,1.9,2.5
     > ,2.4,2.8,2.8,2.0,2.2,2.7,2.1,1.9/
C............ EUV scaling
         DO 50 I=1,37
         A=(EUV206(I)-1)/135.0
         B=1-A*71
         UVFAC(I)=A*F107+B
         IF(UVFAC(I).LT.0.0) UVFAC(I)=0.0
 50      CONTINUE
         RETURN
         END
C:::::::::::::::::::::::::::: REFERENCES :::::::::::::::::::::::::::
C--
C-- Ratios of photoelectron to EUV ionization rates for aeronomic studies,
C-- P. G. Richards and D. G. Torr,    J. Geophys. Res., 93, 4060,  1988.
C--
C-- Thermal electron quenching of N(2D): consequences for the
C-- ionospheric photoelectron flux and the thermal electron
C-- temperature,  P. G. Richards,    Planet. Space Sci., 34, 689, 1986.
C--
C-- The altitude variation of the ionospheric photoelectron
C-- flux: a comparison of theory and measurement,  P. G. Richards,
C-- and D. G. Torr,   J. Geophys. Res., 90, 2877,  1985
C--
C-- An investigation of the consistency of the ionospheric
C-- measurements of the photoelectron flux and solar EUV flux,  P. G.
C-- Richards and D. G. Torr,   J. Geophys. Res., 89, 5625, 1984.
C--
C-- A simple theoretical model for calculating and
C-- parameterizing the ionospheric photoelectron flux,  P. G.
C-- Richards and D. G. Torr,   J. Geophys. Res., 88, 2155, 1983.
C--
C-- Determination of photoionization branching ratios and total
C-- photoionization cross sections at 304A from experimental
C-- ionospheric photoelectron fluxes,  P. G. Richards, D. G. Torr,
C-- and P. J. Espy,   J. Geophys. Res.,   87, 3599, 1982.
C
C:::::::::::::::::::::::: OUTPUT FILE :::::::::::::::::::::::::::
C
C         Output from Richards simple photoelectron model
C
C    ALT     SZA     TE     TN      [O]       [O2]       [N2]     [e]    AFAC
C  148.00   53.00  577.00  577.00  1.6E+10  2.3E+09  3.1E+10  2.0E+05  1.9E-01
C
C     EUV flux factors (1-9)  1.0  1.0  1.0  1.0  1.0  1.0  1.0  1.0  1.0
C
C
C
C   E   FLX/4PI   PEFLUX     SIGOX     SIGN2     EHEAT     EM3371
C   0.5  1.94E+08  2.44E+09  0.00E+00  0.00E+00  1.94E+03  0.00E+00
C   1.5  4.26E+08  5.36E+09  0.00E+00  4.31E-20  3.59E+03  0.00E+00
C   2.5  1.11E+07  1.40E+08  7.46E-18  2.89E-16  3.62E+03  0.00E+00
C   3.5  5.51E+07  6.92E+08  2.21E-17  2.16E-17  3.72E+03  0.00E+00
C   4.5  9.99E+07  1.26E+09  2.83E-17  0.00E+00  3.86E+03  0.00E+00
C   5.5  6.61E+07  8.31E+08  3.01E-17  0.00E+00  3.94E+03  0.00E+00
C   6.5  5.65E+07  7.10E+08  3.00E-17  0.00E+00  3.99E+03  0.00E+00
C   7.5  2.17E+07  2.72E+08  2.91E-17  1.95E-17  4.01E+03  0.00E+00
C   8.5  1.21E+07  1.52E+08  2.79E-17  4.58E-17  4.02E+03  0.00E+00
C   9.5  7.03E+06  8.84E+07  2.65E-17  7.22E-17  4.03E+03  0.00E+00
C  10.5  4.90E+06  6.16E+07  2.52E-17  9.85E-17  4.03E+03  0.00E+00
C  11.5  3.30E+06  4.15E+07  2.39E-17  1.25E-16  4.03E+03  7.11E-01
C  12.5  3.17E+06  3.98E+07  2.28E-17  1.40E-16  4.03E+03  2.85E+00
C  13.5  2.35E+06  2.95E+07  2.73E-17  1.40E-16  4.03E+03  7.79E+00
C  14.5  2.45E+06  3.08E+07  3.18E-17  1.40E-16  4.03E+03  1.83E+01
C  15.5  1.67E+06  2.09E+07  3.65E-17  1.40E-16  4.04E+03  2.46E+01
C  16.5  2.27E+06  2.85E+07  4.43E-17  1.46E-16  4.04E+03  3.21E+01
C  17.5  1.71E+06  2.15E+07  5.25E-17  1.53E-16  4.04E+03  3.71E+01
C  18.5  1.22E+06  1.54E+07  6.08E-17  1.60E-16  4.04E+03  4.02E+01
C  19.5  1.23E+06  1.55E+07  6.91E-17  1.67E-16  4.04E+03  4.29E+01
C  20.5  7.13E+05  8.97E+06  7.75E-17  1.73E-16  4.04E+03  4.43E+01
C  21.5  2.09E+06  2.62E+07  8.59E-17  1.80E-16  4.04E+03  4.78E+01
C  22.5  5.73E+05  7.21E+06  9.43E-17  1.87E-16  4.04E+03  4.87E+01
C  23.5  3.01E+06  3.78E+07  1.03E-16  1.94E-16  4.04E+03  5.26E+01
C  24.5  1.40E+06  1.76E+07  1.11E-16  2.01E-16  4.04E+03  5.42E+01
C  25.5  3.41E+05  4.28E+06  1.17E-16  2.07E-16  4.04E+03  5.45E+01
C  26.5  7.10E+05  8.93E+06  1.20E-16  2.14E-16  4.04E+03  5.51E+01
C  27.5  2.98E+05  3.75E+06  1.23E-16  2.21E-16  4.04E+03  5.54E+01
C  28.5  4.38E+05  5.51E+06  1.26E-16  2.28E-16  4.04E+03  5.56E+01
C  29.5  4.57E+05  5.75E+06  1.29E-16  2.35E-16  4.04E+03  5.59E+01
C  30.5  3.44E+05  4.32E+06  1.32E-16  2.41E-16  4.04E+03  5.61E+01
C  31.5  5.82E+05  7.31E+06  1.35E-16  2.48E-16  4.04E+03  5.63E+01
C  32.5  4.09E+05  5.14E+06  1.38E-16  2.55E-16  4.04E+03  5.65E+01
C  33.5  3.29E+05  4.13E+06  1.41E-16  2.62E-16  4.04E+03  5.66E+01
C  34.5  4.06E+05  5.11E+06  1.45E-16  2.69E-16  4.04E+03  5.67E+01
C  35.5  2.99E+05  3.76E+06  1.48E-16  2.75E-16  4.04E+03  5.68E+01
C  36.5  2.06E+05  2.59E+06  1.51E-16  2.82E-16  4.04E+03  5.69E+01
C  37.5  2.15E+05  2.70E+06  1.54E-16  2.89E-16  4.04E+03  5.69E+01
C  38.5  2.45E+05  3.08E+06  1.57E-16  2.96E-16  4.04E+03  5.70E+01
C  39.5  1.97E+05  2.48E+06  1.60E-16  3.03E-16  4.04E+03  5.70E+01
C  40.5  1.97E+05  2.47E+06  1.64E-16  3.09E-16  4.04E+03  5.70E+01
C  41.5  1.73E+05  2.17E+06  1.67E-16  3.16E-16  4.04E+03  5.70E+01
C  42.5  1.68E+05  2.12E+06  1.70E-16  3.23E-16  4.04E+03  5.71E+01
C  43.5  1.40E+05  1.76E+06  1.73E-16  3.30E-16  4.04E+03  5.71E+01
C  44.5  2.62E+05  3.29E+06  1.77E-16  3.37E-16  4.04E+03  5.71E+01
C  45.5  1.91E+05  2.40E+06  1.80E-16  3.43E-16  4.04E+03  5.71E+01
C  46.5  2.36E+05  2.97E+06  1.83E-16  3.50E-16  4.04E+03  5.71E+01
C  47.5  2.84E+05  3.58E+06  1.86E-16  3.57E-16  4.04E+03  5.71E+01
C  48.5  2.44E+05  3.06E+06  1.89E-16  3.64E-16  4.04E+03  5.71E+01
C  49.5  2.39E+05  3.01E+06  1.93E-16  3.71E-16  4.04E+03  5.72E+01
C  50.5  1.73E+05  2.18E+06  1.95E-16  3.75E-16  4.04E+03  5.72E+01
C  51.5  2.85E+05  3.58E+06  1.96E-16  3.77E-16  4.04E+03  5.72E+01
C  52.5  1.71E+05  2.15E+06  1.97E-16  3.80E-16  4.04E+03  5.72E+01
C  53.5  2.53E+05  3.18E+06  1.98E-16  3.82E-16  4.04E+03  5.72E+01
C  54.5  1.39E+05  1.74E+06  1.99E-16  3.84E-16  4.04E+03  5.72E+01
C  55.5  1.85E+05  2.33E+06  2.00E-16  3.86E-16  4.04E+03  5.72E+01
C  56.5  1.43E+05  1.80E+06  2.01E-16  3.88E-16  4.04E+03  5.72E+01
C  57.5  5.39E+04  6.77E+05  2.01E-16  3.90E-16  4.04E+03  5.72E+01
C  58.5  6.82E+04  8.57E+05  2.02E-16  3.92E-16  4.04E+03  5.72E+01
C  59.5  4.30E+04  5.40E+05  2.03E-16  3.93E-16  4.04E+03  5.72E+01
C  60.5  3.47E+04  4.37E+05  2.04E-16  3.95E-16  4.04E+03  5.72E+01
C  61.5  3.53E+04  4.43E+05  2.04E-16  3.97E-16  4.04E+03  5.72E+01
C  62.5  2.69E+04  3.38E+05  2.05E-16  3.98E-16  4.04E+03  5.72E+01
C  63.5  2.73E+04  3.43E+05  2.06E-16  4.00E-16  4.04E+03  5.72E+01
C  64.5  3.23E+04  4.07E+05  2.06E-16  4.01E-16  4.04E+03  5.72E+01
C  65.5  2.80E+04  3.52E+05  2.07E-16  4.03E-16  4.04E+03  5.72E+01
C  66.5  3.32E+04  4.17E+05  2.08E-16  4.04E-16  4.04E+03  5.72E+01
C  67.5  2.38E+04  2.99E+05  2.08E-16  4.05E-16  4.04E+03  5.72E+01
C  68.5  1.95E+04  2.45E+05  2.09E-16  4.06E-16  4.04E+03  5.72E+01
C  69.5  1.97E+04  2.48E+05  2.09E-16  4.08E-16  4.04E+03  5.72E+01
C  70.5  1.49E+04  1.87E+05  2.10E-16  4.09E-16  4.04E+03  5.72E+01
C  71.5  1.50E+04  1.89E+05  2.10E-16  4.10E-16  4.04E+03  5.72E+01
C  72.5  1.52E+04  1.91E+05  2.11E-16  4.11E-16  4.04E+03  5.72E+01
C  73.5  2.06E+04  2.59E+05  2.11E-16  4.12E-16  4.04E+03  5.72E+01
C  74.5  2.08E+04  2.61E+05  2.12E-16  4.13E-16  4.04E+03  5.72E+01
C  75.5  1.57E+04  1.97E+05  2.12E-16  4.14E-16  4.04E+03  5.72E+01
C  76.5  1.58E+04  1.99E+05  2.12E-16  4.15E-16  4.04E+03  5.72E+01
C  77.5  1.60E+04  2.01E+05  2.13E-16  4.16E-16  4.04E+03  5.72E+01
C  78.5  1.61E+04  2.03E+05  2.13E-16  4.16E-16  4.04E+03  5.72E+01
C  79.5  1.63E+04  2.04E+05  2.13E-16  4.17E-16  4.04E+03  5.72E+01
C  80.5  1.64E+04  2.06E+05  2.14E-16  4.18E-16  4.04E+03  5.72E+01
C  81.5  1.65E+04  2.08E+05  2.14E-16  4.19E-16  4.04E+03  5.72E+01
C  82.5  1.67E+04  2.10E+05  2.14E-16  4.19E-16  4.04E+03  5.72E+01
C  83.5  1.68E+04  2.11E+05  2.15E-16  4.20E-16  4.04E+03  5.72E+01
C  84.5  1.69E+04  2.13E+05  2.15E-16  4.21E-16  4.04E+03  5.72E+01
C  85.5  1.71E+04  2.14E+05  2.15E-16  4.21E-16  4.04E+03  5.72E+01
C  86.5  1.72E+04  2.16E+05  2.15E-16  4.22E-16  4.04E+03  5.72E+01
C  87.5  1.73E+04  2.17E+05  2.16E-16  4.23E-16  4.04E+03  5.72E+01
C  88.5  1.74E+04  2.19E+05  2.16E-16  4.23E-16  4.04E+03  5.72E+01
C  89.5  1.75E+04  2.20E+05  2.16E-16  4.24E-16  4.04E+03  5.72E+01
C  90.5  1.76E+04  2.22E+05  2.16E-16  4.24E-16  4.04E+03  5.72E+01
C  91.5  1.78E+04  2.23E+05  2.17E-16  4.25E-16  4.04E+03  5.72E+01
C  92.5  1.79E+04  2.25E+05  2.17E-16  4.25E-16  4.04E+03  5.72E+01
C  93.5  1.80E+04  2.26E+05  2.17E-16  4.26E-16  4.04E+03  5.72E+01
C  94.5  1.81E+04  2.27E+05  2.17E-16  4.26E-16  4.04E+03  5.72E+01
C  95.5  1.82E+04  2.29E+05  2.17E-16  4.26E-16  4.04E+03  5.72E+01
C  96.5  1.83E+04  2.30E+05  2.17E-16  4.27E-16  4.04E+03  5.72E+01
C  97.5  1.84E+04  2.31E+05  2.18E-16  4.27E-16  4.04E+03  5.72E+01
C  98.5  1.85E+04  2.32E+05  2.18E-16  4.28E-16  4.04E+03  5.72E+01
C  99.5  1.86E+04  2.33E+05  2.18E-16  4.28E-16  4.04E+03  5.72E+01
