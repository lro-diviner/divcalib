C  SUBROUTINE: getlen
c
C  PURPOSE: Determine the length of a string excluding any blank padding
C
C  ARGUMENTS: string (INPUT) - any length string
c		NOTE:  This function discriminates against both blanks,
c		       and char(0), so the length returned by this
c		       function is the number of characters which form
c		       a contiguous string excluding NULLs and blanks
c
C  EXAMPLE:  string='april	    '
c	     len=getlen(string)
c		len would equal 5
C
C  CALLED BY:  functions isparam, iskeywd
c	       subroutine cmdarg, uptolow
C
C  CALLS:  len
C
C  OPERATING SYSTEM / PORTABILITY NOTES:  portable
C
C  DATE:  8/20/88
c
C*******************************************************************************

	integer function getlen(string)
	character*(*) string

c
c  Start with the last character and find the first non-blank
c
	do 10 next = len(string), 1, -1
	   if ((string(next : next) .ne. ' ') .and.
     +	       (string(next : next) .ne. char(0)) ) then
	     getlen = next
	     return
	   endif
10	continue
c
c  All characters are blanks or NULLs
c
	getlen=0

	return
	end

c*****************************************************************************
c  SUBROUTINE:	getparam
c  DATE:  8/09/88
c  PURPOSE:
C	Given an argument, the subroutine returns the word to the LEFT of
c	"=".
c  OPERATING SYSTEM / POTABILITY NOTES:
c	Written in standard Fortran 77.  Compatible on all systems.
c
c  EXAMPLE:
c	Given the argument "col=1"
c	Subroutine will return "col" as the parameter
c  CALLED BY:
c	triconproc, called by pipe fitting pcons.  Code in 'pcons.for'
c  CALLS:
C	index
c
c  ARGUMENTS:
C	arg(INPUT)--a string of the format:
c			parameter=value1(,value2,...)
c	param(OUTPUT)--the string to the left of "="
c
c************************************************************************


	subroutine getparam(arg, param)

	character*(*)	arg
	character*(*) param

c  Local variable declarations
	integer k, index

	k = index( arg,'=')
