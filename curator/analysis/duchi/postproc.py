import sys
import math
import functools
import operator as op
sys.path.append('/libdp')
import libdp


# https://stackoverflow.com/questions/4941753/is-there-a-math-ncr-function-in-python
def ncr(n, r):
    n = int(n)
    r = int(r)
    """Calculate the number of possible combinations."""
    r = min(r, n-r)
    if r == 0:
        return 1
    numer = functools.reduce(op.mul, range(n, n-r, -1))
    denom = functools.reduce(op.mul, range(1, r+1))
    return numer//denom


# Duchi Algorithm 1 for handling numeric attributes

inFile = sys.argv[1]
outFile = sys.argv[2]

data = libdp.fromXml(inFile)

d = 3
epsilon = 2.0
eEpsMinus1 = math.exp(epsilon)-1.0
if d % 2 == 0:
    Cd = 2**(d-1) - (ncr(d, d/2)/2)
    B = (2 ** d + Cd * eEpsMinus1) / (ncr(d-1, d/2) * eEpsMinus1)
else:
    Cd = 2**(d-1)
    B = (2 ** d + Cd * eEpsMinus1) / (ncr(d-1, (d-1)/2) * eEpsMinus1)

libdp.log("report", report=(data, B, Cd))

out = [None] * d
for i in range(0, len(data)):
    out[i] = float(data[i]) * B
libdp.toXml(outFile, out)
