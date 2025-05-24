import numpy as np    

# numpy array of zeros 5x5
zeros = np.zeros((5, 5), dtype=np.uint8)

# numpy array of ones 3x3
ones = np.ones((3, 3), dtype=np.uint8)

# a 5x5 numpy array with the ones in the middle and the rest zeros
middle = np.zeros((5, 5))
middle[2:, 2:] += ones 
print(middle)