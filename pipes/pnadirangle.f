c******************************************************************************
c  PROGRAM: pnadirangle
c
c  PURPOSE: This program calculates the angle between an instrument's
c           look-vector and the vector to the center of the planet.
c           This results in a new column 'nadirangle' which is passed 
c           down the pipe.
c
c  REQUIRED KEYWORDS: 
c
c       x=char -- The column containing the x-component of the look-vector.
c       y=char -- The column containing the y-component of the look-vector.
c       z=char -- The column containing the z-component of the look-vector.
c
c       lat=char -- The column containing the spacecraft latitude.
c       lon=char -- The column containing the spacecraft east longitude.
c
c  OPTIONAL KEYWORDS:
c
c       des=char -- The descriptor file to describe the format and the
c                    fields of each record of the input data
c                    (the default is the previous pipe).
c
c  EXAMPLE:
c
c  pnadirangle des=div35.des x=vlookx y=vlooky z=vlookz lon=sclon lat=sclat 
c                < data.div35 > data.div36
c
c*******************************************************************************

      program pnadirangle
      implicit none
      include 'pipe1.inc'
      character*80 desfile,junk
      character*48 lonparam,latparam,xparam,yparam,zparam
      integer*4 loncol,latcol,xcol,ycol,zcol
      integer*4 ios,iunit,ndeslines,ifound
      real*8 lon,lat,pi,xlook,ylook,zlook,nadirangle,dot,len1,len2

      real*8 xnad,ynad,znad

      real*8 torad,todeg

      pi = dacos(-1.d0)
      torad = pi / 180.d0
      todeg = 180.d0 / pi

      call getcmdchar('lon',1,'required',ifound, lonparam)
      call getcmdchar('lat',1,'required',ifound, latparam)
      call getcmdchar('x',1,'required',ifound, xparam)
      call getcmdchar('y',1,'required',ifound, yparam)
      call getcmdchar('z',1,'required',ifound, zparam)

c check for descriptor file in command line

      call getcmdchar('des',1,'optional',ifound, desfile)

      if( ifound .eq. 1 ) then
          iunit=7
      else
          iunit=5 ! Standard input.
      endif

      call pdesread(iunit, desfile,  cdesheader,
     &               cdesstitle,  cdesltitle,
     &               ndeslines)
          
c check for nodes keyword in command line

      call getcmdchar('nodes',0,'optional',ifound, junk)

      call findcol(lonparam,cdesstitle,ndeslines, loncol)
      call findcol(latparam,cdesstitle,ndeslines, latcol)
      call findcol(xparam,cdesstitle,ndeslines, xcol)
      call findcol(yparam,cdesstitle,ndeslines, ycol)
      call findcol(zparam,cdesstitle,ndeslines, zcol)

      !write(0,*) 'loncol,latcol ',loncol,latcol
      !write(0,*) 'xcol,ycol,zcol ',xcol,ycol,zcol
        

      call adddesline(ndeslines+1,'nadirangle',
     &       'nadirangle',cdesheader,
     &       cdesstitle,cdesltitle,
     &       ndeslines)

      !write (0,*) 'added desline, ndeslines= ',ndeslines

c  send new descriptor file down pipe

      call pdeswrite(6, cdesname, cdesheader, cdesstitle,
     &               cdesltitle, ndeslines)

      !write (0,*) 'new ndeslines= ',ndeslines,idesrecl
          
c check command line for bogus key words

      call chkcmdkey('bogus')

c Loop through records

10    ios = read5(rdat, ndeslines-1)

      if( ios .eq. -1 ) goto 999
          
      lat=rdat(latcol)
      lon=rdat(loncol)
      xlook=rdat(xcol)
      ylook=rdat(ycol)
      zlook=rdat(zcol)

      ! Compute the nadir vector

      lon = lon*torad
      lat = lat*torad

      xnad = -(cos(lon) * cos(lat))
      ynad = -(sin(lon) * cos(lat))
      znad = -(sin(lat))

      !write(0,*) xlook,ylook,zlook,xnad,ynad,znad

      dot = xlook*xnad + ylook*ynad + zlook*znad
      len1 = dsqrt(xlook**2 + ylook**2 + zlook**2)
      len2 = dsqrt(xnad**2  + ynad**2  + znad**2)
      nadirangle = todeg * acos(dot/(len1*len2))

      rdat(ndeslines)=nadirangle

      ios =  write6(rdat, ndeslines)
      goto 10

c     Done?

 999  continue
      endfile (unit=6)
      ios=close5()

      stop
      end