c
c  If k=0 return the whole argument, since it's a keyword, else return
c  the parameter( the part before the = sign
c

	if( k .eq. 0 ) then
	  param = arg
	else
	  param = arg(1:k-1)
	endif
	return
	end

c**********************************************************************
c  SUBROUTINE:
c	getnumval
c
c  DATE:
c	8/10/88
c
c  VERSION:
c
c  PROJECT:
c	command line processing
c
c  PURPOSE:
c	returns the number of values, that is, the number of items to the
c	right of "=" separated by commas.
c
c  OPERATING SYSTEM / PORTABILITY:
c	Written in standard Fortran 77. Compatible with all systems.
c
c  EXAMPLE:
c	arg = 'col=1,2'
c	subroutine returns 2
c	arg = 'col='
c	subroutine prints an error message and stops execution.  NO RETURN
c
c  CALLED BY:
c	cld
c
c  CALLS:
c	index()
c
c  ARGUMENTS:
c	arg(INPUT)--a string of the format:
c		    parameter=value1(,value2,....)
c	numval(OUTPUT)--the number of items(separated by comma) to the right
c			of "="
c
c**************************************************************************

	subroutine getnumval(arg, numval)
	character*(*) arg
	integer numval

c  Local variable declaration

	integer  index, i, nchar, getlen

	numval = 0
	nchar = 0
c
c  skips to the parameter value to the right of =
c
	i = index( arg, '=')
	if ( i .eq. 0 ) return
	i = i + 1
c	 write(0,*) 'len of arg=', getlen(arg)
	do 20 j = i, getlen(arg)
	   if ( arg(j:j) .eq.' ' ) then
	      goto 25
	   else if( arg(j:j) .eq. ',' .and. nchar .gt. 0) then
		 numval = numval + 1
		 nchar = 0
	   else
	      nchar = nchar + 1
	   endif
20	continue
25	if ( nchar .gt. 0 ) then
	   numval = numval + 1
	endif
	return
	end

C*******************************************************************************
C  SUBROUTINE: getcharval
c
C  PURPOSE: to get character values(items separated by commas) of a parameter
C
C  ARGUMENTS:  arg(INPUT) - a string of the format:
c				parameter = value1(,value2,...)
C	       value(OUTPUT) - an array of strings, the character values
C
C  EXAMPLE:    arg='month=august,april'
c	       call getcharval(arg, value)
c		subroutine will return:
c		  value(1)='august'
c		  value(2)='april'
C
C  CALLED BY:  none
C
C  CALLS:  index, len
C
C  OPERATING SYSTEM / PORTABILITY NOTES:  portable
C
C  DATE: 8/20/88
c
C*******************************************************************************



	subroutine getcharval(arg, value)
	character*(*) arg
	character*(*) value(*)

c  Local Variable declaration

	integer i,j,k, index, newval, nval, last

c  Skipping to the first value

	i = index( arg,'=')
	newval = i + 1
	last = 0

c  Parse the values and put them into value array

	nval=1
10	i = index(arg(newval:len(arg)),',' )
c
c  To handle exception:  the last value is not followed by a comma;
c  Last value followed by NULL or space
c
	if ( i .eq. 0 ) then
	   last = 1
	   i = index( arg(newval:len(arg)), char(0))
	   if (i .eq. 0) i=index( arg(newval:len(arg)), ' ')
	endif
c	write(0,*) i,'th char is a comma or NULL or space'
	   value(nval) = arg(newval:newval+i-2)
	   newval = newval + i
	if ( last .eq. 1 ) goto 20
	nval=nval+1
	goto 10
20	continue
	return
	end

C*******************************************************************************
C  SUBROUTINE: getintval
c
C  PURPOSE: to get integer values(items separated by commas) of a parameter
C
C  ARGUMENTS:  arg(INPUT) - a string of the format:
c				parameter = value1(,value2,...)
C	       value(OUTPUT) - an array of integers
C
C  EXAMPLE:    arg='irec=1,3'
c	       call getintval(arg, value)
c		subroutine will return:
c		  value(1)= 1
c		  value(2)= 3
C
C  CALLED BY:  none
C
C  CALLS:  index, len
C
C  OPERATING SYSTEM / PORTABILITY NOTES:  portable
C
C  DATE: 8/20/88
c
C*******************************************************************************

	subroutine getintval(arg, value)
	character*(*) arg
	integer value(*)

c  Local variable declaration

	integer i,j,k,	newval, nval, last
	character*150 temp

c  Skipping to the first value

	i = index( arg,'=')
	newval = i + 1
	last = 0

c  Parse the values and put them into value array

	nval=1
10	i = index(arg(newval:len(arg)),',' )
c
c  To handle exception:  the last value is not followed by a comma;
c  Last value followed by NULL or space
c
	if ( i .eq. 0 ) then
	   last = 1
	   i = index( arg(newval:len(arg)), char(0))
	   if (i .eq. 0) i=index( arg(newval:len(arg)), ' ')
	endif
c	write(0,*) i,'th char is a comma or NULL or space'
	   temp = arg(newval:newval+i-2)
	   read(temp,*,err=99) value(nval)
	   newval = newval + i
	if ( last .eq. 1 ) goto 20
	nval=nval+1
	goto 10
20	continue
	return
99	write (0,*) 'COMMAND LINE ERROR: CAN"T PARSE ARGUMENT: ', arg
	stop
	end

C*******************************************************************************
C  SUBROUTINE: getrealval
c
C  PURPOSE: to get real values(items separated by commas) of a parameter
C
C  ARGUMENTS:  arg(INPUT) - a string of the format:
c				parameter = value1(,value2,...)
C	       value(OUTPUT) - an array of strings, the real values
C
C  EXAMPLE:    arg= 'lat=2.5,56.9'
c	       call getrealval(arg, value)
c		subroutine will return:
c		  value(1)= 2.5
c		  value(2)= 56.9
C
C  CALLED BY:  subroutine triconproc  in pipe fitting pcons
C
C  CALLS:  index, len
C
C  OPERATING SYSTEM / PORTABILITY NOTES:  portable
C
C  DATE: 8/20/88
c
C*******************************************************************************


	subroutine getrealval(arg, value)
	character*(*) arg
	real*8 value(*)

c  Local variable declaration

	integer i,j,k,	newval, nval, last
	character*150 temp

c  Skipping to the first value

	i = index( arg,'=')
c	write(0,*) '= is at ', i
	newval = i + 1
	last = 0

c  Parse the values and put them into value array

	nval=1
c	write(0,*) 'arg=', arg
10	i = index(arg(newval:len(arg)),',' )
c
c  To handle exception:  the last value is not followed by a comma;
c  Last value followed by NULL or space
c
	if ( i .eq. 0 ) then
	   last = 1
	   i = index( arg(newval:len(arg)), char(0))
	   if (i .eq. 0) i=index( arg(newval:len(arg)), ' ')
c	write(0,*) 'last == 1', 'i==', i
	endif
c	write(0,*) i,'th char is a comma or NULL or space'
	   temp = arg(newval:newval+i-2)
	   read(temp,*,err=99) value(nval)
	   newval = newval + i
	if ( last .eq. 1 ) goto 20
	nval=nval+1
	goto 10
20	continue
	return
99	write (0,*) 'COMMAND LINE ERROR: CAN"T PARSE ARGUMENT: ', arg
	stop
	end


C*******************************************************************************
C  SUBROUTINE: uptolow
c
C  PURPOSE: Convert a string to all lower case characters
C
C  ARGUMENTS: string (INPUT, OUTPUT) - a null terminated string preferred
C
C  EXAMPLE:  string='ALL CAPS'
C	     call uptolow(string)
c		string now equals 'all caps'
C
C  CALLED BY:  cmdget
C
C  CALLS: integer functions getlen, ichar
C
C  OPERATING SYSTEM / PORTABILITY NOTES:  portable
C
C  DATE: 8/15/88
c
C*******************************************************************************



	subroutine uptolow(string)
	character*(*) string

c  Local declarations
	integer getlen

	lenstr = getlen(string)
	i=1
10	n = ichar(string(i:i))
	if( n .eq. 0 .or. i .gt. lenstr) goto 99
	if( n .ge. 65 .and. n .le. 90 ) string(i:i) = char( n + 32)
	i=i+1
	goto 10
99	continue
	return
	end



C*******************************************************************************
C  FUNCTION:  colsproc
c
C  PURPOSE:  1.  To transform the column names into column numbers by:
c		a.  look up the column name in the array stitle
c		b.  if found, the array index of the column name in stitle is
c		      the column number, and stored in array, colnum
c		    else an error message is generated, and execution is
c		    stopped
c
c	     2.  Return the number of columns there are
c
c	     3.  In case of error : Output ERROR message to unit 0,
c		 which is set to be sys$error, and stop execution.
c		 sys$error = terminal ( interactive )
c			   = log file ( batch )
c		 To set unit 0 to sys$error, do:
c			$assign sys$error for000
C
C  ARGUMENTS:  cols (INPUT) - the array of column names
c	       stitle (INPUT) - array of short names for each column of the
c			       irtm data, as read from the irtm description
c			       file, irtm.des
c	       colnum (OUTPUT) - array of column numbers corresponding to
c			       the column names in array 'cols'
C
C  EXAMPLE:    ncol=colsproc(cols,stitle, colnum)
C
c	       ncol is the number of column names in cols that were found
c	       in 'stitle', returned by this function
c
C  CALLED BY:  pcons, pbin2d
C
C  CALLS:  index
C
C  OPERATING SYSTEM / PORTABILITY NOTES:  portable
C
C  HISTORY:
c	9/01/88  Carol Chang. Created it
c	7/23/89  Carol Chang. Added error checking for erroneous column
c			      names
c
C*******************************************************************************

	integer function colsproc(cols, stitle, colnum)
		character*(*) stitle(*)
		character*(*) cols(*)
		integer colnum(*)


	ncol=0
	i=1
	j=1

c
c-- Done translating all the column in cols, when char(0) is encountered
c-- in cols
c
10	if (index(cols(i), char(0)) .eq. 1) goto 30
c
c-- Error : no match with any of the short column names
c
20	if (index(stitle(j), char(0)) .eq. 1) goto 50
c
c-- Match successful.  Continue to the next column name
c
	if ( cols(i) .eq. stitle(j)) then
	   ncol=ncol+1
	   colnum(ncol) = j
	   goto 40
	endif
	j=j+1
	goto 20

40	continue
	i=i+1
	j=1
	goto 10

50	continue
	write(0,*) 'COLSPROC: ERROR: COLUMN ',
     +		    cols(i), ' is not a correct column name'
	stop

30	continue
	colsproc=ncol
	return
	end



cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc
c  This file contains all the subroutines which handle the descriptor file.
c  The subroutines are :
c    rdesfil -- reads a descriptor file
c    wdesfil -- outputs a descriptor file
c    pdesread -- prepares a descriptor file for reading and then reads it
c    pdeswrite-- prepares a descriptor file for writing and then writes it
c    adddesline -- add a line to the internal arrays which represent the
c		   descriptor file
c    subdesline -- subtract a line from the internal arrays which represent
c		   the descriptor file
c
c  Please read the documentation preceding each subroutine to understand
c  the particular subroutine
c
cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc


C*******************************************************************************
C  SUBROUTINE:	rdesfil
c
C  PURPOSE:  To read a descriptor file from any unit, process each line
c	     of the descriptor file into fields, and store these separate
c	     fields in separate arrays.
C
C  ARGUMENTS: unit (INPUT) - the unit to read from
C	      count (OUTPUT) - The number of a column corresponding to its
c			       order in a file record.
c			       An array of integers gotten from the first
c			       column of the descriptor file
c
c	      number (OUTPUT) - The number of repetitions of a column in
c				a file record.	An array of integers gotten
c				from the second column of the descriptor file
c
c	      type (OUTPUT) - data type of each column of a file record.
c			      An array of strings gotten from the third column
c			      of the descriptor file
c
c	      stitle (OUTPUT) - The short name of each column of a file record.
c				An array of strings of length 8 gotten from the
c				fourth column of the descriptor file
c
c	      ltitle (OUTPUT) - The long name of each column of a file record.
c				An array of strings of length 32 gotten from
c				the fifth column of the descriptor file
c
c	      units (OUTPUT) - The proper measuring units to use for each
c			       column of a file record.  An array of strings
c			       gotten from the sixth column of the descriptor
c			       file
c
c	      format (OUTPUT) - The recommended format for each column of
c				a file record.	An array of strings gotten
c				from the seventh column of the descriptor file
c
c	      recl (OUTPUT) - The size of a record described by the given
c			      descriptor file in longwords(4 byte)
c
c	      nlines (OUTPUT) - The number of lines in the descriptor file
c
C  EXAMPLE:
C
C  CALLED BY: all pipes except pirtm and pirtm2
C
C  CALLS: index
C
C  OPERATING SYSTEM / PORTABILITY NOTES:  portable
C
C  HISTORY:  8/30/88   Carol Chang.  Created it
c	     9/30/89   Carol Chang.  Changed rdesfil to read from any unit,
c		       leaving the unit-file association, opening of file
c		       to the higher level routine, preprdes
c
c	     6/20/90   Carol Chang.  Changed the stopping condition for
c		       read from EOF to count(irec)=-1 in order to
c		       make reading descriptor file through the UNIX pipes
c		       possible on THESUN.
c
c
C*******************************************************************************

	subroutine rdesfil(unit, header,stitle,ltitle,
     +			   nlines)
	character*(*) ltitle(*),header
	character*(*) stitle(*)
	integer  unit, nlines

c
c  Skip the heading in .des file
c
	irec = 1
	if (unit .ne. 5 ) then
	  read(unit,*) header 

110	  read(unit,*,end=9) 
     +	     stitle(irec),ltitle(irec)
	  irec=irec+1
	  goto 110
	else
	  read (unit,*) header
120	  read(5,*) 
     +	     stitle(irec),ltitle(irec)
	  if ( stitle(irec).eq.'end') goto 9
c	  write(0,*) 'irec=', irec
	  irec=irec+1
	  goto 120
	endif
9	continue
c
c  Mark the end in all the arrays
c
 100	nlines = irec-1 

c
c  Calculate record length
c
c	recl=nlines
c	write (0,*) 'rdesfil recl,nlines,irec',recl,nlines,irec

	return
	end

C*******************************************************************************
C  SUBROUTINE:	wdesfil
c
C  PURPOSE:  To write the descriptor file to any unit.	The descriptor
c	     file is passed to the subroutine as arrays.  These arrays
c	     are written out using the format consistent with the read
c	     format in subroutine RDESFIL.
C
C  ARGUMENTS: unit (INPUT) - the unit to write to
C	      count (INPUT) - The number of a column corresponding to its
c			       order in a file record.
c			       An array of integers gotten from the first
c			       column of the descriptor file
c
c	      number (INPUT) - The number of repetitions of a column in
c				a file record.	An array of integers gotten
c				from the second column of the descriptor file
c
c	      type (INPUT) - data type of each column of a file record.
c			      An array of strings gotten from the third column
c			      of the descriptor file
c
c	      stitle (INPUT) - The short name of each column of a file record.
c				An array of strings of length 8 gotten from the
c				fourth column of the descriptor file
c
c	      ltitle (INPUT) - The long name of each column of a file record.
c				An array of strings of length 32 gotten from
c				the fifth column of the descriptor file
c
c	      units (INPUT) - The proper measuring units to use for each
c			       column of a file record.  An array of strings
c			       gotten from the sixth column of the descriptor file
c
c	      format (INPUT) - The recommended format for each column of
c				a file record.	An array of strings gotten
c				from the seventh column of the descriptor file
c
c	      nlines (INPUT) - The number of lines in the descriptor file
c
c
C  EXAMPLE:
C
C  CALLED BY: all pipes except pirtm and pirtm2
C
C  CALLS: index
C
C  OPERATING SYSTEM / PORTABILITY NOTES:  portable
C
C  HISTORY:  9/30/88   Carol Chang.  Created it
c	     6/20/90   Carol Chang.
c	       Changed the way of indicating EOF from an end-of-file
c	       marker using FORTRAN endfile statement to outputing
c	       a -1 for the count field of the line after the last
c	       line of the file.
c
c
c
c
C*******************************************************************************
	subroutine wdesfil(unit, header, stitle,ltitle,nlines)
	character*(*)  ltitle(*)
	character*(*) header
	character*(*)   stitle(*)
	integer unit,  nlines
c
c  Write each line of the descriptor file to the unit specified
c

	write (unit,*) "'",header,"'"
	do 10 irec=1,nlines
	write(unit,*) "'",stitle(irec),"'",' ',
     & "'",ltitle(irec),"'"
10	continue

	return
	end

C*******************************************************************************
C  SUBROUTINE: preprdes
c
C  PURPOSE: To read a descriptor file from a unit
C
C  ARGUMENTS: unit (INPUT) - the unit to read from
c	      des ( INPUT ) - the name of the descriptor file
C	      count (OUTPUT) - The number of a column corresponding to its
c			       order in a file record.
c			       An array of integers gotten from the first
c			       column of the descriptor file
c
c	      number (OUTPUT) - The number of repetitions of a column in
c				a file record.	An array of integers gotten
c				from the second column of the descriptor file
c
c	      type (OUTPUT) - data type of each column of a file record.
c			      An array of strings gotten from the third column
c			      of the descriptor file
c
c	      stitle (OUTPUT) - The short name of each column of a file record.
c				An array of strings of length 8 gotten from the
c				fourth column of the descriptor file
c
c	      ltitle (OUTPUT) - The long name of each column of a file record.
c				An array of strings of length 32 gotten from
c				the fifth column of the descriptor file
c
c	      units (OUTPUT) - The proper measuring units to use for each
c			       column of a file record.  An array of strings
c			       gotten from the sixth column of the descriptor
c			       file
c
c	      format (OUTPUT) - The recommended format for each column of
c				a file record.	An array of strings gotten
c				from the seventh column of the descriptor file
c
c	      recl (OUTPUT) - The size( in longwords ) of the record described
c			      by the descriptor file
c
c	      nlines (OUTPUT) - The number of lines in the descriptor file
C  EXAMPLE:
C
C  CALLED BY: all pipes except pirtm and pirtm2
C
C  CALLS: index
C
C  OPERATING SYSTEM / PORTABILITY NOTES:  portable
C
C  HISTORY:  9/30/89   Carol Chang.  Created it
c
ccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc

	subroutine pdesread(unit, des, header,stitle,ltitle,
     &			      nlines)
	character*(*) des
	character*(*) header
	character*(*) ltitle(*)
	character*(*)  stitle(*)
	integer nlines, unit, recl

c
c  Append '.des' to <des> to form the name of the description file to open
c
	if( unit .ne. 5 ) then
	  call openform(unit, des, 'old')
	endif
c
c  Read the descriptor file
c

	call rdesfil(unit, header,stitle, ltitle,
     +		      nlines)
c	write(0,*) 'PREPRDES: nlines=', nlines

	if (unit .ne. 5 ) then
	  close( unit, err=999 )
	endif

999	return
	end

C*******************************************************************************
C  SUBROUTINE: pdeswrite
c
C  PURPOSE: To associate the descriptor file with a unit, and open the
c	    unit for writing
C
C  ARGUMENTS: unit (INPUT) - the unit to write to
c	      des ( INPUT ) - the name of the descriptor file
C	      count (INPUT) - The number of a column corresponding to its
c			       order in a file record.
c			       An array of integers gotten from the first
c			       column of the descriptor file
c
c	      number (INPUT) - The number of repetitions of a column in
c				a file record.	An array of integers gotten
c				from the second column of the descriptor file
c
c	      type (INPUT) - data type of each column of a file record.
c			      An array of strings gotten from the third column
c			      of the descriptor file
c
c	      stitle (INPUT) - The short name of each column of a file record.
c				An array of strings of length 8 gotten from the
c				fourth column of the descriptor file
c
c	      ltitle (INPUT) - The long name of each column of a file record.
c				An array of strings of length 32 gotten from
c				the fifth column of the descriptor file
c
c	      units (INPUT) - The proper measuring units to use for each
c			       column of a file record.  An array of strings
c			       gotten from the sixth column of the descriptor
c			       file
c
c	      format (INPUT) - The recommended format for each column of
c				a file record.	An array of strings gotten
c				from the seventh column of the descriptor file
c
c	      nlines (INPUT) - The number of lines in the descriptor file
c
C  EXAMPLE:
C
C  CALLED BY: all pipes except pirtm and pirtm2
C
C  CALLS: index
C
C  OPERATING SYSTEM / PORTABILITY NOTES:  portable
c
C  HISTORY :
c     9/15/89  Carol Chang.  Created it.
C*******************************************************************************
	subroutine pdeswrite(unit, des,header,stitle,ltitle,
     &			    nlines)
	character*(*) des
	character*(*) ltitle(*)
	character*(*)  stitle(*)
	character*(*) header
	integer  nlines, unit




c
c  Append '.des' to <des> to form the name of the description file to open
c
	if( unit .ne. 6 ) then
c	  open(unit=unit, file=outfil, status='new')
	  call openform(unit, des, 'new')
	endif
c
c  Output the descriptor file
c

	call wdesfil(unit, header, stitle, ltitle,
     +		     nlines)

	if( unit .eq. 6 ) then
	  write(6,*) "'",'end',"'",'   ',"'",'end',"'"
	else
	  close( unit )
	endif

999	return
	end


c*************************************************************************

C*******************************************************************************
C  SUBROUTINE:	adddesline
c
C  PURPOSE:  To add a line( a new field ) to a descriptor file in memory
c	     ( not physically alter content of the file )
C
C  ARGUMENTS: pos(INPUT) --  the line which this new line is to become
c			       i.e. 8 -- the line to be added will be the
c			       8th line
C	      newcount (INPUT) - The number of a column corresponding to its
c			       order in a file record.
c
c	      newnumber (INPUT) - The number of repetitions of a column in
c				a file record.
c
c	      newtype (INPUT) - data type of each column of a file record.
c
c	      newstitle (INPUT) - The short name of each column of a file record.
c
c	      newltitle (INPUT) - The long name of each column of a file record.
c
c	      newunits (INPUT) - The proper measuring units to use for each
c			       column of a file record.
c
c	      newformat (INPUT) - The recommended format for each column of
c				a file record.
c
C	      count (OUTPUT) - The number of a column corresponding to its
c			       order in a file record.
c			       An array of integers gotten from the first
c			       column of the descriptor file
c
c	      number (OUTPUT) - The number of repetitions of a column in
c				a file record.	An array of integers gotten
c				from the second column of the descriptor file
c
c	      type (OUTPUT) - data type of each column of a file record.
c			      An array of strings gotten from the third column
c			      of the descriptor file
c
c	      stitle (OUTPUT) - The short name of each column of a file record.
c				An array of strings of length 8 gotten from the
c				fourth column of the descriptor file
c
c	      ltitle (OUTPUT) - The long name of each column of a file record.
c				An array of strings of length 32 gotten from
c				the fifth column of the descriptor file
c
c	      units (OUTPUT) - The proper measuring units to use for each
c			       column of a file record.  An array of strings
c			       gotten from the sixth column of the descriptor file
c
c	      format (OUTPUT) - The recommended format for each column of
c				a file record.	An array of strings gotten
c				from the seventh column of the descriptor file
c
c	      nlines (OUTPUT) - The number of lines in the descriptor file
C
C  EXAMPLE:  To add a line to the descriptor file, irtm15.des passed
c	     to the next pipe, do:
c	call pdesread(7, 'irtm15', count, number, type, stitle,  ltitle,
c     &		     units,format, recl, nlines)
c
c	call adddesline( nlines+1, nlines+1, 1, 'r*4', 'sxpol', ' ', ' ',
c     +			  ' ', count, number, type, stitle, ltitle,
c     +			 units, format, nlines)
c	call pdeswrite(6, des, count, number, type, stitle, ltitle,
c     &		     units,format, nlines)
c
C  CALLED BY: spxy
C
C  CALLS:
C
C  OPERATING SYSTEM / PORTABILITY NOTES:  completely portable
C
C  HISTORY:
c	9/15/89 Carol Chang.  Created it.
c
C*******************************************************************************

	subroutine adddesline(pos, newstitle,
     +			      newltitle, header,stitle, ltitle,
     +			      nlines)
c
c  Parameters to pass in fields of the line to be added
c
	character*(*)  newltitle
	character*(*)  newstitle 
	integer newcount, newnumber, pos
c
c  Parameters to pass in the arrays containing columns of the old des file
c
	character*(*) ltitle(*)
	character*(*)  header, stitle(*)
	integer  nlines

c
c  Local Variables
c
	integer tline
c
c  Validate the line number
c
	if( pos .lt. 1) then
	  write(0,*) 'ADDDESLINE : line number must be >= 1'
	  stop
	endif

	if( pos .gt. nlines + 1 ) then
	  write(0,*) 'ADDDESLINE : line number exceeded file size range'
	  stop
	endif
c
c  Shift everything down 1 to enable the addition of this line
c
	tline = nlines + 1
20	if( tline .eq. pos ) then
	  goto 21
	else
	  stitle(tline) = stitle(tline -1)
	  ltitle(tline) = ltitle(tline -1)
	  tline = tline - 1
	  goto 20
	endif
21	continue
c
c  Insert the line to be added at line # pos
c
	  stitle(pos) = newstitle
	  ltitle(pos) = newltitle
c
c  Mark the ending in  all the arrays
c
	  stitle(nlines+2) = char(0)
	  ltitle(nlines+2) = char(0)
c
c  Record length increase by 1
c
	nlines = nlines + 1

	return
	end


C*******************************************************************************
C  SUBROUTINE:	subdesline
c
C  PURPOSE:  To delete a line from the descriptor file contained in
c	     memory
C
C  ARGUMENTS:
c	      pos( INPUT ) - the number of the line which is to be deleted
C	      count (OUTPUT) - The number of a column corresponding to its
c			       order in a file record.
c			       An array of integers gotten from the first
c			       column of the descriptor file
c
c	      number (OUTPUT) - The number of repetitions of a column in
c				a file record.	An array of integers gotten
c				from the second column of the descriptor file
c
c	      type (OUTPUT) - data type of each column of a file record.
c			      An array of strings gotten from the third column
c			      of the descriptor file
c
c	      stitle (OUTPUT) - The short name of each column of a file record.
c				An array of strings of length 8 gotten from the
c				fourth column of the descriptor file
c
c	      ltitle (OUTPUT) - The long name of each column of a file record.
c				An array of strings of length 32 gotten from
c				the fifth column of the descriptor file
c
c	      units (OUTPUT) - The proper measuring units to use for each
c			       column of a file record.  An array of strings
c			       gotten from the sixth column of the descriptor file
c
c	      format (OUTPUT) - The recommended format for each column of
c				a file record.	An array of strings gotten
c				from the seventh column of the descriptor file
c
c	      nlines (OUTPUT) - The number of lines in the descriptor file
C
C  EXAMPLE:
c	call pdesread(7, 'irtm15', count, number, type, stitle,  ltitle,
c     &		     units,format, nlines)
c
c	call subdesline( nlines+1, count, number, type, stitle, ltitle,
c     +			 units, format, nlines)
c	call pdeswrite(6, des, count, number, type, stitle, ltitle,
c     &		     units,format, nlines)
c
C
C  CALLED BY:
C
C  CALLS:
C
C  OPERATING SYSTEM / PORTABILITY NOTES: completely portable
C
C  HISTORY: 9/15/89 Carol Chang.  Created it
c
C*******************************************************************************


	subroutine subdesline(pos, count, number, type, stitle, ltitle,
     +			      units, format, nlines)
c
c  Parameters to pass in the arrays containing columns of the old des file
c
	character*(*) ltitle(*)
	character*(*) units(*)
	character*(*)  type(*), stitle(*),format(*)
	integer count(*), number(*), nlines, pos

c
c  Local Variables
c
	integer tline
c
c  Validate the line number
c
	if( nlines .lt. 1 )  then
	  write(0,*) 'SUBDESLINE: : file has 0 lines'
	  stop
	else if( pos .lt. 1) then
	  write(0,*) 'SUBDESLINE : line number must be >= 1'
	  stop
	else if( pos .gt. nlines ) then
	  write(0,*) 'SUBDESLINE : file does not contain ',pos,' lines'
	  stop
	endif
c
c  Shift everything down 1 to enable the addition of this line
c
	tline = pos
20	if( tline .eq. nlines + 1 ) then
	  goto 21
	else
	  number(tline) = number(tline + 1)
	  type(tline) = type(tline + 1)
	  stitle(tline) = stitle(tline +1)
	  ltitle(tline) = ltitle(tline +1)
	  units(tline) = units(tline+1)
	  format(tline)=format(tline+1)
	  tline = tline + 1
	  goto 20
	endif
21	continue
c
c File length decrease by 1
c
	nlines = nlines - 1

	return
	end

c
c  Open routines
c
	subroutine openform( myunit, myfile, mystatus)
	  integer myunit
	  character*(*) myfile, mystatus

	  open( unit=myunit, file=myfile, status=mystatus )

	return
	end

	subroutine openunform(myunit, myfile, myaccess,
     +	  mystatus, myrecl)
	  integer myunit, myrecl
	  character*(*) myfile, myaccess, mystatus

	if( myaccess .eq. 'sequential') then
	  open( unit=myunit, file=myfile, access=myaccess,
     +		status=mystatus, form='unformatted' )
	else
	  open( unit=myunit, file=myfile, access=myaccess,
     +		status=mystatus, recl=myrecl*4, form='unformatted')
	endif

	return
	end

	subroutine open5()
	return
	end

	subroutine open6()
	return
	end
c
c  Close pipe routines
c

	integer function close5()
	close(5, iostat=ios)
	close5 = ios
	return
	end

	integer function close6()
	close(6, iostat=ios)
	close6 = ios
	return
	end

	integer function icolnum(colname,colnames,ncolnames)
c
	 character*(*) colname
	 character*(*) colnames(*)
	 character*150 progname
c returns the index in colnames of the string colname, stops if
c column not found.

	 do  i=1,ncolnames


	     if (colname.eq.colnames(i)) then
		     icolnum=i
		     return
	     endif
	  enddo
c colname not present in colnames
	  call getarg(0,progname)
	  write (0,*) 'PROGRAM ', progname(1:index(progname,' ')),':'
	  write (0,*) 'CAN"T FIND COLUMN NAME ',colname,
     &	' IN DESCRIPTOR FILE'
	  stop
	  end

ccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc
ccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc
ccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc

	  subroutine postprocess(value)
	  implicit none
	  character*(*) value
	  integer i

	  if (value.eq.'NULL') then
	      value = ' '
	      return
          endif

	  do i=1,len(value)
	      if (value(i:i).eq.'\\') value(i:i) = ' '
          enddo

	  return
	  end
	      
ccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc
ccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc
ccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc

        subroutine getcmdchar
     &           (keyword,number,reqoropt,ifound, value)
        character*(*) keyword,reqoropt
        character*(*) value
ccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc
c  getcmdchar  - gets keyword character values from command line argument
c
c       inputs  keyword         keyword value
c               number          number of values to look for in keyword
c               reqoropt        'optional' or 'required'
c               ifound          ifound=1 if the keyword is contined
c                               in the command line, ifound=0 if not
c       outputs:value           the value(s) specified in the command
c                               line
c
c       examples:
c
c                for the command line:
c
c       test inp=infile.dat,otherfile.dat  out=outfile.dat
c
c                and for the call
c
c
c       call getcmdchar('inp',2,'required',ifound, value)
c
c               getcmdchar returns:
c
c               keyword='inp'
c               number=2
c               reqoropt='required'
c
c               ifound=1
c               value(1)='infile.dat'
c               value(2)='otherfile.dat'
c
c
c               if a required keyword is not present, getcmdchar
c               stops and writes an error message to LUN=0
c 'command line error: 'progname' keyword 'keyword' not present

c               if a keyword has the wrong number of values,getcmdchar
c               stops and writes an error message to LUN=0
c 'command line error: 'progname' keyword 'keyword' requires 'number' values
c
c
c               if an optional keyword is not present, getcmdchar
c               returns ifound=0
c
c@ccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc
       character*150 arg,key,progname
        ifound=0
        narg=iargc()
        call getarg(0,progname)
c find length of keyword for error message printout
        if (index(keyword,' ').eq.0) then
                keywordlength=len(keyword)
        else
                keywordlength=index(keyword,' ')
        endif
c add keyword to list of legal keywords
        call chkcmdkey(keyword)
        if (reqoropt.eq.'required') then
           if (narg.eq.0) then
                      write (0,*) 'COMMAND LINE ERROR IN PROGRAM ',
     &   progname(1:index(progname,' ')),
     &  '- REQUIRED KEYWORD ',
     &   keyword(1:keywordlength), ' IS NOT PRESENT'
                      stop
           endif

                do i=1,narg
                        call getarg(i,arg)
                        call getparam (arg,key)
                        if (key.eq.keyword) then
                                call getnumval(arg,num)
                                if (num.ne.number) then
                                        write (0,*)
     &'COMMAND LINE ERROR IN PROGRAM ',
     & progname(1:index(progname,' ')),
     &'- KEYWORD ',
     & keyword(1:keywordlength),' REQUIRES ',
     &    number, ' VALUES, BUT ', num, ' VALUES WERE SUPPLIED'
                                        stop
                                else
                                    call getcharval(arg,value)
				    call postprocess(value)
                                    ifound=1
                                    return
                                endif
                        endif
                enddo
                      write (0,*)
     &  'COMMAND LINE ERROR IN PROGRAM ',
     &  progname(1:index(progname,' ')),'- REQUIRED KEYWORD ',
     &  keyword(1:keywordlength),' IS NOT PRESENT'
                      stop
          else  if (reqoropt.eq.'optional') then
                if (narg.eq.0) return
                do i=1,narg
                        call getarg(i,arg)
                        call getparam (arg,key)
                        if (key.eq.keyword) then
                                call getnumval(arg,num)
                                if (num.ne.number) then
                                        write (0,*)
     &'COMMAND LINE ERROR IN PROGRAM ',
     & progname(1:index(progname,' ')),'- KEYWORD  ',
     & keyword(1:keywordlength),' REQUIRES ',
     &  number, ' VALUES, BUT ', num, ' VALUES WERE SUPPLIED'
                                        stop
                                else
                                    call getcharval(arg,value)
				    call postprocess(value)
                                    ifound=1
                                   return
                                endif
                        endif
                enddo
          else
                stop 'bad value for reqoropt'
          endif
          end
c
        subroutine getcmdreal
     &           (keyword,number,reqoropt, ifound,value)
        character*(*) keyword,reqoropt
        real*8 value(number)
ccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc
c  getcmdreal  - gets keyword decimal  values from command line argument
c
c       inputs  keyword         keyword value
c               number          number of values to look for in keyword
c               reqoropt        'optional' or 'required'
c               ifound          ifound=1 if the keyword is contined
c                               in the command line, ifound=0 if not
c       outputs:value           the value(s) specified in the command
c                               line
c
c       examples:
c
c                for the command line:
c
c       test lat=1.5,4  out=outfile.dat
c
c                and for the call
c
c
c       call getcmdchar('lat',2,'required',ifound, value)
c
c               getcmdchar returns:
c
c               keyword='lat'
c               number=2
c               reqoropt='required'
c
c               ifound=1
c               value(1)=1.5
c               value(2)=4.0
c
c
c               if a required keyword is not present, getcmdchar
c               stops and writes an error message to LUN=0
c 'command line error: 'progname' keyword 'keyword' not present

c               if a keyword has the wrong number of values,getcmdchar
c               stops and writes an error message to LUN=0
c 'command line error: 'progname' keyword 'keyword' requires 'number' values
c
c
c               if an optional keyword is not present, getcmdchar
c               returns ifound=0
c
c@ccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc
       character*150 arg,key,progname
        ifound=0
        narg=iargc()
        call getarg(0,progname)
c add keyword to list of legal keywords
c find length of keyword for error message printout
        if (index(keyword,' ').eq.0) then
                keywordlength=len(keyword)
        else
                keywordlength=index(keyword,' ')
        endif
        call chkcmdkey(keyword)
        if (reqoropt.eq.'required') then
           if (narg.eq.0) then
                      write (0,*) 'COMMAND LINE ERROR IN PROGRAM ',
     &   progname(1:index(progname,' ')),
     &  '- REQUIRED KEYWORD ',
     &   keyword(1:keywordlength), ' IS NOT PRESENT'
                      stop
           endif

                do i=1,narg
                        call getarg(i,arg)
                        call getparam (arg,key)
                        if (key.eq.keyword) then
                                call getnumval(arg,num)
                                if (num.ne.number) then
                                        write (0,*)
     &'COMMAND LINE ERROR IN PROGRAM ',
     & progname(1:index(progname,' ')),
     &'- KEYWORD ',
     & keyword(1:keywordlength),' REQUIRES ',
     &    number, ' VALUES, BUT ', num, ' VALUES WERE SUPPLIED'
                                        stop
                                else
                                    call getrealval(arg,value)
                                    ifound=1
                                    return
                                endif
                        endif
                enddo
                      write (0,*)
     &  'COMMAND LINE ERROR IN PROGRAM ',
     &  progname(1:index(progname,' ')),'- REQUIRED KEYWORD ',
     &  keyword(1:keywordlength),' IS NOT PRESENT'
                      stop
          else  if (reqoropt.eq.'optional') then
                if (narg.eq.0) return
                do i=1,narg
                        call getarg(i,arg)
                        call getparam (arg,key)
                        if (key.eq.keyword) then
                                call getnumval(arg,num)
                                if (num.ne.number) then
                                        write (0,*)
     &'COMMAND LINE ERROR IN PROGRAM ',
     & progname(1:index(progname,' ')),'- KEYWORD  ',
     & keyword(1:keywordlength),' REQUIRES ',
     &  number, ' VALUES, BUT ', num, ' VALUES WERE SUPPLIED'
                                        stop
                                else
                                    call getrealval(arg,value)
                                    ifound=1
                                   return
                                endif
                        endif
                enddo
          else
                stop 'bad value for reqoropt'
          endif
          end
c
        subroutine getcmdint
     &           (keyword,number,reqoropt,ifound, value)
        character*(*) keyword,reqoropt
        integer*4 value(number)
ccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc
c  getcmdint  - gets keyword integer values from command line argument
c
c       inputs  keyword         keyword value
c               number          number of values to look for in keyword
c               reqoropt        'optional' or 'required'
c               ifound          ifound=1 if the keyword is contined
c                               in the command line, ifound=0 if not
c       outputs:value           the value(s) specified in the command
c                               line
c
c       examples:
c
c                for the command line:
c
c       test ix=1,40.5  out=outfile.dat
c
c                and for the call
c
c
c       call getcmdint('ix',2,'required',ifound, value)
c
c               getcmdchar returns:
c
c               keyword='ix'
c               number=2
c               reqoropt='required'
c
c               ifound=1
c               value(1)=1
c               value(2)=40   (note that it ignores decimal points)
c
c
c               if a required keyword is not present, getcmdchar
c               stops and writes an error message to LUN=0
c 'command line error: 'progname' keyword 'keyword' not present

c               if a keyword has the wrong number of values,getcmdchar
c               stops and writes an error message to LUN=0
c 'command line error: 'progname' keyword 'keyword' requires 'number' values
c
c
c               if an optional keyword is not present, getcmdchar
c               returns ifound=0
c
c@ccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc
       character*150 arg,key,progname
        ifound=0
        narg=iargc()
        call getarg(0,progname)
c find length of keyword for error message printout
        if (index(keyword,' ').eq.0) then
                keywordlength=len(keyword)
        else
                keywordlength=index(keyword,' ')
        endif
c add keyword to list of legal keywords
        call chkcmdkey(keyword)
        if (reqoropt.eq.'required') then
           if (narg.eq.0) then
                      write (0,*) 'COMMAND LINE ERROR IN PROGRAM ',
     &   progname(1:index(progname,' ')),
     &  '- REQUIRED KEYWORD ',
     &   keyword(1:keywordlength), ' IS NOT PRESENT'
                      stop
           endif

                do i=1,narg
                        call getarg(i,arg)
                        call getparam (arg,key)
                        if (key.eq.keyword) then
                                call getnumval(arg,num)
                                if (num.ne.number) then
                                        write (0,*)
     &'COMMAND LINE ERROR IN PROGRAM ',
     & progname(1:index(progname,' ')),
     &'- KEYWORD ',
     & keyword(1:keywordlength),' REQUIRES ',
     &    number, ' VALUES, BUT ', num, ' VALUES WERE SUPPLIED'
                                        stop
                                else
                                    call getintval(arg,value)
                                    ifound=1
                                    return
                                endif
                        endif
                enddo
                      write (0,*)
     &  'COMMAND LINE ERROR IN PROGRAM ',
     &  progname(1:index(progname,' ')),'- REQUIRED KEYWORD ',
     &  keyword(1:keywordlength),' IS NOT PRESENT'
                      stop
          else  if (reqoropt.eq.'optional') then
                if (narg.eq.0) return
                do i=1,narg
                        call getarg(i,arg)
                        call getparam (arg,key)
                        if (key.eq.keyword) then
                                call getnumval(arg,num)
                                if (num.ne.number) then
                                        write (0,*)
     &'COMMAND LINE ERROR IN PROGRAM ',
     & progname(1:index(progname,' ')),'- KEYWORD  ',
     & keyword(1:keywordlength),' REQUIRES ',
     &  number, ' VALUES, BUT ', num, ' VALUES WERE SUPPLIED'
                                        stop
                                else
                                    call getintval(arg,value)
                                    ifound=1
                                   return
                                endif
                        endif
                enddo
          else
                stop 'bad value for reqoropt'
          endif
          end
c
        subroutine getcmdreals
     &          (cdesstitle,ndeslines,nvals, ngood,idescol,vals)
        character*(*) cdesstitle(*)
        real*8 vals(nvals,ndeslines)
        integer*4 idescol(ndeslines)

c cdesstitle is the titles of the columns we are looking for
c ndesline is the number of lines in the des file
c nvals is the number of values to look for in the command arguments

c ngood is the number of arguments that contained the column titles
c idescol is the column numbers of the column titles
c vals(i,j) are the values that were input

        ngood=1
        do ides=1,ndeslines
c look for keyword in argument (and add to list to check...)
                call getcmdreal(cdesstitle(ides),nvals,'optional',
     &                                  ifound,vals(1,ngood))
                if (ifound.eq.1) then
                        idescol(ngood)=ides
                        ngood=ngood+1
                endif
        enddo
        ngood=ngood-1
        return
        end
c
        subroutine chkcmdkey(c)
        character*(*) c
        character*150 keys(2000),arg,progname,key
        data nkey/0/,ibogus/0/
        save
        if (c.eq.'bogus') then
                narg=iargc()
                do iarg=1,narg
                        call getarg(iarg,arg)
                        call getparam(arg,key)
                        do i=1,nkey
                                if (key.eq.keys(i)) goto 10
                        enddo
c argument not found
                        call getarg(0,progname)
                        write (0,*)
     & 'COMMAND LINE ERROR IN PROGRAM ',
     & progname(1:index(progname,' ')),'- KEYWORD ',
     & key(1:index(key,' ')),' IS BOGUS '
                        ibogus=1

c argument found
10                       continue
                enddo
                        if (ibogus.eq.1) then
                          write (0,*) 'NON-BOGUS KEYWORDS INCLUDE:'
                          do i=1,nkey
                           write (0,*)keys(i)(1:index(keys(i),' '))
                          enddo
                          stop
                        endif
        else
                nkey=nkey+1
                keys(nkey)=c
        endif
        return
        end

************************************************************************
c******************************************************************
      subroutine findcol(char,cdesstitle,nc, col)
c finds char in cdessitle, where col =0 if not found
      implicit none
      character*(*) char
      character*(*) cdesstitle(*)
      integer nc,col
      integer i

      col=0
      do i=1,nc
c         write (0,*) i,char(1:index(char,' ')),
c     & cdesstitle(i)(1:(index(cdesstitle(i),' ')-1))
         if(cdesstitle(i)(1:(index(cdesstitle(i),' ')-1)).eq.char) then
            col = i
            return
         endif
      enddo

      write(0,*) 'ERROR: ',char,' not found in desfile.'
      stop
      end

