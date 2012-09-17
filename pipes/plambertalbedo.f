c******************************************************************************
c  PROGRAM: plambertalbedo
c
c  PURPOSE: This program calculates lambert albedoes 
c from incidence angle and visual brightness
c where visual brightness is the ratio between the measured brightness
c and a normally illuminated lambert surface at the same solar distance
c  REQUIRED KEYWORDS: 
c
c       inc=char  -- The column containing the solar incidence angle
c
c       vb=char  -- The column containing the visual brightness
c
c  OPTIONAL KEYWORDS:
c
c       des=char -- The descriptor file to describe the format and the
c                    fields of each record of the input data
c                    (the default is the previous pipe).
c
c  OUTPUTS:
c     new desfile column al, the lambert albedo
c     al=0 if the incidence angle is out of range (kluge for now)
c  EXAMPLE:
c
c   plambertalbedo inc=tinc vb=tb 
c
c*******************************************************************************


        program plambertalbedo
        implicit none
        include 'pipe1.inc'
        character*80 desfile,junk
        character*48 incparam,vbparam
        integer*4 inccol,vbcol
        integer*4 ios,iunit,ndeslines,ifound
        real*8 pi,inc,vb,al,ainc
        
        pi=dacos(-1.d0)

        call getcmdchar('inc',1,'required',ifound, incparam)
        call getcmdchar('vb',1,'required',ifound, vbparam)

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
        call findcol(vbparam,cdesstitle,ndeslines, vbcol)

        !write (0,*) 'loncol,latcol ',loncol,latcol

       call adddesline(ndeslines+1,'al',
     &       'al', cdesheader,
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
10           ios = read5(rdat, ndeslines-1)
          if( ios .eq. -1 ) goto 999
          

          inc=rdat(inccol)
          vb=rdat(vbcol)
          ainc=inc*pi/180.
          if (inc.lt.90) then
             al=0.001*vb/cos(ainc)
          else
             al=0
          endif
          rdat(ndeslines)=al
          ios =  write6(rdat, ndeslines)
        goto 10
 999         continue
        endfile ( unit=6)
        ios=close5()

        stop
        end


