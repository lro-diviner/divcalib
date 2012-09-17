c**************************************************************
c PBIN3D: -- A three-dimensional binning program that computes
c            the count, average, sigma, min and max for each bin.
c
c
c Required Keywords:
c
c      x=char -- The first independent variable that defines the 
c                range of each bin.
c      y=char -- The second independent variable that defines the 
c                range of each bin.
c      z=char -- The third independent variable that defines the 
c                range of each bin.
c      t=char -- The dependent variable that is dropped into
c                the bins.
c
c
c  xrange=double,double -- The range of values you want to
c                bin, where the first is the minimum and the 
c                second is the maximum. 
c
c  deltax=double -- The increment of the bins.
c
c  yrange=double,double -- The range of values you want to
c                bin, where the first is the minimum and the 
c                second is the maximum. 
c
c  deltay=double -- The increment of the bins.
c
c  zrange=double,double -- The range of values you want to
c                bin, where the first is the minimum and the 
c                second is the maximum. 
c
c  deltaz=double -- The increment of the bins.
c
c Optional Keywords:
c
c    des=char -- Descriptor file (default is previous pipe).
c
c     sparse -- ounly output if count in all Z bins are > 0
c
c     table -- outputs in tabular output with z avg values across the page
c
c     exclude -- outputs this value if the count in a bin is zero

c
c Output:
c
c Ascii file containing bin center values and results, with zeros for empty bins:
c
c      xcenter,ycenter,zcenter,taverage,tcount,tsigma,tmin,tmax
c
c                                             Mark Sullivan
c                                             Dec 20, 1993
c                                             David Paige
c                                             July 7, 2007
c**************************************************************

        program pbin3dsparse

        implicit none
        include 'pipe1.inc'
  
   
        integer nbinx,nbiny,nbinz
        integer ifound

        real*8    xrange(2),xmin,xmax,xlen
        real*8    yrange(2),ymin,ymax,ylen
        real*8    zrange(2),zmin,zmax,zlen
        real*8    deltax,deltay,deltaz
        real*8    sum,sumsq,avg,sigma,cnt,exclude
        real*8    min,max
        integer*4 isparse,ititles,itable,iexclude

        integer*8 nbinxyz
        real*8    arrsize,totsize

        character*80 junk

        integer pbin3dhelp ! A C subprogram
        data isparse/0/,ititles/0/,itable/0/

        write(0,*) '--- pbin3dsparse Main Program'

c sparse mode, titles and table

        call getcmdchar('sparse',0,'optional',ifound,junk)
        if (ifound.eq.1) isparse=1
        write (0,*) 'isparse=1'

        call getcmdchar('titles',0,'optional',ifound,junk)
        if (ifound.eq.1) ititles=1
        write(0,*) 'ititles = ',ititles

        call getcmdchar('table',0,'optional',ifound,junk)
        if (ifound.eq.1) itable=1
        write(0,*) 'itable = ',itable

        call getcmdreal('exclude',1,'optional',ifound, exclude)
        iexclude=0
        if (ifound.eq.1) iexclude=1

c X variable

        call getcmdreal('xrange',2,'required',ifound, xrange)
        if(xrange(1).gt.xrange(2)) then
           xmin = xrange(2)
           xmax = xrange(1)
        else
           xmin = xrange(1)
           xmax = xrange(2)
        endif

        call getcmdreal('deltax',1,'required',ifound, deltax)

        xlen = xmax - xmin

        nbinx = nint(xlen/deltax)

c Y variable

        call getcmdreal('yrange',2,'required',ifound, yrange)
        if(yrange(1).gt.yrange(2)) then
           ymin = yrange(2)
           ymax = yrange(1)
        else
           ymin = yrange(1)
           ymax = yrange(2)
        endif

        call getcmdreal('deltay',1,'required',ifound, deltay)

        ylen = ymax - ymin

        nbiny = nint(ylen/deltay)

c Z variable

        call getcmdreal('zrange',2,'required',ifound, zrange)
        if(zrange(1).gt.zrange(2)) then
           zmin = zrange(2)
           zmax = zrange(1)
        else
           zmin = zrange(1)
           zmax = zrange(2)
        endif

        call getcmdreal('deltaz',1,'required',ifound, deltaz)

        zlen = zmax - zmin

        nbinz = nint(zlen/deltaz)

c call c helper routine to allocate memory

        write (0,*) 'X: ',nbinx,deltax,xmin,xmax,xlen
        write (0,*) 'Y: ',nbiny,deltay,ymin,ymax,ylen
        write (0,*) 'Z: ',nbinz,deltaz,zmin,zmax,zlen

        nbinxyz = int8(nbinx)*int8(nbiny)*int8(nbinz)
        arrsize = (nbinxyz * 8) / 1.d9
        totsize = arrsize * 7

        write(0,*) 'nx*ny*nz: ',nbinxyz
        write(0,*) 'Array size (GB): ',arrsize
        write(0,*) 'Total size (GB): ',totsize
        if(totsize.gt.64.d0) then
            write(0,*) 'This is likely larger than you have memory'
            write(0,*) 'Exiting...'
            call exit(1)
        endif
        

        write (0,*) 'Calling C...'

        ifound = pbin3dhelp(nbinx,deltax,xmin,xmax,xlen,
     &                      nbiny,deltay,ymin,ymax,ylen,
     &                      nbinz,deltaz,zmin,zmax,zlen,
     &                      isparse,ititles,itable,
     &                      iexclude,exclude)


        stop
        end
           
