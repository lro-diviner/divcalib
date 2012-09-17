      subroutine gridsetup(voxsize,ntri,tri, gridmin,gridmax,ngrid)
      implicit none
      real*4 voxsize(3)
      integer*4 ntri
      real*4 tri(3,3,ntri)
      real*4 gridmin(3)
      real*4 gridmax(3)
      real*4 delta
      integer*4 ngrid(3),i,j,k
      real*4 large,small
      data large/1.e30/,small/-1.e30/
c      data delta/1.e-2/ 
      data delta/0.0/
c voxsize is the input size of the voxels (in meters)
c ntri is the number of input triangles
c tri is the triangle array
c gridmin is the minimum x,y,z coordinates of the grid of voxels
c grid max is the......
c ngrid is the number of x,y and z voxels in the grid
c
c first executable statement
c initialize gridmin and gridmax
c      write (0,*) 'in voxsetup'
      do i=1,3
         gridmin(i)=large
         gridmax(i)=small
      enddo
      do i=1,3
         do j=1,3
            do k=1,ntri
               if (tri(i,j,k).gt.gridmax(i)) gridmax(i)=tri(i,j,k)+delta
               if (tri(i,j,k).lt.gridmin(i)) gridmin(i)=tri(i,j,k)-delta
            enddo
         enddo
      enddo
c calculate ngrid
      do i=1,3
         ngrid(i)=(gridmax(i)-gridmin(i))/voxsize(i) + 1
c now ensure that the grid is exactly ngrid*voxsize in total dimensions
         gridmax(i)=gridmin(i)+ngrid(i)*voxsize(i)
      enddo
c      write (0,*) 'done with voxsetup'
      return
      end
