c******************************************************************************
c azimiuth=240 for nadir mapping, elevation=180 for standard nadir mapping
c the direction cosines betwen diviner xyz and lro xyz are 150,30,180 degrees

c  PROGRAM: p3crosstrackplanning
c
c  PURPOSE: This program used ray tracing to recalculate cross-track viewing geometry for targets
c  REQUIRED KEYWORDS: 
c
c       lon=char  -- The column containing target east longitude
c
c       lat=char  -- The column containing target latitude
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
c    talt - target altitude
c    tslope - target slope
c    temis - target emission angle
c    tinc - target incidence angle
c    tinsol - target insolation 
c    tphase - target phase angle
c    taz - target solar azimuth angle
c    ex  - x component of emission angle in sun centered coordinates
c    ey - y component of emission angle in sun centered coordinates
c    itri - triangle number of intersection

c*******************************************************************************


        program p3crosstrackplanning
        implicit none
        include 'pipe1.inc'
        character*80 desfile,junk
        character*48 lonparam,latparam,sclatparam,sclonparam,scradparam
        character*48 demfile
        character*48 sunlatparam,sunlonparam,sundstparam,jdateparam
        real*8 rdat2(MAXCOL),rdat3(MAXCOL),f
        integer*4 loncol,latcol,scloncol,sclatcol,scradcol
        integer*4 sunlatcol,sunloncol,sundstcol
        integer*4 ios,iunit,ndeslines,ifound
        integer*4 jdatecol
        real*8 tlon,tlat,talt,lon,lat,scrad,deltat
        real*8 temis,tinc,tphase,tinsol,tslope,taz
        real*8 ex,ey,swathwidthkm,swathwidth0,jdate,jdateold,jdateold2
        real*8 deltajdate,swathlengthkm,swathtimesec
        real*8 eqxingsec,sclat0

        real*8 lrox_x,lrox_y,lrox_z
        real*8 lroy_x,lroy_y,lroy_z
        real*8 lroz_x,lroz_y,lroz_z
c        real*8 divx_x,divx_y,divx_z
c        real*8 divy_x,divy_y,divy_z
c        real*8 divz_x,divz_y,divz_z
        real*8 rmat(3,3) ! rotation matrix

        real*8 divdir(3),divelev,divazi,divaziold,divelevold
        real*8 deltadivazi,deltadivaziold,sindivazi,sindivaziold


        integer*4 lrox_xcol,lrox_ycol,lrox_zcol
        integer*4 lroy_xcol,lroy_ycol,lroy_zcol
        integer*4 lroz_xcol,lroz_ycol,lroz_zcol
c        integer*4 divx_xcol,divx_ycol,divx_zcol
c        integer*4 divy_xcol,divy_ycol,divy_zcol
c        integer*4 divz_xcol,divz_ycol,divz_zcol

        character*48 lrox_xparam,lrox_yparam,lrox_zparam
        character*48 lroy_xparam,lroy_yparam,lroy_zparam
        character*48 lroz_xparam,lroz_yparam,lroz_zparam
        character*48 divx_xparam,divx_yparam,divx_zparam
        character*48 divy_xparam,divy_yparam,divy_zparam
        character*48 divz_xparam,divz_yparam,divz_zparam
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
      real*4 dsslon,dsslat,rsunau,oneau,s00,cloctime
      character*80 filename
      real*4 sv(3)
c viewer parameters
      real*4 dvlon,dvlat,rv,v(3)
      real*4 p(3),dirmag,trioutmag,triout(3)
      real*4 ev(3),xp(3)
c photometric parameters
      real*4 hs0,dir(3),ddni,r,fluxsun,cosi,dintmin
      real*4 divsun
c pf phase function parameters
      real*4 rpf,pf02,b,c,h,x1,x2,b0,pi,mu0,mu,cosg,tango2
      real*4 rtri,tv(3),g
      real*4 rev
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
      integer*4 ifirst,ifirsteq
