c******************************************************************************
c  PROGRAM: pdivrad2bt
c
c  PURPOSE: This program adds columns for brightness temperature calculated from Diviner radiance
c in channels 3-9. The program will add a column bt containing the brightness temperature
c  REQUIRED KEYWORDS: 
c
c       radiance=char  -- The column containing Diviner radiance
c
c       c=c  -- The column containing Diviner channel
c
c  OPTIONAL KEYWORDS:
c
c       des=char -- The descriptor file to describe the format and the
c                    fields of each record of the input data
c                    (the default is the previous pipe).
c
c  EXAMPLE:
c
c   prad2bt radiance=radiance c=c des=div35 < data.div35
c
c*******************************************************************************


        program pdivrad2bt
        implicit none
        include 'pipe1.inc'
        character*80 desfile,junk
        character*48 radianceparam,cparam
        integer*4 radiancecol,ccol
        integer*4 ios,iunit,ndeslines,ifound
        real*8 radiance,c,t(880),rad(880,9),bt
        integer*4 ifirst,ic,i,j
        data ifirst/1/

        call getcmdchar('radiance',1,'required',ifound, radianceparam)
        call getcmdchar('c',1,'required',ifound, cparam)

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

        call findcol(radianceparam,cdesstitle,ndeslines, radiancecol)
        call findcol(cparam,cdesstitle,ndeslines, ccol)

        write (0,*) 'radiancecol,ccol ',radiancecol,ccol

       call adddesline(ndeslines+1,'bt',
     &       'Calculated Brightness Temperature', cdesheader,
     &       cdesstitle,cdesltitle,
     &       ndeslines)

       write (0,*) 'added desline, ndeslines= ',ndeslines


c  send new descriptor file down pipe
          call pdeswrite(6, cdesname, cdesheader, cdesstitle,
     &               cdesltitle, ndeslines)
c        write (0,*) 'new ndeslines= ',ndeslines,idesrecl
          
          write (0,*) 'wrote descriptor file '

c check command line for bogus key words
        call chkcmdkey('bogus')
10           ios = read5(rdat, ndeslines-1)
          if( ios .eq. -1 ) goto 999
c now we do the processing
c read data file if first time
          if (ifirst.eq.1) then
            open 
     & (unit=91,file='/u/paige/dap/pipesv3/t2r.txt',status="old")
            do i=1,880
                read (91,*) t(i),(rad(i,j),j=3,9)
             enddo
             close (unit=91)
             ifirst=0
          endif
          ic=nint(rdat(ccol))
          radiance=rdat(radiancecol)
          call dfindy(rad(1,ic),t,880,radiance, bt)
          rdat(ndeslines)=bt
          ios =  write6(rdat, ndeslines)
        goto 10
 999         continue
        endfile ( unit=6)
        ios=close5()

        stop
        end


