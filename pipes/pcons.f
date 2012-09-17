C*******************************************************************************
C  PROGRAM: pcons
c
C  PURPOSE: output constrained data based on user input constraints
C
c  REQUIRED KEYWORDS: none
c
c  OPTIONAL KEYWORDSS:
c
c       col_name=real(1),real(2)  - col_name is the short title of a column
c                                   real(1) is the first constraint value
c                                   real(2) is the second constraint value
c
c                                   if real(2) >= real(1), then only data with
c                                   real(1) <= col_name <= real(2) are passed=
c                                   down the pipe.  i.e. real(1) is the minumum
c                                   and real(2) is the maximum
c
c
c                                    if real(2) < real(1), then data with
c                                    real(2) <=  col_name <= real(1) are NOT
c                                    passed down the pipe.  i.e. band reject mode.
c
c
c
c       des=char  -- the descriptor file to describe the format and the
c                   fields of each record of the input data
c                    (the default is the previous pipe)
c
c       nodes   - To prohibit the writing of the descriptor file to
c                  the next pipe.  This enables the unformatted output
c                  to be redirected to an output file.
c
C  EXAMPLE:
c
c               pcons des=irtm_18.des lat=5.5,6.7 hour=15,8.2 <test.dat >test2.dat
c
c               pcons will let pass only those observatoins taken between
c               5.5<=lat<=6.7 and   -Inf<hour<8.2 and 15.0<hour<+Inf
c
c
C@******************************************************************************


        program pcons
c
c  Variable declaration of variables common to all pipes
c
        include 'pipe1.inc'
        character*80 desfile,junk
        integer*4 idescol(MAXCOL)
        real*8 const(2,MAXCOL)

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

        if (ifound.eq.0) then
c if not present, send descriptor file down pipe
          call pdeswrite(6, cdesname, cdesheader, 
     &               cdesstitle,  cdesltitle,
     &               ndeslines)
        endif
        call getcmdreals(cdesstitle,ndeslines,2, ncon,idescol,const)

c check command line for bogus key words
        call chkcmdkey('bogus')

10      ios = read5(rdat, ndeslines)
        if( ios .eq. -1 ) goto 999
              do 440 i = 1, ncon
c check for band reject mode
                 if ( const(2,i) .lt. const(1,i) ) goto 435
c in this (more usual) case, the first constraint is less than the second
                 if ( rdat(idescol(i)) .ge. const(1,i) .and.
     &                rdat(idescol(i)) .le. const(2,i)) then
                    goto 440
                 else
                    goto 10
                 endif
c in this (band reject) case, the first constraint is greater than the second
435              if ( rdat(idescol(i)) .le. const(1,i) .and.
     &                rdat(idescol(i)) .ge. const(2,i)) goto 10
440           continue
             ios =  write6(rdat, ndeslines)
        goto 10
999     continue
        endfile ( unit=6)
        ios=close5()
        stop
        end


