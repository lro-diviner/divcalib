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
 10           if (ju-jl.gt.1) then
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