c woo boundng box variables
      integer hitboundingbox,inside,ihit,ihitbox,ihittri,ihittri2
      real*4 coord(3)
c dpi
      real*8 dpi
c naif parameters
      character*128 kernfile
      logical succss
      real*8  divbore_vec(3),lrox(3),lroy(3),lroz(3)

c data statements
      data voxsize/8.,8.,8./ !km
      data oneau/1.4958e8/ !km
      data rplanet/1737.4/ !km
      data s00/1369.0/ ! W m-2
      data swathwidth0/0.071/ !mrad

c      data asurf/M*0.1/
      data b,c,h,x1,x2,b0/0.249,0.407,0.0345,0.064,0.3,1.17/



        kernfile = "/u/marks/boris2/divbore_kernels.txt"
        CALL FURNSH(KERNFILE)
c        write (0,*) 'kernel file loaded'
        pi=dacos(-1.d0)
        dpi=dacos(-1.d0)
c        write (0,*) 'in p3dcrosstrackplanning'

        call getcmdreal('deltat',1,'required',ifound, deltat)
        call getcmdreal('lon',1,'required',ifound, tlon)
        call getcmdreal('lat',1,'required',ifound, tlat)
        call getcmdchar('sclat',1,'required',ifound, sclatparam)
        call getcmdchar('sclon',1,'required',ifound, sclonparam)
        call getcmdchar('scrad',1,'required',ifound, scradparam)
        call getcmdchar('sunlat',1,'required',ifound, sunlatparam)
        call getcmdchar('sunlon',1,'required',ifound, sunlonparam)
        call getcmdchar('sundst',1,'required',ifound, sundstparam)
        call getcmdchar('jdate',1,'required',ifound, jdateparam)
        call getcmdchar('dem',1,'required',ifound, demfile)

        call getcmdchar('lrox_x',1,'required',ifound, lrox_xparam)
        call getcmdchar('lrox_y',1,'required',ifound, lrox_yparam)
        call getcmdchar('lrox_z',1,'required',ifound, lrox_zparam)
        call getcmdchar('lroy_x',1,'required',ifound, lroy_xparam)
        call getcmdchar('lroy_y',1,'required',ifound, lroy_yparam)
        call getcmdchar('lroy_z',1,'required',ifound, lroy_zparam)
        call getcmdchar('lroz_x',1,'required',ifound, lroz_xparam)
        call getcmdchar('lroz_y',1,'required',ifound, lroz_yparam)
        call getcmdchar('lroz_z',1,'required',ifound, lroz_zparam)



c        call getcmdchar('divx_x',1,'required',ifound, divx_xparam)
c        call getcmdchar('divx_y',1,'required',ifound, divx_yparam)
c        call getcmdchar('divx_z',1,'required',ifound, divx_zparam)

c        call getcmdchar('divy_x',1,'required',ifound, divy_xparam)
c        call getcmdchar('divy_y',1,'required',ifound, divy_yparam)
c        call getcmdchar('divy_z',1,'required',ifound, divy_zparam)

c        call getcmdchar('divz_x',1,'required',ifound, divz_xparam)
c        call getcmdchar('divz_y',1,'required',ifound, divz_yparam)
c        call getcmdchar('divz_z',1,'required',ifound, divz_zparam)




c check for descriptor file in command line
        call getcmdchar('des',1,'optional',ifound, desfile)

c        write (0,*) 'got commands'

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

