c****************************************************************************
c PROGRAM: parith
c
c   This pipe routine allows the user to take two fields of an IRTM dataset 
c and perform an aritmetic operation on them, which is put into an appropriately
c named new field in the output dataset.
c The operations are currently restricted to:
c
c f1+f2
c f1-f2
c f1Xf2
c f1/f2
c f1 (by itself, see below)
c 
c The following separate command line strings are applied to the result,
c if specified:
c    "abs","sqrt","sqr","log10","log"(natural log)
c
c 
c REQUIRED KEYWORDS:
c
c    op=char -- Of the form op=f1<operation>f2 (eg op=t20-t15)
c               Or the form op=f1
c
c OPTIONAL KEYWORDS:
c
c   des=char -- The descriptor file to describe the format and the fields
c               of each record of the input data (default is previous pipe).
c
c   newdes=char -- Create a new descriptor file in your working directory 
c
c   newname=char -- A new short name of this field (default is, eg, 't20-t15')
c                       
c   abs -- Make all results of the new field be of absolute value.
c   sqr -- Square the new field.
c   sqrt -- Square-root the new field.  Note, for some reason
c           if the input is negative, it is made positive before
c           square-rooting.   This is NOT the case, though with log and log10
c   log10 -- log base 10 the new field.   
c            If the input is <= 0, output is -9999.0
c   log   -- natural log the new field.
c            If the input is <= 0, output is -9999.0

c
c Examples: 
c   Just want the absolute value of a field 
c   % parith op=lat      abs des=irtm_18.des < my.irtm_18 > my.irtm_19
c
c   (emis+inc)**2
c   % parith op=emis+inc sqr des=irtm_18.des < my.irtm_18 > my.irtm_19
c
c   (inc/range)
c   % parith op=emis/inc     des=irtm_18.des < my.irtm_18 > my.irtm_19
c
c   (t20)**0.5  ---> Note that abs(20) is done automatically to prevent error.
c   % parith op=t20     sqrt des=irtm_18.des < my.irtm_18 > my.irtm_19
c
c****************************************************************************

        program parith

        implicit none

        include 'pipe1.inc'

        integer ifound,iunit,ndeslines,ios
        integer oldndeslines
        character*80 desfile

        character*80 newdesfile
        character*132 newltitle

        character cfield1*12,cfield2*12,op*30,newname*12,cjunk

        integer field1col,field2col,iabs,isqr,isqrt,newcol
        integer ilog10,ilog
        double precision field1,field2,result,abs

        integer iplus,iminus,itimes,idiv,iop

        character*48 newcdesstitle(MAXCOL)
        character*132 newcdesltitle(MAXCOL)
        integer newndeslines


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


        oldndeslines = ndeslines
c
c parse the operation.
c
        call getcmdchar('op',1,'required',ifound,op) 

        iplus  = index(op,'+')
        iminus = index(op,'-')
        itimes = index(op,'X')
        idiv   = index(op,'/')

        if(iplus.ne.0) then 
           iop = 1
           cfield1 = op(1:iplus-1)
           cfield2 = op(iplus+1:len(op))
        else if(iminus.ne.0) then
           iop = 2
           cfield1 = op(1:iminus-1)
           cfield2 = op(iminus+1:len(op))
        else if(itimes.ne.0) then
           iop = 3
           cfield1 = op(1:itimes-1)
           cfield2 = op(itimes+1:len(op))
        else if(idiv.ne.0) then
           iop = 4
           cfield1 = op(1:idiv-1)
           cfield2 = op(idiv+1:len(op))
        else
           iop = 5
	   cfield1 = op
        endif

        call getcmdchar('abs',0,'optional',iabs, cjunk)
	if(iabs.eq.1) then
	   write(0,*) 'Absolute value.'
        else
           call getcmdchar('sqrt',0,'optional',isqrt, cjunk)
	   if(isqrt.eq.1) then
	      write(0,*) 'Square root.'
           else
              call getcmdchar('sqr',0,'optional',isqr, cjunk)
	      if(isqr.eq.1) then
		 write(0,*) 'Square the result.'
              endif
           endif
        endif

        call getcmdchar('log',0,'optional',ilog, cjunk)
        call getcmdchar('log10',0,'optional',ilog10, cjunk)

c
c Set the column numbers in for the inputs.
c
        call findcol(cfield1,cdesstitle,ndeslines, field1col)
        write(0,*) 'cfield1  : ',cfield1
        write(0,*) 'field1col: ',field1col

	if(iop.lt.5) then
            call findcol(cfield2,cdesstitle,ndeslines, field2col)
            write(0,*) 'cfield2  : ',cfield2
            write(0,*) 'field2col: ',field2col
        endif

