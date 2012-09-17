C*******************************************************************************
C  PROGRAM: pprint
c
C  PURPOSE: to write formatted, the output from the previous pipe to a file
C
c  REQUIRED PARAMETERS: none
c
c  OPTIONAL PARAMETERS:
c
c        output=char - the name of the new output file (with unknown status)
c                       (default is the standard output)
c
c        titles=int  - write out column titles to make pages of length int
c                      if you specify titles=0 then titles will be written
c                      only on the first page
c                       (default is no titles)
c
c       format=char - the fortran format descriptor to write the records in:
c                    format must be in the form:  format="(10g8)"
c                    (you must use quotes and parentheses, no commas! (sorry)
c
c        des=char  - the name of the descriptor file
c                     (default is to read the descriptor file from
c                      the previous pipe)
c
c       forward    - 'forward' to write all the data and the descriptor file read in
c                      to standard output to pass them to the next pipe
c                      (default is forward=no) (forward is icompatable
c                       no specificaiton of output)
cc
C  EXAMPLES:   pcons des=irtm_18.des lat=45,90 <test.dat | pprint
c
c           the output of pcons will be written formatted to the terminal
c           using the default format
C
C@******************************************************************************


        program pprint

        include 'pipe1.inc'
        character*80    output,desfile,cjunk
        character*80 fmt,afmt,innerfmt,fw,fp,fa
        integer j,k
        integer widprec(2),wid,prec
c
c  Get output file name
        call getcmdchar('output',1,'optional', ifound,output)
        if (ifound.eq.1) then
           ioutput=1
           ioutunit=98
           open (unit=ioutunit,file=output,status='unknown')
        else
           ioutunit=6
           call open6()
        endif

c get format
        call getcmdchar('format',1,'optional', ifound,fmt)
        if (ifound.eq.0) then
           fmt='(2048f21.9)'
        endif

c Even better, specify width and precision

        wid = 21
        prec = 9

        call getcmdint('widprec',2,'optional', ifound,widprec)
        if(ifound.eq.1) then
            wid = widprec(1)
            prec = widprec(2)

            ! Can you believe how retarded Fortran is with strings?

            if(wid.ge.100) then
                fw = 'i3'
            else if(wid.ge.10) then
                fw = 'i2'
            else 
                fw = 'i1'
            endif

            if(prec.ge.100) then
                fp = 'i3'
            else if(prec.ge.10) then
                fp = 'i2'
            else 
                fp = 'i1'
            endif

            innerfmt = '(a6,' // fw(1:index(fw,' ')-1) // 
     +                 ',a1,' // fp(1:index(fp,' ')-1) // ',a1)'

            !write(0,*) 'innerfmt ',innerfmt
            !stop
 
            write(fmt,innerfmt) '(2048f',wid,'.',prec,')'

            !write(0,*) wid,prec,fmt
            !stop

        endif

        ! The header format must line up.

        if(wid.ge.100) then
            fw = 'i3'
        else if(wid.ge.10) then
            fw = 'i2'
        else 
            fw = 'i1'
        endif

        innerfmt = '(a6,' // fw(1:index(fw,' ')-1) // ',a1)'
        write(afmt,innerfmt) '(2048a',wid,')'

        !write(0,*) 'afmt: ',afmt
        !stop

        
 

c check for descriptor file in command line
        call getcmdchar('des',1,'optional',ifound, desfile)

        if( ifound .eq. 1 ) then

c if des found, read from unit 7
                iunit=7
        else
c else, get descriptor from standard input
                iunit=5
        endif
c read descriptor file from appropriate unit
          call pdesread(iunit, desfile, cdesheader,  
     &               cdesstitle,  cdesltitle,
     &               ndeslines)
c
c  Forward the descriptor file, if indicated by user,and there are no conflicts
c
        call getcmdchar('forward',0,'optional',ifound, cjunk)
        if (ifound.eq.1) then
          iforward = 1
          if (ioutput.eq.1) then
      write (0,*) 'PPRINT ERROR: '
      write (0,*) 'KEYWORD forward REQUIRES THAT output BE SPECIFIED'
                stop
          endif
        call pdeswrite(6, desfile,  cdesheader, 
     &                cdesstitle,  cdesltitle,
     &               ndeslines)
        else
          iforward = 0
        endif

        ititles=0
        call getcmdint('titles',1,'optional',iyestitles, ititles)

c make titles if necessary
        if (iyestitles.eq.1) then
                npage=0
                write (ioutunit,afmt)
     &    (cdesstitle(k)(1:index(cdesstitle(k),' ')-1),
     &           k=1,ndeslines)
                !!!write (ioutunit,*) ' '
                npage=npage+2
        endif

c check for bad keywords
        call chkcmdkey('bogus')

c main loop
10      ios = read5(rdat,ndeslines )
        if( ios .eq. -1 ) goto 99
c write out formatted data
        write(ioutunit, fmt) (rdat(i), i=1,ndeslines)
        npage=npage+1

c write out titles if at end of page
        if (iyestitles.eq.1.and.ititles.gt.2.and.npage.eq.ititles)
     &      then
                write (ioutunit,'(a)') char(12)
                write (ioutunit,afmt)
     &    (cdesstitle(k)(1:index(cdesstitle(k),' ')-1),
     &           k=1,ndeslines)
                npage=2
        endif
        if( iforward .eq. 1 ) ios=write6(rdat, ndeslines)
        goto 10
99      continue
        if( iforward .eq. 1 ) endfile(6)
999     stop
        end