c        call findcol(lonparam,cdesstitle,ndeslines, loncol)
c        call findcol(latparam,cdesstitle,ndeslines, latcol)
        call findcol(jdateparam,cdesstitle,ndeslines, jdatecol)


        call findcol(sclatparam,cdesstitle,ndeslines, sclatcol)
        call findcol(sclonparam,cdesstitle,ndeslines, scloncol)
        call findcol(scradparam,cdesstitle,ndeslines, scradcol)
        call findcol(sunlatparam,cdesstitle,ndeslines, sunlatcol)
        call findcol(sunlonparam,cdesstitle,ndeslines, sunloncol)
        call findcol(sundstparam,cdesstitle,ndeslines, sundstcol)

        call findcol(lrox_xparam,cdesstitle,ndeslines, lrox_xcol)
        call findcol(lrox_yparam,cdesstitle,ndeslines, lrox_ycol)
        call findcol(lrox_zparam,cdesstitle,ndeslines, lrox_zcol)

        call findcol(lroy_xparam,cdesstitle,ndeslines, lroy_xcol)
        call findcol(lroy_yparam,cdesstitle,ndeslines, lroy_ycol)
        call findcol(lroz_zparam,cdesstitle,ndeslines, lroz_zcol)

        call findcol(lroz_xparam,cdesstitle,ndeslines, lroz_xcol)
        call findcol(lroz_yparam,cdesstitle,ndeslines, lroz_ycol)
        call findcol(lroz_zparam,cdesstitle,ndeslines, lroz_zcol)

c        call findcol(divx_xparam,cdesstitle,ndeslines, divx_xcol)
c        call findcol(divx_yparam,cdesstitle,ndeslines, divx_ycol)
c        call findcol(divx_zparam,cdesstitle,ndeslines, divx_zcol)

c        call findcol(divy_xparam,cdesstitle,ndeslines, divy_xcol)
c        call findcol(divy_yparam,cdesstitle,ndeslines, divy_ycol)
c        call findcol(divy_zparam,cdesstitle,ndeslines, divy_zcol)

c        call findcol(divz_xparam,cdesstitle,ndeslines, divz_xcol)
c        call findcol(divz_yparam,cdesstitle,ndeslines, divz_ycol)
c        call findcol(divz_zparam,cdesstitle,ndeslines, divz_zcol)


c        write (0,*) 'found columns'

c        write (0,*) 'loncol,latcol ',loncol,latcol



       call adddesline(ndeslines+1,'divsun',
     &       'divsun', cdesheader,
     &       cdesstitle,cdesltitle,
     &       ndeslines)
       call adddesline(ndeslines+1,'eqxingsec',
     &       'eqxingsec', cdesheader,
     &       cdesstitle,cdesltitle,
     &       ndeslines)
       call adddesline(ndeslines+1,'cloctime',
     &       'cloctime', cdesheader,
     &       cdesstitle,cdesltitle,
     &       ndeslines)

       call adddesline(ndeslines+1,'divdir_x',
     &       'divdir_x', cdesheader,
     &       cdesstitle,cdesltitle,
     &       ndeslines)

       call adddesline(ndeslines+1,'divdir_y',
     &       'divdir_y', cdesheader,
     &       cdesstitle,cdesltitle,
     &       ndeslines)

       call adddesline(ndeslines+1,'divdir_z',
     &       'divdir_', cdesheader,
     &       cdesstitle,cdesltitle,
     &       ndeslines)

       call adddesline(ndeslines+1,'divelev',
     &       'divelev', cdesheader,
     &       cdesstitle,cdesltitle,
     &       ndeslines)

       call adddesline(ndeslines+1,'divazi',
     &       'divazi', cdesheader,
     &       cdesstitle,cdesltitle,
     &       ndeslines)

       call adddesline(ndeslines+1,'tlon',
     &       'talt', cdesheader,
     &       cdesstitle,cdesltitle,
     &       ndeslines)

       call adddesline(ndeslines+1,'tlat',
     &       'talt', cdesheader,
     &       cdesstitle,cdesltitle,
     &       ndeslines)

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

       call adddesline(ndeslines+1,'tazi',
     &       'tazi', cdesheader,
     &       cdesstitle,cdesltitle,
     &       ndeslines)

       call adddesline(ndeslines+1,'ex',
     &       'ex', cdesheader,
     &       cdesstitle,cdesltitle,
     &       ndeslines)
