C     **************************************************************
C     *                   MERGED XULI.FOR                          *
C     **************************************************************
C Merged Xu-Li Neutral Sheet Model source for library use.
C Contains subroutines extracted from the original AEN, SEN, DEN
C programs with shared utilities deduplicated.
C
C Subroutines included:
C   STIL  - Compute geomagnetic dipole tilt angle
C   SMPF  - Magnetopause radius (Sibeck et al., 1991)
C   SAEN  - Analytical Equatorial Neutral sheet
C   SSEN  - Standard Equatorial Neutral sheet
C   SDEN  - Displaced Equatorial Neutral sheet
C   SD1   - Displaced parameter D for DEN
C   SFA4  - Quartic equation root finder for SD1
C
C Original authors:
C   Ronglan Xu and Lei Li, Center for Space Sci. and Applied Res.,
C   Chinese Academy of Sciences, PO Box 8701, Beijing 100080, China

C     ================================================================
C     SUBROUTINE STIL - Compute dipole tilt angle
C     ================================================================
        SUBROUTINE STIL(DOY,HR,TMI,TILA)
C THIS SUBROUTINE IS TO FIND THE TILT ANGLE OF THE GEOMAGNETIC AXIS IN
C  DIFFERENT TIME: DOY(Day Of Year), HR(Hour) and TMI(Minute)
C INPUT: DOY,HR,TMI
C OUTPUT: TILA(Degree)
        PI=3.14159
        RAD=PI/180.
        TD=DOY+(HR+TMI/60.)/24.-80.6
        TH=HR+TMI/60.-4.6
        FD=360./365.
        FH=360./24.
        TILA=23.5*SIN(RAD*FD*TD)-11.7*COS(RAD*FH*TH)
        RETURN
        END

C     ================================================================
C     SUBROUTINE SMPF - Magnetopause radius (Sibeck et al., 1991)
C     ================================================================
        SUBROUTINE SMPF(XSM,RMP,IM)
C FIND THE RADIUS OF THE CROSS SECTION OF THE MAGNETOPAUSE RMP AND PARAMETER IE
C IE=1: INSIDE THE MAGNETOPAUSE, IE=2: OUTSIDE THE MAGNETOPAUSE
C RMP IS DETERMINED BY THE
C  MAGNETOPAUSE MODEL OF SIBECK ET AL IN:
C  Sibeck, D. G., R. E. Lopez, and R. C. Roelof, Solar wind control of the
C  magnetopause shape, location, and motion, J. Grophys. Res., 96, 5489, 1991
         IM=0
         RMP2=-0.14*XSM**2-18.2*XSM+217.2
         IF(RMP2.LT.0) THEN
           IM=9999.99
           GOTO 50
         ENDIF
         RMP=SQRT(RMP2)
         IF(XSM.LE.-65) RMP=28.5
 50      RETURN
         END

C     ================================================================
C     SUBROUTINE SAEN - Analytical Equatorial Neutral sheet
C     ================================================================
         SUBROUTINE SAEN(TILA,XSM,YSM,ZAEN,RMP,IE)
C FIND THE POSITION OF AEN(Analytical Equatorial-Neutral) SHEET ALONG ZSM AXIS
C  (ZAEN), THE RADIUS OF THE CROSS SECTION OF THE MAGNETOPAUSE (RMP) FOR
C  DIFFERENT XSM,YSM AND TILA(Tilt Angle) AND SHOW WHETHER AEN IS INSIDE THE
C  MAGNETOPAUSE OR NOT. WHERE:
C  IE=1: IS INSIDE THE MAGNETOPAUSE, IE=2: IS OUTSIDE THE MAGNETOPAUSE
C THE RADIUS OF THE CROSS SECTION OF THE MAGNETOPAUSE IS DETERMINED BY THE
C  MAGNETOPAUSE MODEL OF SIBECK ET AL IN:
C  Sibeck, D. G., R. E. Lopez, and R. C. Roelof, Solar wind control of the
C  magnetopause shape, location, and motion, J. Grophys. Res., 96, 5489, 1991
C INPUT XSM,YSM,TILA(Degree)
C OUTPUT ZAEN,RMP,IE

* INTITIAL PARAMETER
         IE=1
         RAD=3.14159/180
         H0=12.6/3.14159
         TIL=TILA*RAD
* THE ANALYTICAL EQUATORIAL NEUTRAL SURFACE
         ZAEN=-H0*SIN(TIL)*ATAN(XSM/5)*(2*COS(YSM/6))
