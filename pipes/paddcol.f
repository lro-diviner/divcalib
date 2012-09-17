C*******************************************************************************
C  PROGRAM: paddcol
c
C  PURPOSE: Adds a new column to the pipe, of fixed value.
c
C
c  REQUIRED KEYWORDS: addcol=colname addval=value
c
c       colname is the short title of a NEW column
c       value is the numerical value you want to colname to be
c
c       des=char  -- the descriptor file to describe the format and the
c                    fields of each record of the input data
c                    (the default is the previous pipe)
c
C  EXAMPLE:
c
c       phist des=irtm_18.des update=1000 lat=-90.,90.,10 hour=0.,24.,1. <test.dat
c       divdata ... | paddcol add=tag1,168 > output
c
C@******************************************************************************


        program paddcol
        !implicit none
c
c  Variable declaration of variables common to all pipes
c
        include 'pipe1.inc'

        character*80 desfile,colname
        integer*4 idescol(MAXCOL),ifound,iunit
        real*8 dat,colval

        integer ndeslines,oldndeslines,ios
        character*80 newdesfile,cjunk

c check for descriptor file in command line

        call getcmdchar('des',1,'optional',ifound, desfile)

        if( ifound .eq. 1 ) then
                iunit=7
        else
                iunit=5
        endif
        call pdesread(iunit, desfile,  cdesheader,
     &               cdesstitle,  cdesltitle,
     &               ndeslines)

        call getcmdchar('addcol',1,'required',ifound, colname)
        call getcmdreal('addval',1,'required',ifound, colval)

c
c Set up new descriptor file.
c

        oldndeslines = ndeslines
        call adddesline(ndeslines+1,colname,colname,cdesheader,
     &                  cdesstitle,cdesltitle,ndeslines)

        call getcmdchar('newdes',1,'optional',ifound, newdesfile)
        if(ifound.eq.1) then
           open (unit=10,file=newdesfile,status='unknown')
           call wdesfil(10, cdesheader,
     &                     cdesstitle,cdesltitle,ndeslines)
           close(unit=10)
        endif


        call getcmdchar('nodes',0,'optional',ifound, cjunk)
        if (ifound.eq.0) then
          call pdeswrite(6, cdesname, cdesheader,
     &               cdesstitle,  cdesltitle,
     &          ndeslines)
        endif

        call chkcmdkey('bogus')

c
c Loop
c

10      ios = read5(rdat, oldndeslines)
        if( ios .eq. -1 ) goto 999

        rdat(ndeslines) = colval

        ios = write6(rdat, ndeslines)

        goto 10

999     continue

        ios=close5()
        stop
        end


