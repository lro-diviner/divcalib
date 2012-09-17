c**************************************************************
c PBIN2D: -- A two-dimensional binning program that computes
c            the count, average, sigma, min and max for each bin.
c
c
c Required Keywords:
c
c      x=char -- The independent variable that defines the 
c                range of each bin.
c
c      y=char -- The dependent variable that is dropped into
c                the bins.
c
c  xrange=double,double -- The range of values you want to
c                bin, where the first is the minimum and the 
c                second is the maximum. 
c
c  deltax=double -- The increment of the bins.
c
c Optional Keywords:
c
c    des=char -- Descriptor file (default is previous pipe).
c
c To bin emission values from julian date 3414 to 3450
c with bins of size 5 julian days, type:
c
c > pbin2d des=irtm_18.des x=jdate xrange=3414,3450 deltax=5 y=emis < file.irtm_18 > out
c
c
c                                             Mark Sullivan
c                                             Dec 20, 1993
c**************************************************************

        program pbin1d

        implicit none
        include 'pipe1.inc'
  
   
        integer nbinx
        integer ifound

        real*8    xrange(2),xmin,xmax,xlen
        real*8    deltax
        real*8    sum,sumsq,avg,sigma,cnt
        real*8    min,max

        integer pbin1dhelp ! A C subprogram

        !pointer (sumptr,sum)
        !pointer (sumsqptr,sumsq)
        !pointer (cntptr,cnt)
        !pointer (avgptr,avg)
        !pointer (sigmaptr,sigma)
        !pointer (minptr,min)
        !pointer (maxptr,max)


c
c ALLOCATE MEMORY FOR THE BINS
c

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

        ifound = pbin1dhelp(nbinx,deltax,xmin,xmax,xlen)

        stop
        end
           
c        sumptr      = malloc(nbinx*4)
c        sumsqptr    = malloc(nbinx*4)
c        cntptr      = malloc(nbinx*4)
c        avgptr      = malloc(nbinx*4)
c        sigmaptr    = malloc(nbinx*4)
c        minptr      = malloc(nbinx*4)
c        maxptr      = malloc(nbinx*4)
c
cc
cc READ IN THE RECORDS AND STORE THE DATA
cc
c
c
c        call makepbin2d(desfile,nbinx,deltax,
c     &                     xmin,xmax,xlen,
c     &                     sum,sumsq,cnt,avg,sigma,
c     &                     min,max)
c
c
c        stop
c        end

c*******************************************************************************
c*******************************************************************************
c*******************************************************************************
c*******************************************************************************
c*******************************************************************************
        subroutine makepbin1d(nx,dx,xmin,xmax,xlen,
     &                 sum,sumsq,cnt,avg,sigma,min,max)


        implicit none
        include 'pipe1.inc'

        integer nx
        real*8 dx
        real*8 xmin,xmax,xlen
        real*8 sum(nx),sumsq(nx),cnt(nx),avg(nx),sigma(nx)
	real*8 min(nx),max(nx)
  
        character*80 desfile
        integer i
        integer ifound,iunit,ndeslines,ios

        integer xparamcol,yparamcol
        character*48 xparam,yparam
        real*8 xdata,ydata
        real*8 r,sqrt
	real*8 BIG
	data BIG/1.D64/

        !write(0,*) 'Back in fortran: ',nx
        !stop




c
c check for descriptor file in command line
c
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
              xparamcol = i
              goto 20
           endif
        enddo
        stop 'ERROR: x parameter not found in descriptor file'

20      continue

        call getcmdchar('y',1,'required',ifound, yparam)
        do i=1,MAXCOL
           if(cdesstitle(i).eq.yparam) then
              yparamcol = i
              goto 40
           endif
        enddo
        stop 'ERROR: y parameter not found in descriptor file'

40      continue
        call chkcmdkey('bogus')

        write(0,*) 'X = ',xparam,' is column ',xparamcol
        write(0,*) 'Y = ',yparam,' is column ',yparamcol
        write(0,*) 'X-Range: ',xmin,xmax
        write(0,*) 'At increments of ',dx

c
c INITIALIZE.
c
        do i=1,nx
              sum(i)      = 0.0
              sumsq(i)    = 0.0
              cnt(i)      = 0.0
              avg(i)      = 0.0
              sigma(i)    = 0.0
	      min(i)      =  BIG
	      max(i)      = -BIG
        enddo

c
c READ IN THE DATA.
c

50      ios = read5(rdat, ndeslines)
        if(ios.eq.-1) goto 300

        xdata = rdat(xparamcol)
        ydata = rdat(yparamcol)

        if(xdata.lt.xmin.or.xdata.ge.xmax) goto 50 ! Read new record

c
c Store data in bins   
c

        i =  nx*(xdata-xmin)/xlen + 1

        sum(i)      = sum(i) + ydata
        sumsq(i)    = sumsq(i) + ydata**2
        cnt(i)      = cnt(i) + 1.0
	if(ydata.lt.min(i)) min(i) = ydata
	if(ydata.gt.max(i)) max(i) = ydata

        goto 50

c
c CALCULATE THE AVERAGE AND STD. DEV. OF EACH BIN
c

300     continue

        ios = close5()
  
        do i=1,nx
	      !!!!!! min,max
	      if(min(i).eq.BIG)  min(i)=0.0
	      if(max(i).eq.-BIG) max(i)=0.0
	      !!!!!! avg
              if(cnt(i).eq.0.0) then
                 avg(i) = 0.0
              else
                 avg(i) = sum(i) / cnt(i)
              endif
	      !!!!!! sigma
              if(cnt(i).le.1.0) then
                 sigma(i) = 0.0
              else
                 sigma(i) =  (sumsq(i)*cnt(i) - sum(i)**2) /
     &                       (cnt(i)*(cnt(i)-1.0))
              endif
              if(sigma(i).ge.0.0) then
                 sigma(i) = sqrt(sigma(i))
              else
                 sigma(i) = 0.0
              endif
        enddo
c
c OUTPUT DATA
c

c      open (unit=9,file=yparam(1:index(yparam,' ')-1)//
c     &                         '.pbin',status='unknown')

c      write(*,*) 'Histogram for ',yparam(1:index(yparam,' ')-1),
c     &           ' values.'

c      write(*,*)
c      write(*,700) xparam,
c     &             '       Count',
c     &             '         Avg',
c     &             '       Sigma',
c     &             '         Min',
c     &             '         Max'
700   format(6(a12))

c      write(*,702) '------------------------',
c     &             '------------------------',
c     &             '------------------------'
702   format(3(a24))

      r = xmin + dx/2.

      do i=1,nx
         write(*,800) r,nint(cnt(i)),avg(i),sigma(i),min(i),max(i)
         r = r + dx
      enddo
800   format(f16.6,i12,4(f16.6))

      !close (unit=9)

      return
      end
   
