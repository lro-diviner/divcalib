C$Procedure DLRE_V2AZEL ( MOON_ME vector to approximate DLRE AZ and EL )

      SUBROUTINE DLRE_XZV2AZEL ( SCX, SCZ, VEC, AZDEG, ELDEG, SUCCSS )

C$ Abstract
C
C     Compute approximate DLRE AZ and EL corresponding to the input
C     given LRO s/c X and Z and DLRE FP_A view vector in the MOON_ME
C     frame
C
C$ Declarations
 
      IMPLICIT              NONE

      DOUBLE PRECISION      SCX    ( 3 )
      DOUBLE PRECISION      SCZ    ( 3 )
      DOUBLE PRECISION      VEC    ( 3 )
      DOUBLE PRECISION      AZDEG
      DOUBLE PRECISION      ELDEG
      LOGICAL               SUCCSS

C$ Brief_I/O
C
C     Variable  I/O  Description
C     --------  ---  --------------------------------------------------
C     SCX        I   LRO s/c X axis in MOON_ME.
C     SCZ        I   LRO s/c Z axis in MOON_ME.
C     VEC        I   Cartesian vector in MOON_ME frame
C     AZDEG      O   Approximate DLRE AZ, degrees.
C     ELDEG      O   Approximate DLRE EL, degrees.
C     SUCCSS     O   Flag indicating that AZ/EL could be computed.
C
C$ Files
C
C     DLRE FK providing data needed to compute the following frame
C     transformations
C
C        LRO_SC_BUS       --> LRO_DLRE_AZI_REF
C        LRO_DLRE_AZI_GIM --> LRO_DLRE_ELV_REF
C        LRO_DLRE_ELV_GIM --> LRO_DLRE_FP_A
C
C     must be loaded prior to calling this routine.
C
C$ Particulars
C
C     AZ and EL computed by this routine are approximate because this
C     implementation takes into account only some of the AZ to EL
C     gimbal and EL gimbal to FPA misalignments. These angles will
C     result in boresight direction pointing error of under a tenth of
C     degrees compared to the full alignment model.
C
C     This routine fetches and saves fixed DLRE frame chain rotations
C     at the first call.
C
C$ Version
C
C-    ALPHA Version 1.0.0, 05-APR-2012 (BVS) 
C
C-&
 
C
C     SPICELIB functions.
C
      DOUBLE PRECISION      DPR
      DOUBLE PRECISION      PI
      DOUBLE PRECISION      HALFPI
      DOUBLE PRECISION      TWOPI

C
C     Local variables.
C
      DOUBLE PRECISION      AZCOR
      DOUBLE PRECISION      DEC
      DOUBLE PRECISION      DROTM0 ( 3, 3 )
      DOUBLE PRECISION      DROTM1 ( 3, 3 )
      DOUBLE PRECISION      DROTM3 ( 3, 3 )
      DOUBLE PRECISION      DROTM5 ( 3, 3 )
      DOUBLE PRECISION      ELCOR1
      DOUBLE PRECISION      ELCOR2
      DOUBLE PRECISION      R
      DOUBLE PRECISION      RA
      DOUBLE PRECISION      ROTX
      DOUBLE PRECISION      ROTZ
      DOUBLE PRECISION      TROT1  ( 3, 3 )
      DOUBLE PRECISION      VEC1   ( 3 )


      LOGICAL               FIRST

C
C     Initial values.
C
      DATA                  FIRST   / .TRUE. /
      
C
C     Save all.
C
      SAVE

C
C     Set SUCCSS to .FALSE.
C
      SUCCSS = .FALSE.

      IF ( FIRST ) THEN

C
C        Compute individual fixed rotations matrices in LRO_DLRE_FP_A
C        -> LRO_SC_BUS chain. Since these are fixed at all times they
C        can be computed at zero ET. Because of the way SPICE builds
C        frame chains we need to compute rotations going the other way
C        first and then transpose them to avoid errors due to 0 ET
C        being outside of the SCLK conversion range.
C
         CALL PXFORM ( 'LRO_DLRE_AZI_REF', 'LRO_SC_BUS',       0.D0, 
     .                                                       DROTM1 )
         CALL XPSGIP ( 3, 3, DROTM1 )

         CALL PXFORM ( 'LRO_DLRE_ELV_REF', 'LRO_DLRE_AZI_GIM', 0.D0, 
     .                                                       DROTM3 )
         CALL XPSGIP ( 3, 3, DROTM3 )

         CALL PXFORM ( 'LRO_DLRE_FP_A',    'LRO_DLRE_ELV_GIM', 0.D0, 
     .                                                       DROTM5 )
         CALL XPSGIP ( 3, 3, DROTM5 )
         
C
C        Decompose DROTM3 and DROTM5 into Euler angles to get small
C        rotations about Z and Y that can be used to slightly improve
C        AZ and EL computed without taking the AZ to EL gimbal and EL
C        gimbal to FPA misalignments.
C
         CALL M2EUL ( DROTM3, 2, 1, 3, ELCOR1, ROTX, AZCOR  )
         CALL M2EUL ( DROTM5, 3, 1, 2, ROTZ,   ROTX, ELCOR2 )

         FIRST = .FALSE.
      
      END IF

C
C     Construct MOON_ME to LRO_SC_BUS rotation based on the input s/c X
C     and Z.
C
      CALL TWOVEC ( SCZ, 3, SCX, 1, DROTM0 )

C
C     Multiply matrices to get rotation from MOON_ME to LRO_DLRE_AZI_REF.
C
      CALL MXM ( DROTM1, DROTM0, TROT1 )

C
C     Rotate input vector from MOON_ME to LRO_DLRE_AZI_REF.
C
      CALL MXV ( TROT1, VEC, VEC1 )

C
C     Convert rotated vector to RA and DEC.
C
      CALL RECRAD( VEC1, R, RA, DEC )

C
C     If DLRE did not have 0..270 gimbal ranges and misalignments
C     between frames, AZ and EL could be simply set to AZ = ( RA - pi )
C     and EL = ( DEC + 1/2 pi ). But because of the range limits and
C     misalignments things are a bit more complicated.
C
C     To get AZ, shift RA by 2pi and AZ correction computed from AZ to
C     EL gimbal misalignment and adjust it to 0..360 range.
C
      RA = RA - PI() - AZCOR

      IF ( RA .LT. 0.D0 ) THEN
         RA = RA + TWOPI()
      END IF

C
C     Compute EL depending on the AZ. If AZ is less than 270, EL is 
C     simply ( DEC + 1/2 pi + corrections ) as mentioned above.
C
      IF ( RA .LE. 3.D0/2.D0 * PI() ) THEN

         AZDEG  =   RA * DPR()
         ELDEG  = ( HALFPI() + DEC - ELCOR1 - ELCOR2 ) * DPR()

         SUCCSS = .TRUE.

      ELSE

C
C        If AZ is greater than 270, EL can be either in the reachable
C        zone (by adjusting AZ by 180 and pushing EL to 180..270
C        range) or unreachable zone.
C
         IF ( ( - DEC - ELCOR1 - ELCOR2 ) .LE. 0.D0  ) THEN

            AZDEG  = ( RA - PI()  ) * DPR()
            ELDEG  = ( 3.D0/2.D0*PI() - DEC - ELCOR1 - ELCOR2 ) * DPR()

            SUCCSS = .TRUE.

         ELSE

C
C           This pointing direction is not reachable. SUCCSS is already
C           set to .FALSE.
C
            
         END IF
         
      END IF

C
C     All done.
C
      RETURN

      END
