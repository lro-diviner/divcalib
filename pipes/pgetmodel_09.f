c******************************************************************************
c  PROGRAM: pgetmodel
c
c  PURPOSE: This program looks up thermal model results and adds columns
c  REQUIRED KEYWORDS: 
c
c       jdate=char  -- The column containing observed jdate
c
c       itri=char  -- The column containing model triangle number
c
c       model=char -- The 8-character prefix of the model you want to use
c
c
c  OPTIONAL KEYWORDS:
c
c       des=char -- The descriptor file to describe the format and the
c                    fields of each record of the input data
c                    (the default is the previous pipe).
c
c  OUTPUT COLUMNS
c
c     tmodel  - time interpolated model temperature at itri

c*******************************************************************************


        program pgetmodel_09
        implicit none
        integer M,ND
        parameter (M=5242880) ! for dm_09.tri
        parameter (ND=2)
        include 'pipe1.inc'
        character*80 desfile,junk
        character*48 jdateparam,itriparam
        integer*4 jdatecol,itricol
        integer*4 ios,iunit,ndeslines,ifound
        real*8 jdate,djul1,djul2,djuls(ND)
        real*8 tmodel,djul,di,djul0,doffset
        real*8 ritri
        real*8 djul1old,djul2old,fdjul
        integer*8 itri,idjul,ifdjul
        character*10 cdjul
        real*8 t(ND,M)
        integer*4 id
        real*4 d,f
        character*8 cmodel
cc
c
c dmview5 parameters
c digital moon viewer assuming lambert phase function
c      parameter (M=14412) ! for shackleton.tri
c counters
      integer*4 i,j,k,n
      integer*4 ntri,nsuntri,ntrilist
      integer*4 i1,i2,i3
c woo boundng box variables
        
        call getcmdchar('jdate',1,'required',ifound, jdateparam)
        call getcmdchar('itri',1,'required',ifound, itriparam)
        call getcmdchar('model',1,'required',ifound, cmodel)
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

        call findcol(jdateparam,cdesstitle,ndeslines, jdatecol)
        call findcol(itriparam,cdesstitle,ndeslines, itricol)

c        write (0,*) 'loncol,latcol ',loncol,latcol

       call adddesline(ndeslines+1,'tmodel',
     &       'tmodel', cdesheader,
     &       cdesstitle,cdesltitle,
     &       ndeslines)

c
c  send new descriptor file down pipe
          call pdeswrite(6, cdesname, cdesheader, cdesstitle,
     &               cdesltitle, ndeslines)
c        write (0,*) 'new ndeslines= ',ndeslines,idesrecl
          
          !write (0,*) 'wrote descriptor file '

c check command line for bogus key words
        call chkcmdkey('bogus')
c**************************************************************
      ntri=M
      n=ND
      djul1old=0.d0
      djul2old=0.d0
      di=0.5d0 ! this is the model timestep
c      doffset=0.5d0
c      djuldelta=0.5
c don't load any files at start of run 

c insert pre main loop code
c here is where the work is done...
 10       ios = read5(rdat, ndeslines-1)
          if (ios.eq.-1) goto 999
          jdate=rdat(jdatecol)
          itri=rdat(itricol)
c calculate djul1 and djul2
         idjul=jdate ! round down jdate
         fdjul=jdate-idjul ! calculate fractional jdate
         ifdjul=fdjul/di ! this is how many steps until djul1
         djul1=idjul+ifdjul*di
         djul2=djul1+di
c         write (0,*) 'jd ',jdate,idjul,djul1,djul2
c decide what to do
         if (djul1.eq.djul2old) then
            do i=1,ntri
               t(1,i)=t(2,i)
            enddo
            djul1old=djul1
         else if (djul2.eq.djul1old) then
            do i=1,ntri
               t(2,i)=t(1,i)
            enddo
            djul2old=djul2
         endif
c read in djul1 file if necessary
         if (djul1.ne.djul1old) then
            write (cdjul,'(f10.2)')  djul1
           write (0,*) jdate,' opening file /s1/dap/ltm5/',cmodel,cdjul,
     &     '.txt'
           open
     &   (unit=1,file="/s1/dap/ltm5/"//cmodel//cdjul//".txt"
     &     ,status="old")
         do j=1,M
           read (1,*) t(1,j)
         enddo
         close (unit=1)
         djul1old=djul1
         endif
c read in djul2 file if necessary
         if (djul2.ne.djul2old) then
            write (cdjul,'(f10.2)')  djul2
           write (0,*) jdate,' opening file /s1/dap/ltm5/',cmodel,cdjul,
     &     '.txt'
           open
     &   (unit=1,file="/s1/dap/ltm5/"//cmodel//cdjul//".txt"
     &     ,status="old")
         do j=1,M
           read (1,*) t(2,j)
         enddo
         close (unit=1)
         djul2old=djul2
         endif
c at this point, the proper files are loaded         
c process record normally
             f=(jdate-djul1)/di
             tmodel=t(1,itri)+f*(t(2,itri)-t(1,itri))
             rdat(ndeslines)=tmodel
             ios =  write6(rdat, ndeslines)
        goto 10
 999         continue
        endfile ( unit=6)
        ios=close5()

        stop
        end



        subroutine dfindy(xx,yy,n,x, y)
c
c-----------------------------------------------------------------------
c general purpose linear interpolation routine
c
c  inputs:      xx      x array of values (monotoically increasing)
c               yy      y array of function values
c               n       numer  in x and y arrays
c               x       the value of x that we want to know the best
c                       guess value of y for
c  outputs:     y       best guess linearly interpolated value
c-----------------------------------------------------------------------
c
        real*8 xx(n),yy(n),x,y
c
        if (x.gt.xx(n)) then
                y=yy(n)
        else if (x.lt.xx(1)) then
                y=yy(1)
        else
c find index of xx in x
                call dlocate (xx,n,x, j)
                y=yy(j)+((x-xx(j))/(xx(j+1)-xx(j)))*(yy(j+1)-yy(j))
        endif
        return
        end



        subroutine dlocate (xx,n,x,j)
c given array xx of length n, and given a value x, returns a value j
c such that x is between xx(j) and xx(j+1).  xx must be monotonic, either
c increasing or decreasing.  j=0 or j=n is returned to indicate that
c x is out of range
        real*8 xx(n),x
        jl=0
        ju=n+1
 10                if (ju-jl.gt.1) then
                jm=(ju+jl)/2
                if ((xx(n).gt.xx(1)).eqv.(x.gt.xx(jm))) then
                        jl=jm
                else
                        ju=jm
                endif
        goto 10
        endif
        j=jl
        return
        end

