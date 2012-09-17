C*******************************************************************************
C  PROGRAM: pcons
c
C  PURPOSE: outputs histograms of specified column names into multiple files
c
C
c  REQUIRED KEYWORDS: none
c
c  OPTIONAL KEYWORDSS:
c
c       col_name=real(1),real(2),real(3)
c
c               col_name is the short title of a column
c               real(1) is the histogram start point
c               real(2) is the histogram end point
c               real(3) is the histogram bin size
c
c               output histogram files have two columns, the first is
c               the mean value of the histogram bin, the second is
c               the number of counts in each bin.
c
c               output histogram filenames are col_name.his
c
cc
c       des=char  -- the descriptor file to describe the format and the
c                   fields of each record of the input data
c                    (the default is the previous pipe)
c
c        update=int  --  how often you want the histogram files updated
c
c      suffix=char  -  suffex used for histogram files (default is .his)
c
c
c
C  EXAMPLE:
c
c       phist des=irtm_18.des update=1000 lat=-90.,90.,10 hour=0.,24.,1. <test.dat
c
c       phist will make two histograms, one of latitude from -90 to +90
c       in increments of 10 degrees called lat.his, and one of hour
c       from 0 to 24 in increments of 1 hour called hour.his.  The histogram
c       files will be rewritten once every 1000 input records
c
c
C@******************************************************************************


        program phist
c
c  Variable declaration of variables common to all pipes
c
        include 'pipe1.inc'
        parameter (IHISTMAX=1000)

        character*80 desfile,junk
        integer*4 idescol(MAXCOL)
        real*8 vals(3,MAXCOL)
        integer ihist(IHISTMAX,MAXCOL)
        character*20 suffex
        real*8 dat

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
        call getcmdreals(cdesstitle,ndeslines,3, nhist,idescol,vals)
        iupdate=0
        call getcmdint('update',1,'optional',ifound, iupdate)
        suffex='.his'
        call getcmdchar('suffex',1,'optional',ifound, suffex)

c check command line for bogus key words
        call chkcmdkey('bogus')

10      ios = read5(rdat, ndeslines)
        if( ios .eq. -1 ) goto 999
        do i = 1, nhist
c get data from input array
           dat=rdat(idescol(i))
c        write (0,*) 'i= ',i,' dat= ',dat
           if (dat.ge.vals(1,i).and.dat.lt.vals(2,i)) then
c increment appropriate histogram bin
                ibin=(dat-vals(1,i))/vals(3,i) +1
                ihist(ibin,i)=ihist(ibin,i)+1
c        write (0,*) 'ibin= ',ibin,' ihist(ibin,i)= ',ihist(ibin,i)
           endif
        enddo
        nout=nout+1
       if (iupdate.gt.0.and.mod(nout,iupdate).eq.0) then
c write out histogram arrays
        do i=1,nhist
           write (0,*) 'opening file ',
     &cdesstitle(idescol(i))
     & (1:index(cdesstitle(idescol(i)),' ')-1)//suffex

                open (unit=1,file=
     &cdesstitle(idescol(i))
     & (1:index(cdesstitle(idescol(i)),' ')-1)//suffex
     &, status= 'unknown')
                jmax=(vals(2,i)-vals(1,i))/vals(3,i)
                do j=1,jmax
                        write (1,'(3g12.5,i12)')
     & vals(1,i)+(j-1)*vals(3,i),vals(1,i)+(j)*vals(3,i),
     & ((vals(1,i)+(j-1)*vals(3,i))+(vals(1,i)+(j)*vals(3,i)))/2,
     & ihist(j,i)
                enddo
                close (unit=1)
        enddo
       endif
c done writing histogram arrays
c go back and read some more data
        goto 10
999     continue
c now write out histogram arrays
        do i=1,nhist
                open (unit=1,file=
     &cdesstitle(idescol(i))
     & (1:index(cdesstitle(idescol(i)),' ')-1)//suffex
     &, status= 'unknown')
                jmax=(vals(2,i)-vals(1,i))/vals(3,i)
                do j=1,jmax
                        write (1,'(3g12.5,i12)')
     & vals(1,i)+(j-1)*vals(3,i),vals(1,i)+(j)*vals(3,i),
     & ((vals(1,i)+(j-1)*vals(3,i))+(vals(1,i)+(j)*vals(3,i)))/2,
     & ihist(j,i)
                enddo
                close (unit=1)
        enddo
c done writing histogram arrays
        ios=close5()
        stop
        end


