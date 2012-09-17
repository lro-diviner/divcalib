C*******************************************************************************
C  PROGRAM: pconspass
c
C  PURPOSE: Like "pcons", but tailored for data like EDR/L1A that don't fill
c           in engineering data every record, but might, say, have a valid
c           value for "last_el_cmd" in the first sounding, then -9999
c           for the next 15 records.   If we want all 16 records in
c           the set that matches this value, we would use pass=15.
c           
C
c  REQUIRED KEYWORDS:
c
c       pass=INTEGER  How many subsequent records should pass down
c                     the pipe when matching a record.
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
c     pconspass des=div247.des pass=15 last_el_cmd=180,180 last_az_cmd=240,240 < test.div247 > test2.div247
c
c
C@******************************************************************************


        program pconspass
        implicit none!!!
c
c  Variable declaration of variables common to all pipes
c
        include 'pipe1.inc'
        character*80 desfile,junk
        integer*4 idescol(MAXCOL),pass,np
        integer iunit,ndeslines,ncon,ios,i,ifound
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

c The pass variable

        call getcmdint('pass',1,'required',ifound, pass);

c check command line for bogus key words
        call chkcmdkey('bogus')

c
c Initialize loop to pass nothing.
c

        np = 0

c
c Loop
c


10      ios = read5(rdat, ndeslines)
        if( ios .eq. -1 ) goto 999

        if(np.gt.0) then
            ! Decrement and pass
            np = np - 1
            goto 800
        endif
        
        do 440 i=1,ncon

            ! check for band reject mode
            if ( const(2,i) .lt. const(1,i) ) goto 435

            ! in this (more usual) case, the first constraint is less than the second
            if ( rdat(idescol(i)) .ge. const(1,i) .and.
     &           rdat(idescol(i)) .le. const(2,i)) then
                    goto 440
            else
                    goto 10
            endif

           ! in this (band reject) case, the first constraint is greater than the second
435        if ( rdat(idescol(i)) .le. const(1,i) .and.
     &          rdat(idescol(i)) .ge. const(2,i)) goto 10


440    continue

       ! 
       ! We have a valid match.   Initialize np
       !

       np = pass

       !
       ! Write a record
       !

800    continue

       ios =  write6(rdat, ndeslines)

        goto 10
999     continue
        endfile (unit=6)
        ios=close5()
        stop
        end