* FIND WHETHER AEN IS INSIDE THE MAGNETOPAUSE OR NOT
         RP=SQRT(YSM**2+ZAEN**2)
         CALL SMPF(XSM,RMP,IM)
         IF(RP.GT.RMP.OR.IM.EQ.9999.99) IE=2
         RETURN
         END

C     ================================================================
C     SUBROUTINE SSEN - Standard Equatorial Neutral sheet
C     ================================================================
         SUBROUTINE SSEN(TILA,XSM,YSM,ZSEN,RMP,IE)
C FIND THE POSITION OF SEN(Standard Equatorial-Neutral) SHEET ALONG ZSM AXIS
C  (ZSEN), THE RADIUS OF THE CROSS SECTION OF THE MAGNETOPAUSE (RMP) FOR
C  DIFFERENT XSM,YSM AND TILA(Tilt Angle) AND SHOW WHETHER SEN IS INSIDE THE
C  MAGNETOPAUSE OR NOT. WHERE:
C  IE=1: IS INSIDE THE MAGNETOPAUSE, IE=2: IS OUTSIDE THE MAGNETOPAUSE
C THE RADIUS OF THE CROSS SECTION OF THE MAGNETOPAUSE IS DETERMINED BY THE
C  MAGNETOPAUSE MODEL OF SIBECK ET AL IN:
C  Sibeck, D. G., R. E. Lopez, and R. C. Roelof, Solar wind control of the
C  magnetopause shape, location, and motion, J. Grophys. Res., 96, 5489, 1991
C INPUT XSM,YSM,TILA(Degree)
C OUTPUT ZSEN,RMP,IE

* INITIAL PARAMETERS
         IE=1
         H=10.5
         TIL=TILA*3.1416/180
         ATIL=ABS(TIL)
         IF(XSM.GE.0) GOTO 101
         YM2=H*(H-XSM/COS(TIL))
         IF(YM2.LT.0) THEN
          IE=2
          RETURN
         ENDIF
         YM=SQRT(YM2)
* Determine the Equatorial Region
         XD2=((H*COS(TIL))**2)*(1-(YSM/H)**2)
         IF(ABS(YSM).GE.H) XD2=0
         RD=SQRT(XD2+YSM**2)
         RSM=SQRT(XSM**2+YSM**2)
* Find EN using 3 different Equations in 3 different Regions
 101     IF(XSM.GE.0.OR.RSM.LE.RD) THEN
          ZSEN=-XSM*SIN(TIL)/COS(TIL)
          GOTO 100
         ENDIF
         IF(ABS(YSM).GT.YM) THEN
          ZSEN=0
          GOTO 100
         ENDIF
         ZSEN=(H*(1-(YSM**2)/YM2))*SIN(TIL)
* Find whether the SEN surface is in the Magnetopause or not
 100     RP=SQRT(YSM**2+ZSEN**2)
         CALL SMPF(XSM,RMP,IM)
         IF(RP.GT.RMP.OR.IM.EQ.9999.99) IE=2
         RETURN
         END

C     ================================================================
C     SUBROUTINE SDEN - Displaced Equatorial Neutral sheet
C     ================================================================
         SUBROUTINE SDEN(TILA,XSM,YSM,ZDEN,RMP,IE)
C FIND THE POSITION OF DEN(Displaced Equatorial-Neutral) SHEET ALONG ZSM AXIS
C  (ZDEN), THE RADIUS OF THE CROSS SECTION OF THE MAGNETOPAUSE (RMP) FOR
C  DIFFERENT XSM,YSM AND TILA(Tilt Angle) AND SHOW WHETHER DEN IS INSIDE THE
C  MAGNETOPAUSE OR NOT. WHERE:
C  IE=1: IS INSIDE THE MAGNETOPAUSE, IE=2: IS OUTSIDE THE MAGNETOPAUSE
C THE RADIUS OF THE CROSS SECTION OF THE MAGNETOPAUSE IS DETERMINED BY THE
C  MAGNETOPAUSE MODEL OF SIBECK ET AL IN:
C  Sibeck, D. G., R. E. Lopez, and R. C. Roelof, Solar wind control of the
C  magnetopause shape, location, and motion, J. Grophys. Res., 96, 5489, 1991
C INPUT XSM,YSM,TILA(Degree)
C OUTPUT ZDEN,RMP,IE

