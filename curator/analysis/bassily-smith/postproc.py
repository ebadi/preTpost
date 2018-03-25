import sys
import random
import math
sys.path.append('/libdp')
import libdp


inFile = sys.argv[1]
outFile = sys.argv[2]

data = libdp.fromXml(inFile)

# The categorical attribute name
x = str(sys.argv[3])
# number of participants
n = float(sys.argv[4])
# size of category
d = int(sys.argv[5])
# confidence
beta = float(sys.argv[6])
# privacy parameter
epsilon = float(sys.argv[7])
# Shared seeds between preprocessing and postprocessing to generate s
SSharedRandomSeeds = int(sys.argv[8])
# This seed is used to generate identical
# Johnson-Lindenstrauss random projection matrix
# sharepd between the agents and the curator
PhiSharedRandomSeeds = int(sys.argv[9])

assert beta > 0
# To avoid negative log
assert beta < 2
assert epsilon > 0
assert d > 1

gamma = math.sqrt(math.log(2.0*d / beta) / epsilon**2.0 * n)
mx = math.log(float(d)+1) * math.log(2.0/beta) / (gamma**2)
# ceil, floor or round ?
m = int(math.ceil(mx))
# TODO: Better way to convert m to an integer!

# To reproduce results set see value accordingly
random.seed(SSharedRandomSeeds)
j = random.randint(0, m)

zj = float(
    data[0]) * math.sqrt(m) * ((math.exp(epsilon) + 1) / (math.exp(epsilon)-1))
o = '(' + str(j) + ',' + str(zj) + ')'

libdp.toXml(outFile, [o])
