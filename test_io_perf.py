import os
import numpy as np

def write_numpy_arrays():
    base = 'testfile'
    arr = np.arange(100000)
    for i in range(10):
        np.save(base+str(i),arr)
    for i in range(10):
        os.remove(base+str(i)+'.npy')

          