c
c add a new descriptor line
c

        if(iop.lt.5) then
           newname = op
        else if(iabs.eq.1) then
	   newname = 'abs' // cfield1(1:5)
        else if(isqr.eq.1) then
	   newname = 'sqr' // cfield1(1:5)
        else if(isqrt.eq.1) then
	   newname = 'sqrt' // cfield1(1:4)
        else if(ilog.eq.1) then
	   newname = 'log' // cfield1(1:5)
        else if(ilog10.eq.1) then
	   newname = 'log10' // cfield1(1:3)
        else
	   newname = 'new' // cfield1(1:5)
        endif
        call getcmdchar('newname',1,'optional',ifound, newname)

	ifound = index(cfield1,' ') - 1

        if(iop.eq.1) then
           newltitle = cfield1(1:ifound)//'+'//cfield2
        else if(iop.eq.2) then
           newltitle = cfield1(1:ifound)//'-'//cfield2
        else if(iop.eq.3) then
           newltitle = cfield1(1:ifound)//'*'//cfield2
        else if(iop.eq.4) then
           newltitle = cfield1(1:ifound)//'/'//cfield2
        else if(iop.eq.5) then
	   if(iabs.eq.1) then
	      newltitle = 'Abs value of ' // cfield1(1:ifound)
           else if(isqr.eq.1) then
	      newltitle = 'Square of ' // cfield1(1:ifound)
           else if(isqrt.eq.1) then
              newltitle = 'Square root of ' // cfield1(1:ifound)
           else if(ilog.eq.1) then
              newltitle = 'Natural log of ' // cfield1(1:ifound)
           else if(ilog10.eq.1) then
              newltitle = 'Log base 10 of ' // cfield1(1:ifound)
	   else
              newltitle = 'Same old ' // cfield1(1:ifound)
	   endif
        endif

        call adddesline(ndeslines+1,newname,newltitle,cdesheader,
     &                  cdesstitle,cdesltitle,ndeslines)

        newcol = ndeslines

        write(0,*) 'New Column Created: ',newname,'(',newltitle,')'

c
c check for 'newdes' in command line (this is for creating a new descriptor
c file in one's filesystem, if desired.
c

        call getcmdchar('newdes',1,'optional',ifound, newdesfile)
        if(ifound.eq.1) then
           open (unit=10,file=newdesfile,status='unknown')
           call writedesheader(10)
           call wdesfil(10, cdesheader,
     &                     newcdesstitle,newcdesltitle,newndeslines)
           close(unit=10)
        endif          ! NOW NDESLINES = NDESLINES + 1


c
c check for 'nodes' in command line 
c

        call getcmdchar('nodes',0,'optional',ifound, cjunk)
        if (ifound.eq.0) then
c          call pdeswrite(6, newdesfile, cdesheader,
c     &               newcdesstitle,  newcdesltitle,
c     &          newndeslines)
          call pdeswrite(6, cdesname, cdesheader,
     &               cdesstitle,  cdesltitle,
     &          ndeslines)
        endif
	call chkcmdkey('bogus')

c
c READ IN THE DATA.
c

500      ios = read5(rdat, oldndeslines)
         if(ios.eq.-1) goto 1000

         field1   = rdat(field1col)
         if(iop.lt.5) field2   = rdat(field2col)

         if(iop.eq.1) then
            result = field1 + field2
         else if(iop.eq.2) then
            result = field1 - field2
         else if(iop.eq.3) then
            result = field1 * field2
         else if(iop.eq.4) then
            result = field1 / field2
         else
	    result = field1
         endif

         if(iabs.eq.1) result = abs(result)
	 if(isqr.eq.1) result = result ** 2.0
	 if(isqrt.eq.1) result = abs(result) ** 0.5
	 if(ilog.eq.1) then
             if(result.le.0.0d0) then
                 result = -9999.0d0
             else
                 result = log(result)
             endif
         endif 
	 if(ilog10.eq.1) then 
             if(result.le.0.0d0) then
                 result = -9999.0d0
             else
                 result = log10(result)
             endif
         endif 

         rdat(newcol) = result
c	 write(0,*) field1,field2,result

         ! END OF CALCULATIONS.

         ios = write6(rdat, ndeslines)

         goto 500

c
c CLOSE INPUT.
c

1000     ios = close5()
         write(0,*) 'DONE'

         stop
         end

         

c************************************************************************
c WRITEDESHEADER: Write out the header for the descriptor file.
c************************************************************************

       subroutine writedesheader(lunit)
       integer lunit
       character*118 desheader

       data desheader/'count   number  type    stitle_8        long_titl
     &e____________________32        units_________________24        For
     &mat'/

       write(lunit,10) desheader
10     format(a118)

       return
       end


c******************************************************************
c******************************************************************
c******************************************************************
c        subroutine findcol(char,cdesstitle,n, col)
c
c        implicit none
c        integer n,col
c        character*8 char,cdesstitle(n)
c        integer i
c
c        do i=1,n
c           if(cdesstitle(i).eq.char) then
c              col = i
c              return
c           endif
c        enddo
c
c        write(0,*) 'ERROR: ',char,' not found in desfile.'
c        stop
c        end
