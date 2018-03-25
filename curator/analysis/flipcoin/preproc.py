import sys
import configparser
sys.path.append('/libdp')
import libdp

inFile = sys.argv[1]
outFile = sys.argv[2]

data = configparser.ConfigParser()
data.read(inFile)

l = [
    data['secret']['DoYouSmoke'],
    data['secret']['DoYouDrink']]
libdp.toXml(outFile, l)
