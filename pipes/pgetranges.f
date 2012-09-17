C*******************************************************************************
C  PROGRAM: pget_quad.f  (Same as pgetranges, but for really large datasets).
c           WORKS MUCH SLOWER THAN PGETRANGES DUE TO REAL*8 PRECISION.
c
C  PURPOSE: Output the minimum and maximum values of all the variables in an
c           irtm file.  And other cool stats.
C
c  REQUIRED KEYWORDS: 
c
c
c  OPTIONAL KEYWORDS:
c
c           des=char    -- The descriptor filename.
c
c  EXAMPLE:
c
c           > pgetranges des=irtm_18.des < 3414to3416.irtm_18 > 3414to3416.ranges
c
c
c
c                                                          Mark Sullivan
c                                                          1993 September 10
c
C@******************************************************************************

        program pgetranges

        implicit none

        include 'pipe1.inc'
  
        integer*4 i,ifound,iunit,ndeslines,ios
        integer*4 n
        character*80 desfile
        

        real*8 min(MAXCOL),max(MAXCOL),sum(MAXCOL),avg(MAXCOL)
        real*8 sumsq(MAXCOL),sigma(MAXCOL),qdat,gigantic,miniscule
        data gigantic/1.d64/,miniscule/1.d-64/

c
c check for descriptor file in command line

c
        call getcmdchar('des',1,'optional',ifound, desfile)
        if( ifound .eq. 1 ) then
                iunit=7
        else
                iunit=5
        endif
        call pdesread(iunit, desfile, cdesheader,  
     &               cdesstitle,  cdesltitle,
     &               ndeslines)

       call chkcmdkey('bogus')


c
c Initialize all the Minimum and Maximum values. 
c
       do i=1,ndeslines
          min(i) = (1.D307)
          max(i) = (-1.D307)
          sum(i) = 0.0d0
          sumsq(i) = 0.0d0
       enddo

       n = 0

c
c HERE IS WHERE WE READ IN THE RECORDS
c


100     ios = read5(rdat, ndeslines)
        if( ios .eq. -1 ) goto 500 

        n = n + 1

        do i=1,ndeslines
	   qdat = (rdat(i))
c           write (0,'(2f20.10)') rdat(i),qdat
           sum(i) = sum(i) + qdat
           sumsq(i) = sumsq(i) + qdat**2
           if (sumsq(i).gt.gigantic) write (0,*) 
     & 'warning in pgetranges, sums of squares too large in column ',
     & cdesstitle(i) 
c           if (sumsq(i).lt.miniscule) write (0,*) 
c     & 'warning in pgetranges, sums of squares too small in column ',
c     & cdesstitle(i)
           call setrange(qdat, min(i),max(i))
        enddo

        goto 100

500     ios = close5()

c
c NOW WE DISPLAY THE STATISTICS. 
c

        do i=1,ndeslines
           avg(i) = sum(i) / n
           if(n.gt.1) then
              sigma(i) = (sumsq(i) - n*(avg(i)**2)) / (n-1)
              if(sigma(i).ge.0.0) then
                 sigma(i) = dsqrt(sigma(i))
              else
                 sigma(i) = 0.0
              endif
           endif
        enddo

        write(6,400) 'NUMBER OF DATA POINTS: ',n
400     format(a23,i16)

        write(6,499) 'TITLE                        MIN'//
     +                         '                   MAX'//
     +                         '                   AVG'//
     +                         '                 SIGMA'//
     +                         '       100 * SIGMA/AVG'
        write(6,499) '----------------------------------'//
     +                         '------------------------'//
     +                         '------------------------'//
     +                         '------------------------'//
     +                         '------------------------'
499     format(a120)

        do i=1,ndeslines
	   if(dabs(min(i)).gt.1E10.or.
     +        dabs(max(i)).gt.1E10.or.
     +        dabs(avg(i)).gt.1E10.or.
     +        dabs(sigma(i)).gt.1E10)   then
              write(6,554) cdesstitle(i),min(i),max(i),avg(i),sigma(i)
     &             ,abs(100*sigma(i)/avg(i))
           else
              write(6,555) cdesstitle(i),min(i),max(i),avg(i),sigma(i)
     &             ,abs(100*sigma(i)/avg(i))
           endif
        enddo

554     format(a8,2x,5(10x,E12.4))
555     format(a8,2x,5f22.4)

        stop
        end



c**********************************************************************
c SETRANGE: Sets the minimum and maximum values given a value.        *
c**********************************************************************
        subroutine setrange(value, min,max)
        
        implicit none
        real*8 value,min,max

        if(value.lt.min) min = value
        if(value.gt.max) max = value

        return
        end