* INITIAL PARAMETERS
         IE=1
         H=10.5
         H1=10.05
         TIL=TILA*3.1416/180
         ATIL=ABS(TIL)
         IF(XSM.GE.0) GOTO 101
         CALL SD1(TIL,H,H1,XSM,D)
         YM21=((H1*(H+D))**2)*(1-(XSM/(H*COS(TIL)))**2)
         YM22=(H+D)**2-(D-XSM/COS(TIL))**2
         YM2=YM21/YM22
         IF(YM2.LT.0) THEN
          IE=2
          RETURN
         ENDIF
         YM=SQRT(YM2)
         XD2=((H*COS(TIL))**2)*(1-(YSM/H1)**2)
         IF(ABS(YSM).GE.H1) XD2=0
* Find the Equatorial Region
         XD=SQRT(XD2)
         RD=SQRT(XD**2+YSM**2)
         RSM=SQRT(XSM**2+YSM**2)
* Find DEN from 3 different equations in 3 different regions
 101     IF(XSM.GE.0.OR.RSM.LE.RD) THEN
          ZDEN=-XSM*SIN(TIL)/COS(TIL)
          GOTO 100
         ENDIF
         IF(ABS(YSM).GT.YM) THEN
          ZDEN=-D*SIN(TIL)
          GOTO 100
         ENDIF
         ZDEN=((H+D)*SQRT(1-(YSM**2)/YM2)-D)*SIN(TIL)
* Find whether the DEN surface is in the Magnetopause or not
 100     RP=SQRT(YSM**2+ZDEN**2)
         CALL SMPF(XSM,RMP,IM)
         IF(RP.GT.RMP.OR.IM.EQ.9999.99) IE=2
         RETURN
         END

C     ================================================================
C     SUBROUTINE SD1 - Displaced parameter D for DEN model
C     ================================================================
         SUBROUTINE SD1(TIL,H,H1,XSM,D)
C FIND THE DISPLACED PARAMETER D OF THE DISPLACED NEUTRAL SHEET MODEL, SO THAT
C  IT PROVIDES APPROXIMATELY EQUAL CROSS-SECTIONAL AREAS ABOVE AND BELOW THE
C  NEUTRAL SHEET
C INPUT=TIL,H,H1,XSM    OUTPUT=D
         PAI=3.1416
         CT=COS(TIL)
         XX=XSM
         XH=-H*CT
         IF(XSM.GE.XH) XX=XH
* Radius of the cross-section of Olson's Magnetopause Model
         IF(XX.LE.-5.) RM=9*(10-3*XX)/(10-XX)+3
         IF(XX.GT.-5.) RM=SQRT(18**2-(XX+5)**2)
         RM2=RM**2
* If the cross-section areas above & below the Neutral Sheet are approxi-
* mately equal, then D satified: D**4+AA*D**3+BB*D**2+CC*D+DD=0. Where
         AA=4*H-(32*RM2*H**2)/(PAI**2*H1**2*(H-XX/CT))
         BB=2*H**2*(3-8*RM2/(PAI**2*H1**2))
         CC=4*(H**3)
         DD=H**4
         CALL SFA4(AA,BB,CC,DD,X)
         IF(XSM.GE.XH) THEN
          FK=-X/SQRT(-XH)
          D=-FK*SQRT(-XSM)
          RETURN
         ENDIF
         D=X
         RETURN
         END

C     ================================================================
C     SUBROUTINE SFA4 - Quartic equation root finder
C     ================================================================
         SUBROUTINE SFA4(AA,BB,CC,DD,X)
C FIND THE ROOT OF X**4+AA*X**3+BB*X**2+CC*X+DD=0
C INITIAL PARAMETER
         NDX=0
         XMIN=0
         XMAX=50
         NDXMAX=3
         DX=1
         X=XMIN
         YY=X**4+AA*X**3+BB*X**2+CC*X+DD
 100     X=X+DX
         IF(NDX.GT.NDXMAX.OR.X.GE.XMAX) THEN
          NDX=0
          RETURN
         ENDIF
         Y=X**4+AA*X**3+BB*X**2+CC*X+DD
         RY=Y/YY
         IF(RY.LT.0) THEN
C THIS MEANS THAT Y.LE.0 AND YY.GT.0 OR Y.GT.0.AND
C       YY.LE.0, IN THIS CASE DX CHANGE TO ITS HIGHER ORDER
          X=X-DX
          DX=DX/10.
          NDX=NDX+1
          GOTO 100
         ENDIF
         YY=Y
         GOTO 100
         RETURN
         END
