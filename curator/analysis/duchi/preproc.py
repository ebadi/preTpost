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

# Duchi Algorithm 1 for handling numeric attributes
t = [
    float(data['secret']['value0']),
    float(data['secret']['value1']),
    float(data['secret']['value2'])]
d = 3

# To reproduce results set see value accordingly
prng = np.random.RandomState(None)
# To reproduce results set see value accordingly
random.seed(None)
for Aj in range(0, len(t)):
    v = np.random.choice([1, -1], d, p=[(t[Aj]+1.0)/2.0, (1.0 - t[Aj])/2.0])

libdp.toXml(outFile, v)