c
       call adddesline(ndeslines+1,'ey',
     &       'ey', cdesheader,
     &       cdesstitle,cdesltitle,
     &       ndeslines)

       call adddesline(ndeslines+1,'swathlngthkm',
     &       'swathlngthkm', cdesheader,
     &       cdesstitle,cdesltitle,
     &       ndeslines)

       call adddesline(ndeslines+1,'swathwidthkm',
     &       'swathwidthkm', cdesheader,
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
c**************************************************************
c insert pre main loop code
      pi=acos(-1.)

      deltajdate=deltat/(24.*3600.) ! in days
c      write (0,*) 'deltajdate= ',deltajdate

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
c before we calculate target gemetry, we first must determine the altitude of the target
c this can be accomplished by projecting a radial ray from above the dem.
          clat=tlat
          clon=tlon
c calculate v and dir, the location and look direction of the hypothetical nadir looking spacecraft at an altitude of 50 km above the target
          v(3)=(rplanet+50)*sin(clat*pi/180.d0)
          v(1)=(rplanet+50)*cos(clat*pi/180.d0)*cos(clon*pi/180.d0)
          v(2)=(rplanet+50)*cos(clat*pi/180.d0)*sin(clon*pi/180.d0)
          dir(1)=-v(1)/(rplanet+50)
          dir(2)=-v(2)/(rplanet+50)
          dir(3)=-v(3)/(rplanet+50)
c          write (0,*) gridmin,gridmax
c          write (0,*) tlat,tlon,dir
c raytrace to surface target from an absolute altitude of 50 km
c          write (0,*) 'calling hitbounding box ',clon,clat,v,dir 
            ihitbox=hitboundingbox(gridmin,gridmax,v,dir, inside,coord)
            if (ihitbox.eq.0) stop 
     &       'p3dcrosstrackplanning  missed bounding box'
                  ihit = voxgrid_raytrace3(
     &              ntri,tri,
     &              coord,dir,dintmin,
     &              voxsize,gridmin,gridmax,
     &              ngrid,grid,lltri,llpoint,nll,trilist,ntrilist)
              ihit=ihit+1 ! correct ihit for fortran
              ihittri=ihit
              if (ihit.eq.0) stop 
     &        'p3dcrosstrackplanning missed triangles'
c              write (0,*) 'hit triangle ',ihittri
             do i=1,3
                t(i)=coord(i)+dintmin*dir(i)
                p(i)=t(i)
             enddo

             tradius=sqrt(t(1)**2+t(2)**2+t(3)**2)
             talt=tradius-rplanet
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
c             write (0,*) tlon,tlat,tradius,talt
c             write (0,*) 't= ',t,tradius,talt,tlat,tlon



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



C current direction cosines 150.13  29.88 179.12
c desired direction cosines: 150 30 180
c rotation matrix
c
c     -0.866025404    -.5      0
c     -.5        0.866025404   0
c      0             0        -1
             rmat(1,1)=-cos(30.d0*pi/180.d0)
             rmat(1,2)=-0.5d0
             rmat(1,3)=0.d0
             
             rmat(2,1)=-0.5d0
             rmat(2,2)=cos(30.d0*pi/180.d0)
             rmat(2,3)=0.d0

             rmat(3,1)=0.d0
             rmat(3,2)=0.d0
             rmat(3,3)=-1.d0






c             write (0,*) 'starting main loop'


c******************************************************************************\

c at this point, the calculation has been set up. the next step is to read in t\
c input data and to get to work processing.


             eqxingsec=-999.0
             ifirst=1
             ifirsteq=1
             sclat0=-999999.0
c             deltadivaziold=0.
             sindivaziold=0.
10           ios = read5(rdat, ndeslines-22) ! very important that -20 
          if( ios .eq. -1 ) goto 999

          jdate=rdat(jdatecol)
          if (ifirst.eq.1) jdateold2=jdate
c          clat=rdat(latcol)
c          clon=rdat(loncol)
          sclat=rdat(sclatcol)
          sclon=rdat(scloncol)
          rv=rdat(scradcol)

c check for equator crossing
c first check for first
          if (sclat0.lt.-10000) then ! check for first time
             sclat0=sclat
          else ! not first time
c check for equator crossing
             if (sclat0.gt.0.and.sclat.le.0) then
c interpolate first point after equator crossing
                eqxingsec=-deltat*sclat/(sclat-sclat0)
c                write (0,*) 'eqxingsec ',sclat,sclat0,deltat
                sclat0=sclat
                ifirsteq=0
             else ! not equator crossing case
                if (ifirsteq.eq.0) then ! if we've already crossed the equator
                   eqxingsec=eqxingsec+deltat
                   sclat0=sclat
                else ! if we haven't, then don't alter equxingsec
                   sclat0=sclat
                endif
             endif
          endif   
c          if (eqxingsec.gt.3300.0) write (0,*) 
c     &              eqxingsec,sclat,sclat0,deltat,ifirsteq

c          write (0,*) sclat,sclon,rv

            v(3)=rv*sin(sclat*pi/180.)
            v(1)=rv*cos(sclat*pi/180.)*cos(sclon*pi/180.)
            v(2)=rv*cos(sclat*pi/180.)*sin(sclon*pi/180.)
c            write (0,*) 'v= ',v
c view direction
c            p(3)=rplanet*sin(clat*pi/180.)
c            p(1)=rplanet*cos(clat*pi/180.)*cos(clon*pi/180.)
c            p(2)=rplanet*cos(clat*pi/180.)*sin(clon*pi/180.)
c            write (0,*) 'p= ',p
            dir(1)=p(1)-v(1)
            dir(2)=p(2)-v(2)
            dir(3)=p(3)-v(3)
            dirmag=sqrt(dir(1)**2+dir(2)**2+dir(3)**2)
            dir(1)=dir(1)/dirmag
            dir(2)=dir(2)/dirmag
            dir(3)=dir(3)/dirmag
            ev(1)=-dir(1)
            ev(2)=-dir(2)
            ev(3)=-dir(3)
            

c first check for back side 

            dotp=-trin(1)*dir(1)-trin(2)*dir(2)-trin(3)*dir(3)
            if (dotp.lt.0) goto 10

c  use woo boundingbox to find where ray intersects grid
            ihitbox=hitboundingbox(gridmin,gridmax,v,dir, inside,coord)
            if (ihitbox.eq.0) goto 10
c               write (0,*) 'ihitbox=0 '
c            write (0,*) 'inside= ',inside,' coord= ',coord
c call voxgridraytrace3

                  ihit = voxgrid_raytrace3(
     &              ntri,tri,
     &              coord,dir,dintmin,
     &              voxsize,gridmin,gridmax,
     &              ngrid,grid,lltri,llpoint,nll,trilist,ntrilist)
              ihit=ihit+1 ! correct ihit for fortran
c if we hit the wrong griangle, then go to 10
              if (ihit.ne.ihittri) goto 10
c set target range from spacecraft in km

c              write (0,*) 'hit ',ihit,coord,dir,dintmin


c calculate local time
          sunlat=rdat(sunlatcol)
          sunlon=rdat(sunloncol)
          sundst=rdat(sundstcol)


              trange=dirmag

c             write (0,*) 'ihit= ',ihit,' dintmin= ', dintmin
c             write (0,*) 'lon,lat,alt ',dlon(ihit),dlat(ihit),alt(ihit)
c             write (0,*) 'tric ',(tric(k,ihit),k=1,3)
c             write (0,*) 'v again ',v
c             write (0,*) 'dir again ',dir



c               write (0,*) 'ihit= ',ihit

             do i=1,3
                t(i)=coord(i)+dintmin*dir(i)
             enddo
c             tradius=sqrt(t(1)**2+t(2)**2+t(3)**2)
c             talt=tradius-rplanet

c calculate tlat and tlon
c             write (0,*) 't= ',t,tradius,talt
c             tlat=180*asin(t(3)/tradius)/pi
c             write (0,*) 'tlat=' , tlat
c             trxy=sqrt(t(1)**2+t(2)**2)
c             if (t(1).eq.0.and.t(2).eq.0) then
c                tlon=0.
c             else if (t(2).gt.0) then
c                tlon=180*acos(t(1)/trxy)/pi
c             else if (t(2).lt.0) then
c                tlon=-180*acos(t(1)/trxy)/pi
c             endif
c             write (0,*) dir,ihit,dintmin,p,t
c calculate target slope - the angle between the triange normal and vertical
c calculate a normalized vector from the center of the planet to the center of the triangle
c call tricna to get data for hit triangle
c            call ctricna  (tri(1,1,ihit),tric,trin,tria)
cc
c
c             trioutmag=
c     & sqrt(tric(1)**2+tric(2)**2+tric(3)**2)
c             triout(1)=tric(1)/trioutmag
c             triout(2)=tric(2)/trioutmag
c             triout(3)=tric(3)/trioutmag

c             write (0,*) trioutmag,triout

c             dotp=
c     & trin(1)*triout(1)+trin(2)*triout(2)+
c     & trin(3)*triout(3) 
c             if (dotp.lt.0) then
c               tslope=90.
c             else
c             tslope=(180./pi)*acos (dotp)
c             endif


c calculate emis, betwen the triangle normal and the look vector, which is -dir
             dotp=
     & -trin(1)*dir(1)-trin(2)*dir(2)-trin(3)*dir(3) 
             if (dotp.gt.1) then
                dotp=1.0
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
c calculate divsun, the angle between the look direction and the sun
             divsun=180.*acos(dir(1)*sv(1)+dir(2)*sv(2)+dir(3)*sv(3))/pi
c calculate dot product between triangle normal and solar vector 
             dotp=
     & trin(1)*sv(1)+trin(2)*sv(2)+trin(3)*sv(3) 
             if (dotp.gt.1) then
                dotp=1.0
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
c check for positive or negative taz by taking cross product of
c solar vector and look vector and taking the dot product with the normal vector
             xp(1)=sv(2)*ev(3)-sv(3)*ev(2)
             xp(2)=sv(3)*ev(1)-sv(1)*ev(3)
             xp(3)=sv(1)*ev(2)-sv(2)*ev(1)
             dotp=xp(1)*trin(1)+xp(2)*trin(2)+xp(3)*trin(3)
             if (dotp.lt.0) taz=-taz
c
             if (tinc.ge.90) then ! level 2
                tinsol=0.
                ex=-999.0
                ey=-999.0
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
                 ex=-999.
                 ey=-999.
              else   
                tinsol=
     & ((s00*cos(pi*tinc/180.)/(sundst**2)))! *(1-0.2)/5.667e-8)**0.25
                ex=temis*cos(pi*taz/180.)
                ey=temis*sin(pi*taz/180.)
