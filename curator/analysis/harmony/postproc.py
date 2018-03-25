import sys
import random
import math
sys.path.append('/libdp')
import libdp

inFile = sys.argv[1]
outFile = sys.argv[2]

data = libdp.fromXml(inFile)

d = 3
epsilon = 2.0
# **IMPORTANT** chosen by curator in both preprocessing and postprocessing
Aj = 1
# **IMPORTANT**: Instead of using the same seed in
# preprocessing and postprocesing algorithm to have identical Aj
# the curator can simply choose the Aj

# IMPORTANT: This is unique for each agent and not accessable to the curator.
# agentAnalysisSeed = 123456789
# To reproduce results set see value accordingly
# random.seed(agentAnalysisSeed)
# Aj = random.randint(0,d)
assert Aj < d

out = [0.0] * d
out[Aj] = float(data[0]) * float(d) * (math.exp(epsilon)+1.0) / (math.exp(epsilon)-1.0)
libdp.toXml(outFile, out)
