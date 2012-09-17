c******************************************************************************
c  PROGRAM: pitri2lonlatalt_09
c
c  PURPOSE: This program computes center lon, lat and altitudes for digital
c           moon triangles
c  REQUIRED KEYWORDS: 
c
c       itri=char  -- The digital moon triangle number
c

c  OPTIONAL KEYWORDS:
c
c       des=char -- The descriptor file to describe the format and the
c                    fields of each record of the input data
c                    (the default is the previous pipe).
c
c  OUTPUT COLUMNS
c
c     dmlon  - triangle center latitude (deg)
c     dmlat - triangle center longitude (deg)
c     dmalt - triangle center altitude (km)
c     dma - triangle area  (sq km)

c*******************************************************************************


        program p3dgeom
        implicit none
        include 'pipe1.inc'
        character*80 desfile,junk
        character*48 itriparam
        integer*4 itricol
        integer*4 ios,iunit,ndeslines,ifound
        integer*4 itri,ntri,i,j,k
cc
c
c dmview5 parameters
      integer M
c digital moon viewer assuming lambert phase function
c      parameter (M=14412) ! for shackleton.tri
c      parameter (M=2880000) ! for 80s_grid3.tri
      parameter (M=5242880 ) ! for 80s_grid3.tri
      real*4 tri(3,3,M),tric(3,M),trin(3,M),tria(M)
      real*4 dlat(M),dlon(M),htri(M)
      real*4 rplanet,pi
      data rplanet/1737.4/
      save
        
        pi=acos(-1.0)

        call getcmdchar('itri',1,'required',ifound, itriparam)
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

        call findcol(itriparam,cdesstitle,ndeslines, itricol)

c        write (0,*) 'loncol,latcol ',loncol,latcol

       call adddesline(ndeslines+1,'dmlon',
     &       'dmlon', cdesheader,
     &       cdesstitle,cdesltitle,
     &       ndeslines)

c       write (0,*) 'added desline, ndeslines= ',ndeslines

       call adddesline(ndeslines+1,'dmlat',
     &       'dmlat', cdesheader,
     &       cdesstitle,cdesltitle,
     &       ndeslines)

c       write (0,*) 'added desline, ndeslines= ',ndeslines


       call adddesline(ndeslines+1,'dmalt',
     &       'dmalt', cdesheader,
     &       cdesstitle,cdesltitle,
     &       ndeslines)

c add itri to descriptior file
       call adddesline(ndeslines+1,'dma',
     &       'dma', cdesheader,
     &       cdesstitle,cdesltitle,
     &       ndeslines)

c       write (0,*) 'added desline, ndeslines= ',ndeslines


       !write (0,*) 'added desline, ndeslines= ',ndeslines


c
c  send new descriptor file down pipe
          call pdeswrite(6, cdesname, cdesheader, cdesstitle,
     &               cdesltitle, ndeslines)
c        write (0,*) 'new ndeslines= ',ndeslines,idesrecl
          
          !write (0,*) 'wrote descriptor file '

c check command line for bogus key words
        call chkcmdkey('bogus')
c**************************************************************
c insert pre main loop code
      ntri=M
      pi=acos(-1.)
c      write (0,*) 'ntri= ',ntri, ' nsuntri= ',nsuntri
c      write (0,*) 'rmax= ', rmax
c process arguments
c carg(1) is the triangle file
c carg(2) is the sun file

c      write (0,*) 'reading triangle file'
c read in how many triangles
         open (unit=1,file=
c     & '/u/paige/smeeker/digmoon/lev10/selene/dm4_sg_lev10_global.tri',
     & '/u/paige/dap/pipesv3/dm_lev09.r4tri9',
     &     status='old',form='unformatted',access='direct',recl=9*4)
         ntri=M
c         read (1,*) ntri
c here is where we would malloc
c         write (0,*) 'start reading tri file'
         do i=1,ntri
            read (1,rec=i) ((tri(j,k,i),j=1,3),k=1,3)
            call ctricna(tri(1,1,i),tric(1,i),trin(1,i),tria(i))
            call xyz2latlon(tric(1,i),tric(2,i),tric(3,i),rplanet,
     &           dlat(i),dlon(i),htri(i))
c     if (mod(i,10000).eq.0) write (0,*) 'read ',i
         enddo
c         write (0,*) 'end reading tri file'
         close (unit=1)
c******************************************************************************\

10           ios = read5(rdat, ndeslines-4) ! very important that -4 
          if( ios .eq. -1 ) goto 999
          

          itri=nint(rdat(itricol))
          rdat(ndeslines-3)=dlon(itri)
          rdat(ndeslines-2)=dlat(itri)
          rdat(ndeslines-1)=htri(itri)
          rdat(ndeslines)=tria(itri)

          ios =  write6(rdat, ndeslines)



        goto 10
 999         continue
        endfile ( unit=6)
        ios=close5()

        stop
        end

        subroutine xyz2latlon(x,y,z,r0, dlat,dlon,htri)
        real*4 x,y,z,dlat,dlon,r,r0,xi,yi,zi,htri
        real*4 lat,lon,pi,r1
        pi=dacos(-1.d0)
        r=sqrt(x**2+y**2+z**2)
c find where x,y,z intersect sphere
        xi=(r0/r)*x
        yi=(r0/r)*y
        zi=(r0/r)*z
c find latitude
        lat=asin(zi/r0)
        dlat=lat*180.d0/pi
c find projection onto equator
        r1=sqrt(x**2+y**2)
        lon=acos(x/r1)
        if (y.lt.0.d0) lon=-lon
        dlon=lon*180.d0/pi
        htri=r-r0
        return
        end

        subroutine ctricna(t, tc,tn,tarea)
c calculates triangle centers (tc),normals (tn) and triangele areas (tarea)
        real*4 t(3,3),tn(3),tarea,u(3),v(3),cross(3),tc(3)
c calculate triangle centriod
        tc(1)=(t(1,1)+t(1,2)+t(1,3))/3.
        tc(2)=(t(2,1)+t(2,2)+t(2,3))/3.
        tc(3)=(t(3,1)+t(3,2)+t(3,3))/3.
c set u and v, the difference vectors between the verticies
        do i=1,3
                u(i)=t(i,2)-t(i,1)
                v(i)=t(i,3)-t(i,1)
        enddo
c       write (*,*) 'u= ',u
c       write (*,*) 'v= ',v

c calculate u cross v, which is tn
        tn(1)=u(2)*v(3)-u(3)*v(2)
        tn(2)=u(3)*v(1)-u(1)*v(3)
        tn(3)=u(1)*v(2)-u(2)*v(1)
c calculate triangle area, which is 0.5*uXv
        crossmag=sqrt(tn(1)**2+tn(2)**2+tn(3)**2)
        tarea=0.5*crossmag
c normalize triange unit vectors to 1
        tn(1)=tn(1)/crossmag
        tn(2)=tn(2)/crossmag
        tn(3)=tn(3)/crossmag
        return
        end