c                write (0,*) 'tinsol= ',tinsol
              endif ! level 3
c            write (0,*) 'tlon= ',tlon
c             write (0,*) 'talt= ',talt
             
             endif  ! level 2
c calculate local time
             cloctime=12.0-(sunlon-tlon)*24./360.
             if (cloctime.lt.0) cloctime=24+cloctime
             if (cloctime.gt.24) cloctime=cloctime-24
c calculate div swath km
             swathwidthkm=trange*swathwidth0/cos(temis*pi/180.)
             swathlengthkm=trange*swathwidth0

c             write (0,*) 'divswathkm ',trange,divswath0,temis
c             write (0,*) 'calling vecmatmult'

c            write (0,*)
c            write (0,*) rdat(divx_xcol),rdat(divx_ycol),rdat(divx_zcol)
c            write (0,*) rdat(divy_xcol),rdat(divy_ycol),rdat(divy_zcol)
c            write (0,*) rdat(divz_xcol),rdat(divz_ycol),rdat(divz_zcol)


c             call vecmatmult
c     & (rdat(divx_xcol),
c     &  rdat(divx_ycol),
c     &  rdat(divx_zcol),rmat,
c     &  divx_x,divx_y,divx_z)

c             call vecmatmult
c     & (rdat(divy_xcol),
c     &  rdat(divy_ycol),
c     &  rdat(divy_zcol),rmat,
c     &  divy_x,divy_y,divy_z)

