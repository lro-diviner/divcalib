*******************************************************************************
c  PROGRAM: pmcsalbedo
c
c  PURPOSE: This program calculates lambert albedo from mcs channel 6 radiance and geometery
c and creates a new column titled lambert_albedo

c  REQUIRED KEYWORDS: 
c
c       rad=char  -- The column containing the MCS radance to turn into lambert albedo
c
c       inc=char  -- The column containing the solar incidence angle
c
c       dau=char -- the column containing mars-sun distance (in AU)

c  OPTIONAL KEYWORDS:
c
c       des=char -- The descriptor file to describe the format and the
c                    fields of each record of the input data
c                    (the default is the previous pipe).
c
c  EXAMPLE:
c
c   pmcsalbedo rad=radiance inc=incidence dau=dau <data.mcs_35 > data.mcs_36
c
c*******************************************************************************


        program pmcsalbedo
        implicit none
        include 'pipe1.inc'
        character*80 desfile
        character*48 radparam,incparam,dauparam,junk
        integer*4 radparmcol,incparmcol,dauparmcol
        real*8 lamalb,pi
        integer*4 ios,iunit,ndeslines,ifound

        pi=dacos(-1.d0)

        call getcmdchar('rad',1,'required',ifound, radparam)
        call getcmdchar('inc',1,'required',ifound, incparam)
        call getcmdchar('dau',1,'required',ifound, dauparam)

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

        call findcol(radparam,cdesstitle,ndeslines, radparmcol)
        call findcol(incparam,cdesstitle,ndeslines, incparmcol)
        call findcol(dauparam,cdesstitle,ndeslines, dauparmcol)

        write (0,*) 'radparmcol,incparmcol,dauparmcol ',
     & radparmcol, incparmcol, dauparmcol

       call adddesline(ndeslines+1,'lambert_albedo',
     &       'lambert_albedo', cdesheader,
     &       cdesstitle,cdesltitle,
     &       ndeslines)

       write (0,*) 'added desline'
c
c  send new descriptor file down pipe
          call pdeswrite(6, cdesname, cdesheader, cdesstitle,
     &               cdesltitle, ndeslines)
c        write (0,*) 'new ndeslines= ',ndeslines,idesrecl
          
          write (0,*) 'wrote descriptor file '

c check command line for bogus key words
        call chkcmdkey('bogus')
10           ios = read5(rdat, ndeslines-1)
          if( ios .eq. -1 ) goto 999
          
          lamalb=rdat(radparmcol)*rdat(dauparmcol)**2
     & /cos(pi*rdat(incparmcol)/180.) 

      rdat(ndeslines)=lamalb

        ios =  write6(rdat, ndeslines)
        goto 10
 999         continue
        endfile ( unit=6)
        ios=close5()

        stop
        end


