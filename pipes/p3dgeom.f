c******************************************************************************
c  PROGRAM: p3dgeom
c
c  PURPOSE: This program used ray tracing to recalculate geometry
c  REQUIRED KEYWORDS: 
c
c       dem=demfile -- Which dem file to use
c
c       lon=char  -- The column containing original east longitude
c
c       lat=char  -- The column containing original latitude
c
c       sclat=char -- the column containing spacecraft latitude
c 
c       sclon=char -- the column spacecraft longitude
c
c       scrad=char -- the column containing the spacecraft radius
c
c       sunlat=char -- the column containing the subsolar latitude
c
c       sunlon=char -- the column containing the subsolar longitude
c
c       sundst=char - the column containing the sun-planet distance (AU)
c
c  OPTIONAL KEYWORDS:
c
c       des=char -- The descriptor file to describe the format and the
c                    fields of each record of the input data
c                    (the default is the previous pipe).
c
c  OUTPUT COLUMNS
c
c     tlat  - target latitude
c     tlon - target longitude
c    talt - target altitude
c    tslope - target slope
c    temis - target emission angle
c    tinc - target incidence angle
c    tinsol - target insolation 
c    tphase - target phase angle
c    taz - target solar azimuth angle
c    itri - triangle number of intersection

c*******************************************************************************


        program p3dgeom
        implicit none
        include 'pipe1.inc'
        character*80 desfile,junk
        character*48 lonparam,latparam,sclatparam,sclonparam,scradparam
        character*48 demfile
        character*48 sunlatparam,sunlonparam,sundstparam
        integer*4 loncol,latcol,scloncol,sclatcol,scradcol
        integer*4 sunlatcol,sunloncol,sundstcol
        integer*4 ios,iunit,ndeslines,ifound
        real*8 tlon,tlat,talt,lon,lat,scrad
        real*8 temis,tinc,tphase,tinsol,tslope,taz
cc
c
c dmview5 parameters
      integer M,MSUN,MNVOXPERTRI,MNTRILIST,NGRID1,NGRID2,NGRID3
c digital moon viewer assuming lambert phase function
c      parameter (M=14412) ! for shackleton.tri
c      parameter (M=20971520) 
c      parameter (M=5242880) ! for level 9 digital moon
c      parameter (MNVOXPERTRI=6,MNTRILIST=100)
c      parameter (NGRID1=580,NGRID2=580,NGRID3=580) ! 80s_grid3.tri parameters -  these parameters need to be hardwired after the first run
c      parameter (NGRID1=25,NGRID2=25,NGRID3=3) ! shackleton.tri grid parameters -  these parameters need to be hardwired after the first run
c scene triangles
      real*4 d
      real*4, allocatable :: tri(:,:,:)!,tric(:,:),trin(:,:),tria(:)
      real*4 tric(3),trin(3),tria
c      real*4, allocatable :: dlat(:),dlon(:),alt(:)
      !real*4 tri(3,3,M),tric(3,M),trin(3,M),tria(M),dlat(M),dlon(M),alt(M)
c      real*4 alt(M)
c grid parameters
      real*4 voxsize(3),gridmin(3),gridmax(3)
      integer*4 ngrid(3)
      integer*4, allocatable ::  lltri(:) ! lltri(MNVOXPERTRI*M)
      integer*4, allocatable ::  llpoint(:) !llpoint(MNVOXPERTRI*M)
      integer*4, allocatable ::  trilist (:) !trilist(MNTRILIST)
      integer*4 nll,llend
      integer*4, allocatable:: grid(:,:,:) !grid(NGRID1,NGRID2,NGRID3)
      integer*4 nvoxpertri,ntrilist

      real*4 rplanet
c      external voxgrid_raytrace3,voxgrid_raytrace2
      integer*4 voxgrid_raytrace3,voxgrid_raytrace2
      integer*4 izero,iplus1
c subsolar parameters
      real*4 dsslon,dsslat,rsunau,oneau,s00
      character*80 filename
      real*4 sv(3)
c viewer parameters
      real*4 dvlon,dvlat,rv,v(3)
      real*4 p(3),dirmag,trioutmag,triout(3)
c photometric parameters
      real*4 hs0,dir(3),ddni,r,fluxsun,cosi,dintmin
c pf phase function parameters
      real*4 rpf,pf02,b,c,h,x1,x2,b0,pi,mu0,mu,cosg,tango2
      real*4 rtri,tv(3),g
      real*4 ev(3),rev
      real*4 cosg2,dgmin,cosgmin,rmag,uvr(3)
      real*4 rmax,dlatmax,raxis