c             call vecmatmult
c     & (rdat(divz_xcol),
c     &  rdat(divz_ycol),
c     &  rdat(divz_zcol),rmat,
c     &  divz_x,divz_y,divz_z)

c             write (0,*)
c             write (0,*) rdat(divx_xcol),rdat(divx_ycol),rdat(divx_zcol)
c             write (0,*) rdat(divy_xcol),rdat(divy_ycol),rdat(divy_zcol)
c             write (0,*) rdat(divz_xcol),rdat(divz_ycol),rdat(divz_zcol)
c             write (0,*)
c             write (0,*) rmat
c             write (0,*)
c             write (0,*) divx_x,divx_y,divx_z
c             write (0,*) divy_x,divy_y,divy_z
c             write (0,*) divz_x,divz_y,divz_z
c             write (0,*)

             





c assign parameters (This is old)
c all of these need to be multiplied by the rotation matrix above





             lrox(1)=rdat(lrox_xcol) 
             lrox(2)=rdat(lrox_ycol) 
             lrox(3)=rdat(lrox_zcol) 

             lroy(1)=rdat(lroy_xcol) 
             lroy(2)=rdat(lroy_ycol) 
             lroy(3)=rdat(lroy_zcol) 

             lroz(1)=rdat(lroz_xcol) 
             lroz(2)=rdat(lroz_ycol) 
             lroz(3)=rdat(lroz_zcol) 



