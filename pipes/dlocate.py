import numpy as np

def main(xx, n, x):
    jl = -1
    ju = n
    while (ju-jl) > 1:
        print(ju,jl)
        jm = (ju+jl)/2
        if (xx[-1] >= xx[0]) and (x >= xx[jm]):
            jl = jm
        else:
            ju = jm
    if x == xx[0]:
        j=1
    elif x == xx[n-1]:
        j=n-1
    else:
        j=jl
    return j

if __name__ == '__main__':
    n=100
    xx = np.arange(n)
    x = -0.5
    j = main(xx,n,x)
    print("Answer:",j)