c input parameters
      real*4 sunlon,sunlat,sclon,sclat,scalt,clon,clat,sundst
c output parameters
      real*4 t(3),tradius,trxy,trange,dotp
c counters
      integer*4 i,j,k,isun,iresult
      integer*4 ntri,nsuntri
      integer*4 i1,i2,i3
c woo boundng box variables
      integer hitboundingbox,inside,ihit,ihitbox,ihittri
      real*4 coord(3)
c data statements
      data voxsize/8.,8.,8./ !km
      data oneau/1.4958e8/ !km
      data rplanet/1737.4/ !km
      data s00/1369.0/ ! W m-2

c      data asurf/M*0.1/
      data b,c,h,x1,x2,b0/0.249,0.407,0.0345,0.064,0.3,1.17/

      write(0,*) 'p3dgeom: Start'

        
        pi=dacos(-1.d0)

        call getcmdchar('lon',1,'required',ifound, lonparam)
        call getcmdchar('lat',1,'required',ifound, latparam)
        call getcmdchar('sclat',1,'required',ifound, sclatparam)
        call getcmdchar('sclon',1,'required',ifound, sclonparam)
        call getcmdchar('scrad',1,'required',ifound, scradparam)
        call getcmdchar('sunlat',1,'required',ifound, sunlatparam)
        call getcmdchar('sunlon',1,'required',ifound, sunlonparam)
        call getcmdchar('sundst',1,'required',ifound, sundstparam)
        call getcmdchar('dem',1,'required',ifound, demfile)


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

        call findcol(lonparam,cdesstitle,ndeslines, loncol)
        call findcol(latparam,cdesstitle,ndeslines, latcol)
        call findcol(sclatparam,cdesstitle,ndeslines, sclatcol)
        call findcol(sclonparam,cdesstitle,ndeslines, scloncol)
        call findcol(scradparam,cdesstitle,ndeslines, scradcol)
        call findcol(sunlatparam,cdesstitle,ndeslines, sunlatcol)
        call findcol(sunlonparam,cdesstitle,ndeslines, sunloncol)
        call findcol(sundstparam,cdesstitle,ndeslines, sundstcol)

c        write (0,*) 'loncol,latcol ',loncol,latcol

       call adddesline(ndeslines+1,'tlon',
     &       'tlon', cdesheader,
     &       cdesstitle,cdesltitle,
     &       ndeslines)

c       write (0,*) 'added desline, ndeslines= ',ndeslines

       call adddesline(ndeslines+1,'tlat',
     &       'tlat', cdesheader,
     &       cdesstitle,cdesltitle,
     &       ndeslines)

c       write (0,*) 'added desline, ndeslines= ',ndeslines


       call adddesline(ndeslines+1,'talt',
     &       'talt', cdesheader,
     &       cdesstitle,cdesltitle,
     &       ndeslines)

       call adddesline(ndeslines+1,'tslope',
     &       'tslope', cdesheader,
     &       cdesstitle,cdesltitle,
     &       ndeslines)


       call adddesline(ndeslines+1,'temis',
     &       'temis', cdesheader,
     &       cdesstitle,cdesltitle,
     &       ndeslines)


       call adddesline(ndeslines+1,'tinc',
     &       'tinc', cdesheader,
     &       cdesstitle,cdesltitle,
     &       ndeslines)


       call adddesline(ndeslines+1,'tphase',
     &       'tphase', cdesheader,
     &       cdesstitle,cdesltitle,
     &       ndeslines)

       call adddesline(ndeslines+1,'taz',
     &       'taz', cdesheader,
     &       cdesstitle,cdesltitle,
     &       ndeslines)

       call adddesline(ndeslines+1,'tinsol',
     &       'tinsol', cdesheader,
     &       cdesstitle,cdesltitle,
     &       ndeslines)

c add itri to descriptior file
       call adddesline(ndeslines+1,'itri',
     &       'itri', cdesheader,
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

c Check first record for input.

      write(0,*) 'p3dgeom: Checking first record'

      ios = read5(rdat, ndeslines-10) ! very important that -10 
      if( ios .eq. -1 ) then
          write(0,*) 'p3dgeom: NO RECORDS FOUND, EXITING'
          goto 999
      endif

      write(0,*) 'p3dgeom: Reading models and allocating memory'

c**************************************************************
c insert pre main loop code
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
     & '/u/paige/dap/pipesv3/'//demfile,
     &     status='old',form='unformatted',access='direct',recl=9) ! this may be different from g77
