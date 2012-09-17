*******************************************************************************
c  PROGRAM: pbintag
c
c  PURPOSE: This program adds numerical tags to data based on a user-specified
c binning scheme, and the values of the coordinates at the center of the bin
c
c  REQUIRED KEYWORDS: 
c
c       x=char    -- The first variable you want to index the bins by. The bins
c                    will be indexed as bin(x,y).  For example, one could set
c                    set up the bins to be indexed by "lon" and "lat" ( bin(lon,lat) ).
c
c       y=char    -- See x=char.
c
c
c  xrange=real,real  -- The range of x values you want the bins to encompass (xmin and xmax).
c                          (eg lon=0.0,360.0)
c
c  yrange=real,real  -- The range of y values you want the bins to encompass (ymin and ymax).
c                          (eg lat=-90.0,90.0)
c
c  nbinx=int      -- Number of bins along the x-axis
c   --OR--      
c  deltax=real    -- Increment of the bins along the x-axis
c                        (eg every 2.0 degrees longitude)
c
c  nbiny=int      -- Number of bins along the y-axis
c   --OR--      
c  deltay=real    -- Increment of the bins along the y-axis
c                        (eg every 2.0 degrees latitude)
c
c  OPTIONAL KEYWORDS:
c
c       des=char -- The descriptor file to describe the format and the
c                    fields of each record of the input data
c                    (the default is the previous pipe).
c
c  EXAMPLE:
c
c   pbintag des=irtm_20.des x=lon y=lat xrange=0.0,10.0 yrange=0.0,10.0 \
c         nbinx=120 nbiny=120 < irtm_20.data
c
c
c                                                          DAP
c                                                          2002 May 8
c
c*******************************************************************************


        program pbintag
        include 'pipe1.inc'
        implicit none
        character*80 desfile,xparam,yparam,newdesfile
	character*12 junk
        real*8    xrange(2),yrange(2),xlen,ylen
        integer nbinx,nbiny,maxbin,ifound,i
        real*8    deltax,deltay
        integer iunit,ndeslines,ncon,idescol(MAXCOL),ios
        integer xbin,ybin,nbin,xparamcol,yparamcol
        real*8 zbin

        call getcmdchar('x',1,'required',ifound, xparam)
        call getcmdchar('y',1,'required',ifound, yparam)

        call getcmdreal('xrange',2,'required',ifound, xrange)
        call getcmdreal('yrange',2,'required',ifound, yrange)

	xlen = abs(xrange(1)-xrange(2))
	ylen = abs(yrange(1)-yrange(2))

        call getcmdint('nbinx',1,'optional',ifound, nbinx)
        if(ifound.eq.0) then
           call getcmdreal('deltax',1,'required',ifound, deltax)
           if(deltax.le.0.0) then
              write(0,*) 'ERROR in PBIN: deltax <= 0 : ',deltax
              stop
           endif
           nbinx = nint(xlen/deltax)
        else 
           deltax = xlen / real(nbinx)
        endif
        if(nbinx.le.0.0) then
           write(0,*) 'ERROR in PBIN: nbinx <= 0 : ',nbinx
           stop
        endif
   
  
        call getcmdint('nbiny',1,'optional',ifound, nbiny)
        if(ifound.eq.0) then
           call getcmdreal('deltay',1,'required',ifound, deltay)
           if(deltay.le.0.0) then
              write(0,*) 'ERROR in PBIN: deltay <= 0 : ',deltay
              stop
           endif
           nbiny = nint(ylen/deltay)
        else 
           deltay = ylen / real(nbiny)
        endif
        if(nbiny.le.0.0) then
           write(0,*) 'ERROR in PBIN: nbiny <= 0 : ',nbiny
           stop
        endif

        maxbin = nbinx*nbiny



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

        call findcol(xparam,cdesstitle,ndeslines, xparamcol)
        call findcol(yparam,cdesstitle,ndeslines, yparamcol)

        write (0,*) 'xparamcol= ',xparamcol,' yparamcol= ',yparamcol
        write(0,100) 'nbinx = ',nbinx,', deltax = ',deltax
        write(0,100) 'nbiny = ',nbiny,', deltay = ',deltay
	write (0,100) 'xmin = ',xrange(1), 'xmax= ',xrange(2)
	write (0,100) 'ymin = ',yrange(1),'ymax= ',yrange(2)

100     format(a8,i4,a11,f6.2)


        if (ifound.eq.0) then
c add a line to the descriptor file
c          write (0,*) 'ndeslines= ', ndeslines,idesrecl

       call adddesline(ndeslines+1,'tag',
     &       'tag', cdesheader,
     &       cdesstitle,cdesltitle,
     &       ndeslines)

c          write (0,*) 'ndeslines= ', ndeslines,idesrecl

       call adddesline(ndeslines+1,'xtag','xtag',cdesheader,
     &       cdesstitle,cdesltitle,
     &       ndeslines)

c          write (0,*) 'ndeslines= ', ndeslines,idesrecl

       call adddesline(ndeslines+1,'ytag','ytag',cdesheader,
     &       cdesstitle,cdesltitle,
     &       ndeslines)

          write (0,*) 'ndeslines= ', ndeslines

c
c  send new descriptor file down pipe
          call pdeswrite(6, cdesname, cdesheader, cdesstitle,
     &               cdesltitle, ndeslines)
        endif
c        write (0,*) 'new ndeslines= ',ndeslines,idesrecl


c check for 'newdes' in command line (this is for creating a new descriptor
c file in one's filesystem, if desired.
c

        call getcmdchar('newdes',1,'optional',ifound, newdesfile)
        if(ifound.eq.1) then
           open (unit=10,file=newdesfile,status='unknown')
c write des header
	 write (0,*) "'",cdesheader,"'"
           call wdesfil(10, idescount,idesnumber,cdestype,
     &                     cdesstitle,cdesltitle,cdesunits,
     &                     cdesformat,ndeslines)
           close(unit=10)
        endif  



c check command line for bogus key words
        call chkcmdkey('bogus')
        i=0
10           ios = read5(rdat, ndeslines-3)
          if( ios .eq. -1 ) goto 999
          
          if 
     &  (rdat(xparamcol).ge.xrange(1).and.rdat(xparamcol).lt.xrange(2))
     & then
         xbin =1+((rdat(xparamcol) - xrange(1))/xlen)*nbinx
         else
            goto 10
         endif

       if
     & (rdat(yparamcol).ge.yrange(1).and.rdat(yparamcol).lt.yrange(2))
     & then
         ybin =1+((rdat(yparamcol) - yrange(1))/ylen)*nbiny
         else
            goto 10
      endif


      nbin = (ybin-1)*nbinx + xbin
      zbin=nbin
      rdat(ndeslines-2)=zbin
      rdat(ndeslines-1)=
     & xrange(1)+(xrange(2)-xrange(1))*(xbin-0.5)/float(nbinx)

      rdat(ndeslines)=
     & yrange(1)+(yrange(2)-yrange(1))*(ybin-0.5)/float(nbiny)

      i=i+1

c      write (0,*) i,rdat(xparamcol),xbin,rdat(yparamcol),ybin, zbin

        ios =  write6(rdat, ndeslines)
        goto 10
 999         continue
c             write(0,*) 'Number through pbintag = ', i
        endfile ( unit=6)
        ios=close5()

        stop
        end


