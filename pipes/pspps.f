c******************************************************************************
c  PROGRAM: pspps
c
c  PURPOSE: This program adds columns for  south polar steregrphic x and y coordinates given
c latitude and east longitude. The scale of the projection is normalized to a planetary
c radius of 1.0. A spherical planet is assumed. The output columns are titled:
c sppsx for the x coordinate, and sppsy for the y coordinate
c In this projection;
c     0 degrees east longitude is pointing up
c     90 degrees east longitude points to the right
c     180 degrees east longitude points down
c     270 degrees east longitude points to the left

c  REQUIRED KEYWORDS: 
c
c       lon=char  -- The column containing east longitude
c
c       lat=char  -- The column containing latitude
c
c  OPTIONAL KEYWORDS:
c
c       des=char -- The descriptor file to describe the format and the
c                    fields of each record of the input data
c                    (the default is the previous pipe).
c
c  EXAMPLE:
c
c   pspps lon=surflon lat=surflat <data.mcs_35 > data.mcs_37
c
c*******************************************************************************


        program psspps
        implicit none
        include 'pipe1.inc'
        character*80 desfile,junk
        character*48 lonparam,latparam
        integer*4 loncol,latcol
        integer*4 ios,iunit,ndeslines,ifound
        real*8 lon,lat,pi,sppsx,sppsy,rp
        data rp/1.d0/
        pi=dacos(-1.d0)

        call getcmdchar('lon',1,'required',ifound, lonparam)
        call getcmdchar('lat',1,'required',ifound, latparam)

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

        call findcol(lonparam,cdesstitle,ndeslines, loncol)
        call findcol(latparam,cdesstitle,ndeslines, latcol)

        write (0,*) 'loncol,latcol ',loncol,latcol

       call adddesline(ndeslines+1,'sppsx',
     &       'sppsx', cdesheader,
     &       cdesstitle,cdesltitle,
     &       ndeslines)

       write (0,*) 'added desline, ndeslines= ',ndeslines

       call adddesline(ndeslines+1,'sppsy',
     &       'sppsy', cdesheader,
     &       cdesstitle,cdesltitle,
     &       ndeslines)

       write (0,*) 'added desline, ndeslines= ',ndeslines


c
c  send new descriptor file down pipe
          call pdeswrite(6, cdesname, cdesheader, cdesstitle,
     &               cdesltitle, ndeslines)
c        write (0,*) 'new ndeslines= ',ndeslines,idesrecl
          
          write (0,*) 'wrote descriptor file '

c check command line for bogus key words
        call chkcmdkey('bogus')
10           ios = read5(rdat, ndeslines-2)
          if( ios .eq. -1 ) goto 999
          

          lat=rdat(latcol)*pi/180.d0
          lon=rdat(loncol)*pi/180.d0
          sppsx=2*rp*tan(pi/4. + lat/2.)*sin(lon)
          sppsy=2*rp*tan(pi/4. + lat/2.)*cos(lon)
          rdat(ndeslines-1)=sppsx
          rdat(ndeslines)=sppsy
          ios =  write6(rdat, ndeslines)
        goto 10
 999         continue
        endfile ( unit=6)
        ios=close5()

        stop
        end


