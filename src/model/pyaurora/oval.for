
	subroutine oval(xmlt,iql,pcgl,ecgl)
C --------------------------------------------------------------------
C computes Feldstein ovals using the Holzworth&Meng parameterization
C
C input:	XMLT	magnetic local time in hours
C		IQL	level of magnetic activity from 0 (quiet)
C			to active (6)
C output:	PCGL	corrected geomagnetic latitude of poleward
C			boundary
C		ECGL	corr. geom. lat. of equatorward boundary
C --------------------------------------------------------------------- 

	dimension	A1(7),A2(7),A3(7),a4(7),a5(7),a6(7),a7(7),
     &			b1(7),b2(7),b3(7),b4(7),b5(7),b6(7),b7(7)
	data	a1/15.22,15.85,16.09,16.16,16.29,16.44,16.71/,
     &		a2/2.41,2.7,2.51,1.92,1.41,0.81,0.37/,
     &		a3/3.34,3.32,3.27,3.14,3.06,2.99,2.9/,
     &		a4/-0.85,-0.67,-0.56,-0.46,-.09,.14,.63/,
     &		a5/1.01,1.15,1.3,1.43,1.35,1.25,1.59/,
     &		a6/.32,.49,.42,.32,.4,.48,.6/,
     &		a7/.9,1.,.94,.96,1.03,1.05,1./
	data	b1/17.36,18.66,19.73,20.63,21.56,22.32,23.18/,
     &		b2/3.03,3.9,4.69,4.95,4.93,4.96,4.85/,
     &		b3/3.46,3.37,3.34,3.31,3.31,3.29,3.34/,
     &		b4/.42,.16,-.57,-.66,-.44,-.39,-.38/,
     &		b5/2.11,2.55,-1.41,-1.28,-.81,-.72,-.62/,
     &		b6/-.25,-.13,-.07,.3,-.07,-.16,-.53/,
     &		b7/1.13,.96,.75,-.58,-.75,-.52,-.16/

	PI = atan(1.) * 4.0
	umr = PI / 180.
	iq = iql+1
	PHI = XMLT *15.

	z=a1(iq)+a2(iq)*cos(umr*(phi+a3(iq)))+
     &		a4(iq)*cos(2.*umr*(phi+a5(iq)))+
     &		a6(iq)*cos(3.*umr*(phi+a7(iq)))
	pcgl=90.-z

	y=b1(iq)+b2(iq)*cos(umr*(phi+b3(iq)))+
     &		b4(iq)*cos(2.*umr*(phi+b5(iq)))+
     &		b6(iq)*cos(3.*umr*(phi+b7(iq)))
	ecgl=90.-y
	return
	end
