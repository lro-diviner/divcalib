c******************************************************************************
c  PROGRAM: photoangles2
c  PURPOSE: This program calculates phase angle from incidence, emission and
c azimugh angles  
c from incidence angle and visual brightness
c where visual brightness is the ratio between the measured brightness
c and a normally illuminated lambert surface at the same solar distance
c  REQUIRED KEYWORDS: 
c
c       inc=char  -- The column containing the solar incidence angle
c       emis=char -- The column conatining emission angle
c       phase=char -- The column containing solar phase angle

c  OPTIONAL KEYWORDS:
c
c       des=char -- The descriptor file to describe the format and the
c                    fields of each record of the input data
c                    (the default is the previous pipe).
c
c  OUTPUTS:
c     new desfile columns:
c     az -- the azimuth angle
c eventually it will also calculate these angles:
c     ex - the x component of the emission angle
c     ey - the y component of the emiission angle
c     ix - the x compoent of the incidence angle
c     iy - the y component of the incidence angle
c 
c  EXAMPLE:
c
c   cphotoangles inc=cinc emis=cemis az=csunazi
c
c*******************************************************************************


        program photoangles
        implicit none
        include 'pipe1.inc'
        character*80 desfile,junk
        character*48 incparam,emisparam,phaseparam
        integer*4 inccol,emiscol,phasecol
        integer*4 ios,iunit,ndeslines,ifound
        real*8 pi,inc,emis,az,g,ex,ey,ix,iy,phase
        
        pi=dacos(-1.d0)

        call getcmdchar('inc',1,'required',ifound, incparam)
        call getcmdchar('emis',1,'required',ifound, emisparam)
        call getcmdchar('phase',1,'required',ifound, phaseparam)

c check for descriptor file in command line
        call getcmdchar('des',1,'optional',ifound, desfile)

        if( ifound .eq. 1 ) then
c if des found, read from unit 7
                iunit=7
        else
c else, get descriptor from standard input
                iunit=5
        endif
          call pdesread(iunit, desfile,  cdesheader,
     &               cdesstitle,  cdesltitle,
     &               ndeslines)
          
c check for nodes keyword in command line
        call getcmdchar('nodes',0,'optional',ifound, junk)

        call findcol(incparam,cdesstitle,ndeslines, inccol)
        call findcol(emisparam,cdesstitle,ndeslines,emiscol)
        call findcol(phaseparam,cdesstitle,ndeslines,phasecol)

        !write (0,*) 'loncol,latcol ',loncol,latcol

       call adddesline(ndeslines+1,'ix',
     &       'ix', cdesheader,
     &       cdesstitle,cdesltitle,
     &       ndeslines)

       call adddesline(ndeslines+1,'iy',
     &       'iy', cdesheader,
     &       cdesstitle,cdesltitle,
     &       ndeslines)

       call adddesline(ndeslines+1,'ex',
     &       'ex', cdesheader,
     &       cdesstitle,cdesltitle,
     &       ndeslines)

       call adddesline(ndeslines+1,'ey',
     &       'ey', cdesheader,
     &       cdesstitle,cdesltitle,
     &       ndeslines)

       call adddesline(ndeslines+1,'az',
     &       'az', cdesheader,
     &       cdesstitle,cdesltitle,
     &       ndeslines)


       !write (0,*) 'added desline, ndeslines= ',ndeslines

c
c  send new descriptor file down pipe
          call pdeswrite(6, cdesname, cdesheader, cdesstitle,
     &               cdesltitle, ndeslines)
c        write (0,*) 'new ndeslines= ',ndeslines,idesrecl
          
          !write (0,*) 'wrote descriptor file '

c check command line for bogus key words
        call chkcmdkey('bogus')
10           ios = read5(rdat, ndeslines-5)
          if( ios .eq. -1 ) goto 999
          

          inc=rdat(inccol)
          emis=rdat(emiscol)
          phase=rdat(phasecol)
c          g=acos(cos(inc*pi/180.)*cos(emis*pi/180.)+
c     & sin(inc*pi/180.)*sin(emis*pi/180.)*cos(az*pi/180.))
c          =acos(cos(inc*pi/180.)*cos(emis*pi/180.)+sin(inc*pi/180.)*sin(emis*pi/180.)*cos(az*pi/180.))
          az=(180./pi)*acos((cos(phase*pi/180.)-
     &                      cos(inc*pi/180.)*cos(emis*pi/180.))
     &                    /(sin(inc*pi/180.)*sin(emis*pi/180.)))
          
          ix=inc
          iy=0.
          rdat(ndeslines-2)=iy
          ex=emis*cos(pi*az/180.)
          ey=emis*sin(pi*az/180.)

          rdat(ndeslines)=az
          rdat(ndeslines-1)=ey
          rdat(ndeslines-2)=ex
          rdat(ndeslines-3)=iy
          rdat(ndeslines-4)=ix

          ios =  write6(rdat, ndeslines)
        goto 10
 999         continue
        endfile ( unit=6)
        ios=close5()

        stop
        end


