        program pskip
c
c  Variable declaration of variables common to all pipes
c
        include 'pipe1.inc'
        character*80 desfile,junk
        integer*4 idescol(MAXCOL), ipass, iskip

c get the number of lines to be skipped
        call getcmdint('nskip',1,'required',ifound,iskip)
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
          call pdeswrite(6, cdesname,  cdesheader,
     &               cdesstitle,  cdesltitle,
     &               ndeslines)
        endif

c check command line for bogus key words
        call chkcmdkey('bogus')

        ios = read5(rdat,ndeslines)
        if (ios .eq. -1) goto 999
        ios = write6(rdat, ndeslines)

        ipass = iskip
10      ios = read5(rdat, ndeslines)
        if( ios .eq. -1 ) goto 999
        ipass = ipass - 1
        if (ipass.eq.0) then
             ios =  write6(rdat, ndeslines)
             ipass = iskip
             goto 10
        else
           goto 10
        endif
999     continue
        endfile ( unit=6)
        ios=close5()
        stop
        end


