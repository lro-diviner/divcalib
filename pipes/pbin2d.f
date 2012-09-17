c**************************************************************
c PBIN2D: -- A two-dimensional binning program that computes
c            the count, average, sigma, min and max for each bin.
c
c
c Required Keywords:
c
c      x=char -- The first independent variable that defines the 
c                range of each bin.
c      y=char -- The second independent variable that defines the 
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
c      xcenter,ycenter,taverage,tcount,tsigma,tmin,tmax
c
c                                             Jean-Pierre Williams
c                                             July 7, 2011
c
c**************************************************************

        program pbin2d

        implicit none
        include 'pipe1.inc'
  
   
        integer nbinx,nbiny,nbinz
        integer ifound

        real*8    xrange(2),xmin,xmax,xlen
        real*8    yrange(2),ymin,ymax,ylen
        real*8    deltax,deltay
        real*8    sum,sumsq,avg,sigma,cnt
        real*8    min,max
        integer*4 isparse

        integer*8 nbinxyz
        real*8    arrsize,totsize

        character*80 junk

        integer pbin2dhelp ! A C subprogram

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

c call c helper routine to allocate memory

        nbinxyz = int8(nbinx)*int8(nbiny)
        arrsize = (nbinxyz * 8) / 1.d9
        totsize = arrsize * 7

        write(0,*) 'nx*ny: ',nbinxyz
        write(0,*) 'Array size (GB): ',arrsize
        write(0,*) 'Total size (GB): ',totsize
        if(totsize.gt.64.d0) then
            write(0,*) 'This is likely larger than you have memory'
            write(0,*) 'Exiting...'
            call exit(1)
        endif
        
        ifound = pbin2dhelp(nbinx,deltax,xmin,xmax,xlen,
     &                      nbiny,deltay,ymin,ymax,ylen)


        stop
        end
           
c*******************************************************************************
c*******************************************************************************
c*******************************************************************************
c*******************************************************************************
c*******************************************************************************
        subroutine makepbin2d(nx,dx,xmin,xmax,xlen,
     &                       ny,dy,ymin,ymax,ylen,
     &    sum,sum1,sum2,cnt,cnt1,cnt2,avg,avg1,avg2)


        implicit none
        include 'pipe1.inc'

        integer nx,ny
        real*8 dx,dy
        real*8 xmin,xmax,xlen,ymin,ymax,ylen, aa, bb
        real*8 sum(nx,ny),sum1(nx,ny),sum2(nx,ny)
        real*8 cnt(nx,ny),cnt1(nx,ny),cnt2(nx,ny)
        real*8 avg(nx,ny),avg1(nx,ny),avg2(nx,ny)

        character*80 desfile
        integer i,j
        integer ifound,iunit,ndeslines,ios,icrfound

        integer xf,yf,tf
        character*48 xparam,yparam,tparam
        real*8 xdata,ydata,tdata,crparam
        real*8 r,sqrt
        integer iprint
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

        call getcmdchar('t',1,'required',ifound, tparam)
        do i=1,MAXCOL
           if(cdesstitle(i).eq.tparam) then
              tf = i
              goto 60
           endif
        enddo
        stop 'ERROR: t parameter not found in descriptor file'

60      continue

        call getcmdreal('circmax',1,'optional',icrfound, crparam)
        if(icrfound.eq.0) crparam=0.0

C
        call chkcmdkey('bogus')
C
c INITIALIZE.
c
        do i=1,nx
           do j=1,ny
                  sum(i,j)   = 0.0
                  sum1(i,j)  = 0.0
                  sum2(i,j)  = 0.0
                  cnt(i,j)   = 0.0
                  cnt1(i,j)  = 0.0
                  cnt2(i,j)  = 0.0
                  avg(i,j)   = 0.0
                  avg1(i,j)  = 0.0
                  avg2(i,j)  = 0.0
           enddo   
        enddo
c
c READ IN THE DATA.
c

100     ios = read5(rdat, ndeslines)
        if(ios.eq.-1) goto 300

        xdata = rdat(xf)
        ydata = rdat(yf)
        tdata = rdat(tf)

        if(xdata.lt.xmin.or.xdata.ge.xmax) goto 100 ! Read new record
        if(ydata.lt.ymin.or.ydata.ge.ymax) goto 100 ! Read new record

c
c Store data in bins   
c
        i =  nx*(xdata-xmin)/xlen + 1
        j =  ny*(ydata-ymin)/ylen + 1

        if(icrfound.ne.0.) then
           if(tdata.lt.crparam/2.D0) then
             sum1(i,j) = sum1(i,j) + tdata
             cnt1(i,j) = cnt1(i,j) + 1.0
           else
             sum2(i,j) = sum2(i,j) + tdata
             cnt2(i,j) = cnt2(i,j) + 1.0
           endif
        else
           sum(i,j) = sum(i,j) + tdata
           cnt(i,j) = cnt(i,j) + 1.0
        endif

        goto 100

c
c CALCULATE THE AVERAGE AND STD. DEV. OF EACH BIN
c

300     continue

        ios = close5()

        do i=1,nx
           do j=1,ny
              !!!!!! avg
              if(cnt(i,j).eq.0.0) then
                 avg(i,j) = 0.0
              else
                 avg(i,j) = sum(i,j) / cnt(i,j)
              endif
              ! if circular interpolation
              if(cnt1(i,j).ne.0.0.and.cnt2(i,j).eq.0.0)
     &           avg(i,j) = sum1(i,j)/cnt1(i,j)
              if(cnt1(i,j).eq.0.0.and.cnt2(i,j).ne.0.0)
     &           avg(i,j) = sum2(i,j)/cnt2(i,j)
              if(cnt1(i,j).ne.0.0.and.cnt2(i,j).ne.0.0) then
                 avg1(i,j) = sum1(i,j)/cnt1(i,j)
                 avg2(i,j) = sum2(i,j)/cnt2(i,j)
                 aa = avg1(i,j) + crparam - avg2(i,j)
                 bb = avg2(i,j) - avg1(i,j)
                 if(aa.lt.bb) avg1(i,j) = avg1(i,j) + crparam
                 avg(i,j) = (avg1(i,j) + avg2(i,j))/2.D0
                 if(avg(i,j).ge.crparam) avg(i,j)=avg(i,j)-crparam
              endif

           enddo   
        enddo
c
c OUTPUT DATA
c
        write (*,*) "lon", " lat"," z"
       do j=1,ny
         do i=1,nx
             iprint=1
c             if (cnt(i,j).le.0.and.cnt1(i,j).le.0
c     &                          .and.cnt2(i,j).le.0) iprint=0
c             if (iprint.eq.1) then
               write (*,800) 
     &                    xmin+(i-.5)*xlen/float(nx),
     &                    ymin+(j-.5)*ylen/float(ny),
     &                    avg(i,j)
c            endif
          enddo
       enddo

800   format(3f20.8)

      return
      end