c*******************************************************************************
c*******************************************************************************
c*******************************************************************************
c*******************************************************************************
c*******************************************************************************
        subroutine makepbin3d(nx,dx,xmin,xmax,xlen,
     &                       ny,dy,ymin,ymax,ylen,
     &                       nz,dz,zmin,zmax,zlen,
     &    sum,sumsq,cnt,avg,sigma,min,max,isparse,ititles,itable,
     &    iexclude,exclude)


        implicit none
        include 'pipe1.inc'

        integer nx,ny,nz
        real*8 dx,dy,dz
        real*8 xmin,xmax,xlen,ymin,ymax,ylen,zmin,zmax,zlen
        real*8 sum(nx,ny,nz),sumsq(nx,ny,nz),cnt(nx,ny,nz)
        real*8 avg(nx,ny,nz),sigma(nx,ny,nz)
	real*8 min(nx,ny,nz),max(nx,ny,nz)
        integer*4 isparse,ititles,itable,iexclude

        character*80 desfile
        integer i,j,k
        integer ifound,iunit,ndeslines,ios

        integer xf,yf,zf,tf
        character*48 xparam,yparam,zparam,tparam
        real*8 xdata,ydata,zdata,tdata
        real*8 r,sqrt,exclude
	real*8 BIG
	data BIG/1.D64/
        integer iprint
c        iexclude=0
c        exclude=-999.0

        write(0,*) ' '
        write(0,*) 'In Fortran function makepbin3d()'
        write(0,*) 'nx,ny,nz: ',nx,ny,nz

c
c check for descriptor file in command line
c
        write (0,*) 'X: ',nx,dx,xmin,xmax,xlen
        write (0,*) 'Y: ',ny,dy,ymin,ymax,ylen
        write (0,*) 'Z: ',nz,dz,zmin,zmax,zlen


        call getcmdchar('des',1,'optional',ifound, desfile)
        if( ifound .eq. 1 ) then
                iunit=7
        else
                iunit=5
        endif
        call pdesread(iunit, desfile,  cdesheader,
     &               cdesstitle,  cdesltitle,
     &               ndeslines)
  
c
c Get the X parameters from the command line
c
        call getcmdchar('x',1,'required',ifound, xparam)
        do i=1,MAXCOL
           if(cdesstitle(i).eq.xparam) then
              xf = i
              goto 20
           endif
        enddo
        stop 'ERROR: x parameter not found in descriptor file'

20      continue

        call getcmdchar('y',1,'required',ifound, yparam)
        do i=1,MAXCOL
           if(cdesstitle(i).eq.yparam) then
              yf = i
              goto 40
           endif
        enddo
        stop 'ERROR: y parameter not found in descriptor file'

40      continue

        call getcmdchar('z',1,'required',ifound, zparam)
        do i=1,MAXCOL
           if(cdesstitle(i).eq.zparam) then
              zf = i
              goto 50
           endif
        enddo
        stop 'ERROR: z parameter not found in descriptor file'

50      continue

        call getcmdchar('t',1,'required',ifound, tparam)
        do i=1,MAXCOL
           if(cdesstitle(i).eq.tparam) then
              tf = i
              goto 60
           endif
        enddo
        stop 'ERROR: t parameter not found in descriptor file'

60      continue



        call chkcmdkey('bogus')

        write(0,*) 'X = ',xparam,' is column ',xf
        write(0,*) 'Y = ',yparam,' is column ',yf
        write(0,*) 'Z = ',zparam,' is column ',zf
        write(0,*) 'T = ',tparam,' is column ',tf
        write(0,*) 'X-Range: ',xmin,xmax,dx
        write(0,*) 'Y-Range: ',ymin,ymax,dy
        write(0,*) 'Z-Range: ',zmin,zmax,dz
        write (0,*) 'isparse = ',isparse
        write (0,*) 'ititles = ',ititles
        write (0,*) 'itable = ',itable
     

c INITIALIZE.
c
        do i=1,nx
           do j=1,ny
              do k=1,nz
                  sum(i,j,k)      = 0.0
                  sumsq(i,j,k)    = 0.0
                  cnt(i,j,k)      = 0.0
                  avg(i,j,k)      = 0.0
                  sigma(i,j,k)    = 0.0
	          min(i,j,k)      =  BIG
	          max(i,j,k)      = -BIG
              enddo
           enddo   
        enddo

        write (0,*) 'Initialized arrays.'
