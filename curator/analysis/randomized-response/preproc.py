import sys
import configparser
sys.path.append('/libdp')
import libdp

inFile = sys.argv[1]
outFile = sys.argv[2]

print (inFile)
data = configparser.ConfigParser()
data.read(inFile + 'data.ini')
#with open(inFile + 'data.ini', 'r') as fin:
#    print (fin.read())

l = [
    data['secret']['cat0'],
    data['secret']['cat1']]
libdp.toXml(outFile, l)
