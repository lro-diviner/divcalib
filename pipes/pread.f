C*******************************************************************************
C  PROGRAM: pread
c
C  PURPOSE: to read formatted data into a pipe
C
c  REQUIRED PARAMETERS: none
c
c        des=char  - the name of the descriptor file
c                     (default is to read the descriptor file from
c                      the previous pipe)
c
c  OPTIONAL PARAMETERS:
c
c
c       format=char - the fortran format descriptor to read the records in:
c                    format must be in the form:  format="(10g8)"
c                    (you must use quotes and parentheses, no commas! (sorry)
c                     (default is format="(*)"
c
c       skip=int    -  causes pread to skip int lines before reading data
c                      (default is skip=0)
c       
c       skiperror  - skips lines with read errors
c
c       nodes - suppress writng descriptor file to standard output
C  EXAMPLES: pread des=irtm15.des | pcons lat=45,90  | pprint
c
c
c  BUGS:  format must be 12 characters wide per column if the titles
c         are to line up
C
C@******************************************************************************


        program pread

        include 'pipe1.inc'
        character*80    desfile
        character*80 fmt
        integer iskiperror
c

c get format
        call getcmdchar('format',1,'optional', ifmt,fmt)

c check for descriptor file in command line
        call getcmdchar('des',1,'required',ifound, desfile)
c read descriptor file from appropriate unit
          call pdesread(7, desfile,  cdesheader,
     &               cdesstitle,  cdesltitle,
     &                ndeslines)


c          write (0,*) 'cdesstitle ',cdesstitle(1),cdesstitle(2)

c
c  send the descriptor file down the pipe
c
          ifound=0
          call getcmdchar('nodes',0,'optional',ifound, desfile)


          if (ifound.eq.0) then
        call pdeswrite(6, desfile,  cdesheader,
     &               cdesstitle, cdesltitle,
     &               ndeslines)
         endif

c check for skipping errors
          iskiperror=0
          
          call getcmdchar('skiperror',0,'optional',iskiperror, desfile)
          



c check for skipping lines
        call getcmdint('skip',1,'optional',ifound,iskip)
        if (ifound.eq.1) then
                do i=1,iskip
                        read (5,*)
                enddo
        endif
c check for bad key words
        call chkcmdkey('bogus')
c main loop
10      continue
        if (iskiperror.eq.0) then
        if (ifmt.eq.0) read(5,*,end=99) (rdat(i),i=1,ndeslines)
        if (ifmt.eq.1) read (5,fmt,end=99) (rdat(i),i=1,ndeslines)
        else
        if (ifmt.eq.0) read(5,*,end=99,err=10) (rdat(i),i=1,ndeslines)
        if (ifmt.eq.1) read (5,fmt,end=99,err=10)(rdat(i),i=1,ndeslines)
        endif
        ios=write6(rdat, ndeslines)
        goto 10
99      continue

        stop
        end