c read first record to get info about grid
         read (1,rec=1) ntri,voxsize(1),voxsize(2),voxsize(3),
     & nvoxpertri,ntrilist,izero,izero,izero
         ntrilist=ntrilist*50 ! kluge to make it work for now
c      ntri=M
c         write (0,*) 'dem parameters',ntri,voxsize,nvoxpertri,ntrilist

      nll=nvoxpertri*ntri
      ntrilist=ntrilist
c next we do mallocs
c      write (0,*) 'allocating triangle arrays'
       allocate(tri(3,3,ntri),stat=ios)
       if (ios.gt.0)  then
          write (0,*) ' cannot allocate tri '
          stop
       endif
c       allocate(tric(3,ntri),stat=ios)
c       if (ios.gt.0)  then
c          write (0,*) ' cannot allocate tric '
c          stop
c       endif
c       allocate(trin(3,ntri),stat=ios)
c       if (ios.gt.0)  then
c          write (0,*) ' cannot allocate trin '
c          stop
c       endif
c       allocate(tria(ntri),stat=ios)
c       if (ios.gt.0)  then
c          write (0,*) ' cannot allocate tria '
c          stop
c       endif
c      ngrid(1)=NGRID1
c      ngrid(2)=NGRID2
c      ngrid(3)=NGRID3
c         read (1,*) ntri
c here is where we would malloc
c         write (0,*) 'start reading tri file, ntri= ',ntri
         do i=1,ntri
c            if (mod(i,100000).eq.0) write (0,*) i
c            if (i.eq.1) write (0,*) 'about to read tri ',i

c            if (i.eq.ntri) write (0,*) 'about to read tri ',i
c            iplus1=i+1
            read (1,rec=i+1) ((tri(j,k,i),j=1,3),k=1,3)
c           if (mod(i,100000).eq.0)write (0,*)((tri(j,k,i),j=1,3),k=1,3)

c            write (0,*) ((tri(j,k,i),j=1,3),k=1,3)
c calculate triangle parameters
c            call ctricna(tri(1,1,i),tric(1,i),trin(1,i),tria(i))
         enddo
c         write (0,*) 'end reading tri file'
 2              continue
         close (unit=1)
c         write (0,*) 'calling gridsetup'
         call gridsetup(voxsize,ntri,tri, gridmin,gridmax,ngrid)
c         write (0,*) 'gridmin ', gridmin
c         write (0,*) 'gridmax ' , gridmax
c         write (0,*) 'ngrid ', ngrid
c next we malloc grid
       allocate(grid(ngrid(1),ngrid(2),ngrid(3)),stat=ios)
       if (ios.gt.0)  then
          write (0,*) ' cannot allocate grid'
          stop
       endif
       nll=nvoxpertri*ntri
       allocate(lltri(nvoxpertri*ntri),stat=ios)
       if (ios.gt.0)  then
          write (0,*) 'cannot allocate lltri'
          stop
       endif
       allocate(llpoint(nvoxpertri*ntri),stat=ios)
       if (ios.gt.0)  then
          write (0,*) ' cannot allocate llpoint'
          stop
       endif
       allocate(trilist(ntrilist),stat=ios)
       if (ios.gt.0)  then
          write (0,*) ' cannot allocate trilist'
          stop
       endif
c         write (0,*) 'calling gridpopulate'
         call gridpopulate (voxsize,ntri,tri,gridmin,gridmax,ngrid,grid,
     & lltri,llpoint,nll,llend,trilist,ntrilist)
c         write (0,*) 'nll= ',nll,' llend= ',llend
c******************************************************************************\

c at this point, the calculation has been set up. the next step is to read in t\
c input data and to get to work processing.

      write(0,*) 'p3dgeom: Looping over records'

10    continue

          clat=rdat(latcol)
          clon=rdat(loncol)
          sclat=rdat(sclatcol)
          sclon=rdat(scloncol)
          rv=rdat(scradcol)
          sunlat=rdat(sunlatcol)
          sunlon=rdat(sunloncol)
          sundst=rdat(sundstcol)
c          write (0,*) clat,clon,sclat,sclon,rv,sunlat,sunlon,sundst

            v(3)=rv*sin(sclat*pi/180.)
            v(1)=rv*cos(sclat*pi/180.)*cos(sclon*pi/180.)
            v(2)=rv*cos(sclat*pi/180.)*sin(sclon*pi/180.)
