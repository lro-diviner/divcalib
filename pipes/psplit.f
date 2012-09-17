        program psplit
c
c psplit splits an input stream into multiple binary output streams 
c with no descriptor file using a binning scheme.
c syntax:
c  psplit lat=0,90,10  filename='/s2/user/dap/data**.pipe'
c  where ** indicates 01,02,03 etc depending on the bin number
c the * can go anywhere in the filename
c or you can get tricky and do:
c psplit lat=0,90,10 filename=c0-**:/u/dap/data.dat

        include 'pipe1.inc'
        parameter (MAXFILES=360)
        character*80 desfile
        character*80 filename
        character*92 rmcomm
        character*80 filenames(MAXFILES)
        integer*4 idescol(MAXCOL)
        real*8 const(3,MAXCOL)
        real*8 bmin,bmax,bdelta
        integer*4 isplitcol,nsplit
        integer*4 irec(MAXFILES)
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
c           

        call getcmdreals(cdesstitle,ndeslines,3, ncon,idescol,const)
        if (ncon.ne.1) stop 
     & 'error in psplit, zero or multiple split parms'

        bmin=const(1,1)
        bmax=const(2,1)
        bdelta=const(3,1)
        isplitcol=idescol(1)
        nsplit=dabs(bmax-bmin)/dabs(bdelta)

        call getcmdchar('filename',1,'required',ifound,filename)



c check command line for bogus key words
        call chkcmdkey('bogus')

c figure out filenames and open files

c find the series of * characters in filename

        istar1=index(filename,"*")
        if (istar1.eq.0) stop 
     & 'psplit error: filename must contain * characters'
c        write (0,*) 'psplit istar1= ',istar1
        nstars=1
        istar2=index(filename,"**")
        if (istar2.ne.0) nstars=2
        istar2=index(filename,"***")
        if (istar2.ne.0) nstars=3
        istar2=index(filename,"****")
        if (istar2.ne.0) nstars=4
        istar2=index(filename,"*****")
        if (istar2.ne.0) stop  
     &'psplit erorr: too many stars in filename'
        istar2=istar1+nstars-1

c        write (0,*) 'psplit , istar1,istar2,nstars ',
c     & istar1,istar2,nstars


c name and open the files
        do i=1,nsplit
           iunit=10+i
           if (nstars.eq.1) 
     & write (filename(istar1:istar2),'(i1)') i
           if (nstars.eq.2)
     & write (filename(istar1:istar2),'(i2.2)') i
           if (nstars.eq.3)
     & write (filename(istar1:istar2),'(i3.3)') i
           if (nstars.eq.4)
     & write (filename(istar1:istar2),'(i4.4)') i

       write(rmcomm,'(a12,a80)') '/bin/rm -f ',filename
       ios = system(rmcomm)
       open (unit=iunit,file=filename,status='unknown',

     & recl=ndeslines*8,access='direct')
           irec(i)=1
c        write (0,*)'psplit: opening unit ',iunit,' file name: ',filename
        enddo

10      ios = read5(rdat, ndeslines)
        if( ios .eq. -1 ) goto 999
c reject data that's out of range
        if (rdat(isplitcol).lt.bmin.or.rdat(isplitcol).ge.bmax) goto 10
c calculate which file data goes in
        ibin=nsplit*(rdat(isplitcol)-bmin)/(bmax-bmin)+1
c        write out data
        write (10+ibin,rec=irec(ibin)) (rdat(l),l=1,ndeslines)
        irec(ibin)=irec(ibin)+1
            goto 10     
999     continue
        ios = close5()
        do i=1,nsplit
           close (unit=10+i)
        enddo
        stop
        end



