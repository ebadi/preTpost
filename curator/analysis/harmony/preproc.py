import sys
import configparser
import random
import numpy as np
sys.path.append('/libdp')
import libdp

inFile = sys.argv[1]
outFile = sys.argv[2]

data = configparser.ConfigParser()
data.read(inFile)

# Harmony Algorithm 2 for handling numeric attributes
t = [
    float(data['secret']['value0']),
    float(data['secret']['value1']),
    float(data['secret']['value2'])]
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

# To reproduce results set see value accordingly
prng = np.random.RandomState(None)
# To reproduce results set see value accordingly
random.seed(None)

u = np.random.choice([1, -1], 1, p=[(t[Aj]+1.0)/2.0, (1.0 - t[Aj])/2.0])

libdp.toXml(outFile, u)