c            write (0,*) 'v= ',v
c view direction
            p(3)=rplanet*sin(clat*pi/180.)
            p(1)=rplanet*cos(clat*pi/180.)*cos(clon*pi/180.)
            p(2)=rplanet*cos(clat*pi/180.)*sin(clon*pi/180.)
c            write (0,*) 'p= ',p
            dir(1)=p(1)-v(1)
            dir(2)=p(2)-v(2)
            dir(3)=p(3)-v(3)
            dirmag=sqrt(dir(1)**2+dir(2)**2+dir(3)**2)
            dir(1)=dir(1)/dirmag
            dir(2)=dir(2)/dirmag
            dir(3)=dir(3)/dirmag
c            write (0,*) 'dir= ',dir
c check dirmag
c            write (0*,*) 'target ',v(1)+dirmag*dir(1),v(2)+dirmag*dir(2),
c     & v(3)+dirmag*dir(3)


c  use woo boundingbox to find where ray intersects grid
            ihitbox=hitboundingbox(gridmin,gridmax,v,dir, inside,coord)
            if (ihitbox.eq.0) then ! level 0
c               write (0,*) 'ihitbox=0 '
          rdat(ndeslines-9)=-999.
          rdat(ndeslines-8)=-999.
          rdat(ndeslines-7)=-999.
          rdat(ndeslines-6)=-999.
          rdat(ndeslines-5)=-999.
          rdat(ndeslines-4)=-999.
          rdat(ndeslines-3)=-999.
          rdat(ndeslines-2)=-999.
          rdat(ndeslines-1)=-999.
          rdat(ndeslines)=-999.

          ios =  write6(rdat, ndeslines)

            else ! level 0
c            write (0,*) 'inside= ',inside,' coord= ',coord
c call voxgridraytrace3

                  ihit = voxgrid_raytrace3(
     &              ntri,tri,
     &              coord,dir,dintmin,
     &              voxsize,gridmin,gridmax,
     &              ngrid,grid,lltri,llpoint,nll,trilist,ntrilist)
              ihit=ihit+1 ! correct ihit for fortran
              ihittri=ihit
c             write (0,*) 'ihit= ',ihit,' dintmin= ', dintmin
c             write (0,*) 'lon,lat,alt ',dlon(ihit),dlat(ihit),alt(ihit)
c             write (0,*) 'tric ',(tric(k,ihit),k=1,3)
c             write (0,*) 'v again ',v
c             write (0,*) 'dir again ',dir

             if (ihit.eq.0) then ! level 1
c              write (0,*) 'ihitri=0 '

          rdat(ndeslines-9)=-999.
          rdat(ndeslines-8)=-999.
          rdat(ndeslines-7)=-999.
          rdat(ndeslines-6)=-999.
          rdat(ndeslines-5)=-999.
          rdat(ndeslines-4)=-999.
          rdat(ndeslines-3)=-999.
          rdat(ndeslines-2)=-999.
          rdat(ndeslines-1)=-999.
          rdat(ndeslines)=-999.

          ios =  write6(rdat, ndeslines)
            else ! level 1

c               write (0,*) 'ihit= ',ihit

             do i=1,3
                t(i)=coord(i)+dintmin*dir(i)
             enddo
             trange=dintmin
             tradius=sqrt(t(1)**2+t(2)**2+t(3)**2)
             talt=tradius-rplanet

c calculate tlat and tlon
c             write (0,*) 't= ',t,tradius,talt
             tlat=180*asin(t(3)/tradius)/pi
c             write (0,*) 'tlat=' , tlat
             trxy=sqrt(t(1)**2+t(2)**2)
             if (t(1).eq.0.and.t(2).eq.0) then
                tlon=0.
             else if (t(2).gt.0) then
                tlon=180*acos(t(1)/trxy)/pi
             else if (t(2).lt.0) then
                tlon=-180*acos(t(1)/trxy)/pi
             endif
c             write (0,*) dir,ihit,dintmin,p,t
c calculate target slope - the angle between the triange normal and vertical
c calculate a normalized vector from the center of the planet to the center of the triangle
c call tricna to get data for hit triangle
            call ctricna  (tri(1,1,ihit),tric,trin,tria)


             trioutmag=
     & sqrt(tric(1)**2+tric(2)**2+tric(3)**2)
             triout(1)=tric(1)/trioutmag
             triout(2)=tric(2)/trioutmag
             triout(3)=tric(3)/trioutmag