c
c READ IN THE DATA.
c

100     ios = read5(rdat, ndeslines)
        if(ios.eq.-1) goto 300

        xdata = rdat(xf)
        ydata = rdat(yf)
        zdata = rdat(zf)
        tdata = rdat(tf)

        if(xdata.lt.xmin.or.xdata.ge.xmax) goto 100 ! Read new record
        if(ydata.lt.ymin.or.ydata.ge.ymax) goto 100 ! Read new record
        if(zdata.lt.zmin.or.zdata.ge.zmax) goto 100 ! Read new record

c
c Store data in bins   
c

        i =  nx*(xdata-xmin)/xlen + 1
        j =  ny*(ydata-ymin)/ylen + 1
        k =  nz*(zdata-zmin)/zlen + 1


        sum(i,j,k)      = sum(i,j,k) + tdata
        sumsq(i,j,k)    = sumsq(i,j,k) + tdata**2
        cnt(i,j,k)      = cnt(i,j,k) + 1.0
	if(tdata.lt.min(i,j,k)) min(i,j,k) = tdata
	if(tdata.gt.max(i,j,k)) max(i,j,k) = tdata

        goto 100

c
c CALCULATE THE AVERAGE AND STD. DEV. OF EACH BIN
c

300     continue

        ios = close5()

        write (0,*) 'computing averages'
        do i=1,nx
           do j=1,ny
              do k=1,nz
	      !!!!!! min,max
	      if(min(i,j,k).eq.BIG)  min(i,j,k)=0.0
	      if(max(i,j,k).eq.-BIG) max(i,j,k)=0.0
	      !!!!!! avg
              if(cnt(i,j,k).eq.0.0) then
                   avg(i,j,k) = 0.0
                   if (iexclude.eq.1) avg(i,j,k)=-999.
              else
                 avg(i,j,k) = sum(i,j,k) / cnt(i,j,k)
              endif
	      !!!!!! sigma
              if(cnt(i,j,k).le.1.0) then
                 sigma(i,j,k) = 0.0
              else
                 sigma(i,j,k) =  (sumsq(i,j,k)*cnt(i,j,k) - 
     &                            sum(i,j,k)**2) /
     &                       (cnt(i,j,k)*(cnt(i,j,k)-1.0))
              endif
              if(sigma(i,j,k).ge.0.0) then
                 sigma(i,j,k) = sqrt(sigma(i,j,k))
              else
                 sigma(i,j,k) = 0.0
              endif
              enddo
           enddo   
        enddo
c
c OUTPUT DATA
c

c      open (unit=9,file=yparam(1:index(yparam,' ')-1)//
c     &                         '.pbin',status='unknown')

        write (0,*) 'output loop, isparse= ',isparse
        write (0,*) 'ititles= ',ititles
        write (0,*) 'itable= ',itable


       if (itable.eq.1) then
        if (ititles.eq.1) then
           write (*,'(2a20,128f20.8)') 
     & cdesstitle(xf)(1:index(cdesstitle(xf),' ')-1),
     & cdesstitle(yf)(1:index(cdesstitle(yf),' ')-1),
     & (zmin+(k-0.5)*zlen/float(nz),k=1,nz)
        endif   
        do i=1,nx
           do j=1,ny
              iprint=1
              if (isparse.eq.1) then
              do k=1,nz
                 if (cnt(i,j,k).le.0) iprint=0
              enddo
              endif
             if (iprint.eq.1) then
              write (*,800) 
     &                    xmin+(i-.5)*xlen/float(nx),
     &                    ymin+(j-.5)*ylen/float(ny),
     &                    (avg(i,j,k),k=1,nz)
             endif
          enddo
       enddo
      else if (itable.eq.0) then

        if (ititles.eq.1) then
           write (*,'(8a20)') 
     & cdesstitle(xf)(1:index(cdesstitle(xf),' ')-1),
     & cdesstitle(yf)(1:index(cdesstitle(yf),' ')-1),
     & cdesstitle(zf)(1:index(cdesstitle(zf),' ')-1),
     & cdesstitle(tf)(1:index(cdesstitle(tf),' ')-1),
     & ' count',' sigma',' min',' max'
        endif   
        do i=1,nx
           do j=1,ny
              iprint=1
              if (isparse.eq.1) then
              do k=1,nz
                  if (cnt(i,j,k).le.0) iprint=0
              enddo
              endif
             if (iprint.eq.1) then
              ! write(0,*) 'iprint is 1'
              do k=1,nz
              write (*,800) 
     &                    xmin+(i-.5)*xlen/float(nx),
     &                    ymin+(j-.5)*ylen/float(ny),
     &                    zmin+(k-.5)*zlen/float(nz),
     &                    avg(i,j,k),cnt(i,j,k),sigma(i,j,k),
     &                    min(i,j,k),max(i,j,k)
              enddo
             endif
          enddo
       enddo
      endif ! itable endif 

800   format(12f20.8)

      !close (unit=9)

      return
      end
   
