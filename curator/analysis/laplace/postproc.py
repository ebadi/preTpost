import sys
sys.path.append('/libdp')
import libdp

inFile = sys.argv[1]
outFile = sys.argv[2]

data = libdp.fromXml(inFile)
libdp.toXml(outFile, data)