c             write (0,*) trioutmag,triout

             dotp=
     & trin(1)*triout(1)+trin(2)*triout(2)+
     & trin(3)*triout(3) 
             if (dotp.lt.0) then
               tslope=90.
             else
             tslope=(180./pi)*acos (dotp)
             endif


c calculate emis, betwen the triangle normal and the look vector, which is -dir
             dotp=
     & -trin(1)*dir(1)-trin(2)*dir(2)-trin(3)*dir(3) 
             if (dotp.gt.1) then
                dotp=1.0
             endif
             if (dotp.le.0.) then
                temis=90.
             else
                 temis=(180./pi)*acos(dotp)
             endif


c next determine if the sun ray hits the triangle at the ray intersection
c do this by drawing a ray from the intersection to the sun

c calculate incidence, betwee the triangle normal and the sun vector
c calculate solar vactor
             sv(3)=sin(sunlat*pi/180.)
             sv(1)=cos(sunlat*pi/180.)*cos(sunlon*pi/180.)
             sv(2)=cos(sunlat*pi/180.)*sin(sunlon*pi/180.)
c calculate dot product between triangle normal and solar vector 
             dotp=
     & trin(1)*sv(1)+trin(2)*sv(2)+trin(3)*sv(3) 
             if (dotp.gt.1) then
                dotp=1.0
             endif
             if (dotp.le.0) then
                tinc=90.
             else
             tinc= (180./pi)*acos(dotp)
             endif
c             write (0,*) 'tinc= ',tinc
c calculate phase,, between the solar vector and -dir
             tphase=(180./pi)*acos(
     & -sv(1)*dir(1)-sv(2)*dir(2)-sv(3)*dir(3) )
c calculate azimuth angle
             dotp=
     & ((cos(tphase*pi/180.)-cos(tinc*pi/180.)*cos(temis*pi/180.))/
     & (sin(tinc*pi/180.)*sin(temis*pi/180.)))
             if (dotp.gt.1)  then
                dotp=1.0
             else if (dotp.lt.-1) then
                dotp=-1.0
             endif
             taz=(180./pi)*acos(dotp)
c
             if (tinc.ge.90) then ! level 2
                tinsol=0.
             else ! level 2
c raytrace to sun 
                  ihit = voxgrid_raytrace2(ihittri-1,
     &              ntri,tri,
     &              t,sv,dintmin,
     &              voxsize,gridmin,gridmax,
     &              ngrid,grid,lltri,llpoint,nll,trilist,ntrilist)
              ihit=ihit+1 ! correct ihit for fortran
c              write (0,*) 'ihitsun= ',ihit,ihittri             
c if ihit=0, then they ray is clear
              if (ihit.gt.0) then ! level 3
                 tinsol=0.
              else   
                tinsol=
     & ((s00*cos(pi*tinc/180.)/(sundst**2)))! *(1-0.2)/5.667e-8)**0.25
c                write (0,*) 'tinsol= ',tinsol
              endif ! level 3
c            write (0,*) 'tlon= ',tlon
c             write (0,*) 'talt= ',talt
             
             endif  ! level 2

c here is where the work is done...

c add one last check for temis>90             

          if (temis.ge.90.) then
          rdat(ndeslines-9)=-999.
          rdat(ndeslines-8)=-999.
          rdat(ndeslines-7)=-999.
          rdat(ndeslines-6)=-999.
          rdat(ndeslines-5)=-999.
          rdat(ndeslines-4)=-999.
          rdat(ndeslines-3)=-999.
          rdat(ndeslines-2)=-999.
          rdat(ndeslines-1)=-999.
          rdat(ndeslines)=-999.
          else
          rdat(ndeslines-9)=tlon
          rdat(ndeslines-8)=tlat
          rdat(ndeslines-7)=talt
          rdat(ndeslines-6)=tslope
          rdat(ndeslines-5)=temis
          rdat(ndeslines-4)=tinc
          rdat(ndeslines-3)=tphase
          rdat(ndeslines-2)=taz
          rdat(ndeslines-1)=tinsol
          rdat(ndeslines)=ihittri
          endif

          ios =  write6(rdat, ndeslines)
          endif ! level 1
          endif ! level 0

          ios = read5(rdat, ndeslines-10) ! very important that -10 
          if( ios .eq. -1 ) goto 999

        goto 10

 999         continue
       
        write(0,*) 'p3dgeom: Done reading records'

        endfile ( unit=6)
        ios=close5()

        stop
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


