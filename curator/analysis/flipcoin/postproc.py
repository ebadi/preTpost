import sys
import math
sys.path.append('/libdp')
import libdp

inFile = sys.argv[1]
outFile = sys.argv[2]

epsilon = float(sys.argv[3])  # the epsilon has to be given via cmd argument
scalingFactor = (math.exp(epsilon) + 1) / (math.exp(epsilon) - 1)
data = libdp.fromXml(inFile)

out = {}
for i in range(0, len(data)):
    out[i] = float(data[i]) * scalingFactor

libdp.toXml(outFile, out)