c calculate direction of look vector in Diviner coordinates
             divbore_vec(1)=dir(1)
             divbore_vec(2)=dir(2)
             divbore_vec(3)=dir(3)



             call dlre_xzv2azel(lrox,lroz,divbore_vec, 
     &                       divazi,divelev,succss)

             if (succss.eq..false.) 
     &                write (0,*)  'false success',
     & lrox,lroz,divbore_vec,divazi,divelev
             if (succss.eq..false.)   goto 10

c             divdir(1)=dir(1)*divx_x+dir(2)*divx_y+dir(3)*divx_z
c             divdir(2)=dir(1)*divy_x+dir(2)*divy_y+dir(3)*divy_z
c             divdir(3)=dir(1)*divz_x+dir(2)*divz_y+dir(3)*divz_z



c             write (0,*) sclon,sclat,tlon,tlat,divdir

c calculate angles between divdir and "nadir"
c             divelev=(acos(divdir(3)))*180./pi
c calculate diviner azimuth angle (note that 240 degrees is perpendicular to the LRO ground track
c this boils down to finding the rotation direction in the diviner x-y plane necessary to hit the target
c Find the angle of dir in the diviner x-y plane
c             write (0,*) 'divazi ',divdir,
c     & 180*acos(divdir(1)/sqrt(divdir(1)**2+divdir(2)**2))/pi
c              if (divdir(2).ge.0) then
c         divazi=-180*acos(divdir(1)/sqrt(divdir(1)**2+divdir(2)**2))/pi
c            else 
c         divazi=+180*acos(divdir(1)/sqrt(divdir(1)**2+divdir(2)**2))/pi
c             endif
c             if (divazi.lt.0) divazi=360+divazi
c check for reverse mapping configuration
             if (divazi.lt.180) then
                divazi=divazi+180
                divelev=180+(180-divelev)
             endif
c check for divazi=240 crossover
c             write (0,*) sclon,sclat,divelev,divazi

c                tlon=-180*acos(t(1)/trxy)/pi
c             endif

c load results into rdat
             rdat(ndeslines)=ihittri
             rdat(ndeslines-1)=tinsol
             rdat(ndeslines-2)=swathwidthkm
             rdat(ndeslines-3)=swathlengthkm
             rdat(ndeslines-4)=ey
             rdat(ndeslines-5)=ex
             rdat(ndeslines-6)=taz
             rdat(ndeslines-7)=tphase
             rdat(ndeslines-8)=tinc
             rdat(ndeslines-9)=temis
             rdat(ndeslines-10)=tslope
             rdat(ndeslines-11)=talt
             rdat(ndeslines-12)=tlat
             rdat(ndeslines-13)=tlon
             rdat(ndeslines-14)=divazi
             rdat(ndeslines-15)=divelev
             rdat(ndeslines-16)=divdir(3)
             rdat(ndeslines-17)=divdir(2)
             rdat(ndeslines-18)=divdir(1)
             rdat(ndeslines-19)=cloctime
             rdat(ndeslines-20)=eqxingsec
             rdat(ndeslines-21)=divsun

c             deltadivazi=divazi-divaziold
c check for divazi=240 crossover
c             write (0,*) 'ifirst ',jdate,divazi,divaziold
             if (ifirst.ne.1.and.jdate-jdateold2.lt.1.2*deltajdate) then ! check for continuous time

                sindivazi=(divelev-180.)*sin(pi*(divazi-240.)/180.)
                if ((sindivazi.lt.0.and.sindivaziold.gt.0).or.
     &                     (sindivazi.gt.0.and.sindivaziold.lt.0)) then
                   if (abs(sindivazi).lt.55.) then ! extra test for large variation in sindivazi
c                   write (0,*) ifirst,jdate,jdateold,jdate-jdateold,
c     & deltajdate,sindivazi,sindivaziold
c               if (abs(divelev-divelevold).lt.10.) then ! arbitrary check for az=180,360 crossings
c chedk for change in first derivative of divazi
c               write (0,*) divazi,divaziold,deltadivazi,deltadivaziold,
c     &                       sign(1.d0,deltadivazi)
c                if (sign(1.d0,deltadivaziold).eq.sign(1.d0,deltadivazi)) 
c     &                                                            then

c                  if (divazi.lt.240.and.divaziold.gt.240.or.
c     &              divazi.gt.240.and.divaziold.lt.240) then
c                   f=(240-divaziold)/(divazi-divaziold)
                   f=(-sindivaziold)/(sindivazi-sindivaziold)
c                   write (0,*) 'f= ',f,divaziold,divazi
c linearly interpolate all columns (bad for ciclic variables, but ok for now)
                  do i=1,ndeslines
                    rdat3(i)=rdat2(i)+f*(rdat(i)-rdat2(i))
                  enddo
                  rdat3(ndeslines-14)=240.d0 ! very important that -14
c                  write (0,*) 'outputting ',rdat3(1),rdat3(jdatecol)
c                  ios =  write6(rdat2, ndeslines)
                  ios =  write6(rdat3, ndeslines) ! just write out interpolated value
c                  ios =  write6(rdat, ndeslines)

c                 endif
c                endif
               endif
               endif
c                  jdateold2=jdate
              endif

c compute deltadivaziold
c              deltadivaziold=rdat(ndeslines-14)-rdat2(ndeslines-14)
c write data to spare buffer
          do i=1,ndeslines
             rdat2(i)=rdat(i)
          enddo
c assign divaziold
          divelevold=rdat2(ndeslines-15) ! very important that -13
          divaziold=rdat2(ndeslines-14) ! very important that -13
          sindivaziold=sindivazi
          jdateold=rdat2(jdatecol)
          jdateold2=jdate
          ifirst=0
        goto 10
 999         continue
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


      subroutine vecmatmult (a1,a2,a3,m, v1,v2,v3)
      real*8 a1,a2,a3,m(3,3),v1,v2,v3
c      write (0,*) 'in vecmtmult'
c      write (0,*) 'a= ',a1,a2,a3
c      write (0,*) 'm= ',m
      v1=a1*m(1,1)+a2*m(1,2)+a3*m(1,3)
      v2=a1*m(2,1)+a2*m(2,2)+a3*m(2,3)
      v3=a1*m(3,1)+a2*m(3,2)+a3*m(3,3)
c      write (0,*) 'v= ',v1,v2,v3
      return
      end
