import csv
import glob
import sys
import math
import random
import configparser
from xml.etree.ElementTree import Element, SubElement, tostring, parse, ElementTree
import tempfile
import os
import uuid


# To reproduce results set see value accordingly
random.seed(None)
uploadDir = "instance-" + str(uuid.uuid4())[:4] + "/"  # TODO : Fix, include the full string


def parseToDic(str):
    """ Parse a string into key:value dictionary like this:
    >>> str
    'timeout:12;cpu:12;dev/rand:/input1;sensitiveDir:input2'
    >>> dict(kv.split('=')  for kv in  str.split(';'))
    {'sensitiveDir': 'input2', 'cpu': '12', 'timeout': '12', 'dev/rand': '/input1'}
    """
    return (dict(kv.split(':') for kv in str.split(';')))


def laplace(epsilon, v = 0):
    '''Laplace noise scaled with the parameter epsilon.'''
    scale = 1 / epsilon
    r = random.uniform(0, 1)
    if (r >= 0.5 ):
        return (v - scale * math.log(2 * (1 - r)))
    else :
        return (v + scale * math.log(2 * r))


def wd(reqId='', type=''):
    """Return the working directory."""
    return os.getcwd()+'/'+uploadDir + str(reqId) + type + "/"


def log(topic, **kwargs):
    """Log errors and warnings."""
    #print("[" + topic + "] ", end="")
    for name, value in kwargs.items():
        print('{0} = {1}'.format(name, value))


def toXml(path, data):
    """
    Convert data and save it into file.

    toXml('tmp', [99,98,97])
    """
    top = Element('root')
    for i in range(0, len(data)):
        report = SubElement(top, 'result', id=str(i))
        report.text = str(data[i])
    tree = ElementTree(top)
    #  print(tostring(top))
    tree.write(path)


def fromXml(path, numOutput=-1):
    """
    Load data from a file.

    print(fromXml('tmp', 2))
    """
    OutLines = {}
    tree = parse(path)
    for tags in tree.iter('result'):
        i = int(tags.attrib['id'])
        if i < numOutput and i > -1:
            OutLines[int(tags.attrib['id'])] = tags.text
        if numOutput == -1:
            OutLines[int(tags.attrib['id'])] = tags.text
    return OutLines


def errorXml(path, msg):
    """
    Write an error message into an xml file.

    errorXml("tmp", "msg")
    """
    top = Element('root')
    report = SubElement(top, 'error', id='error')
    report.text = str(msg)
    tree = ElementTree(top)
    tree.write(path)


def buildStairCaseMatrix(epsilon, domain):
    """
    Build a trasition matrix given the epsilon value.

    [Extremal Mechanisms for Local Differential Privacy] Page 13
    e.g. buildStairCaseMatrix(2, ["T", "F", "U"])
    """
    file, path = tempfile.mkstemp()
    os.close(file)
    with open(path, 'w') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        writer.writerow(['attribute'] + domain)
        counter = 0
        for i in domain:
            row = [domain[counter]] + ['1'] * len(domain)
            row[counter+1] = math.exp(epsilon)
            writer.writerow(row)
            counter = counter + 1

    with open(path, 'r') as f:
        data = f.read()
        f.close()
    os.remove(path)
    return data


def loadTransitionMatrix(path):
    """Load a transition matrix from a file."""
    ATTRIBUTE = 'attribute'
    transitionMatrix = dict()
    reader = csv.DictReader(open(path))
    for inPut in reader:
        totalProbability = 0
        tmpDic = dict()
        for PossibleOutput, probabilityStr in inPut.items():
            if PossibleOutput == ATTRIBUTE:
                pass
            else:
                probability = float(probabilityStr)
                totalProbability = totalProbability + probability
                # print (PossibleOutput, probability)
                tmpDic[(inPut['attribute'], PossibleOutput)] = probability
        # normalize probabilities to have total probability of 1
        tmpDic = {k: v/totalProbability for k, v in tmpDic.items()}
        transitionMatrix.update(tmpDic)
    reader.fieldnames.remove(ATTRIBUTE)
    fieldnames = list(set(reader.fieldnames))
    return (transitionMatrix, fieldnames)


def measureEpsilon(transitionMatrix, fieldnames):
    """Measure the cost of the given transition matrix."""
    epsilon = sys.maxsize  # infinity
    for field in fieldnames:
        mx = max({k: v for k, v in
                  transitionMatrix.items() if k[1] == field}.values())
        mn = min({k: v for k, v in
                  transitionMatrix.items() if k[1] == field}.values())
        # since we are deadling a probability matrix, mx != 0
        try:
            epsilon = math.log(max(abs(mx/mn), abs(mn/mx)))
        except ZeroDivisionError:
            epsilon = sys.maxsize  # infinity
    return epsilon


def randmizer(input, transitionMatrix):
    """Apply the transition matrix to the input value."""
    choice = random.random()
    totalprob = 0
    for k, v in transitionMatrix.items():
        i, o = k
        if i == input:
            totalprob += float(v)
            if choice <= totalprob:
                return o


def measureRisk(reqId):
    dir = wd(str(reqId), "public")
    """Measure the total cost of analysis in the given directory(request)"""
    totalCost = 0
    log(dir)
    for matFile in glob.glob(dir + '/*.analysesMatrix'):
        mat, fn = loadTransitionMatrix(matFile)
        totalCost += measureEpsilon(mat, fn)

    for lapFile in glob.glob(dir + '/*.analysesLaplace'):
        fd = open(lapFile, "r")
        epsilon = float(fd.readline())
        fd.close()
        totalCost += epsilon
    return totalCost


def getTotalCost(path):
    """Get total cost."""
    conf = configparser.SafeConfigParser()
    conf.read(path)
    return float(conf.get('policy', 'totalcost'))


def getBudget(path):
    """Get budget."""
    conf = configparser.SafeConfigParser()
    conf.read(path)
    return float(conf.get('policy', 'budget'))


def updateTotalCost(path, epsilon):
    """Add epsilon to the total cost."""
    conf = configparser.SafeConfigParser()
    conf.read(path)
    totalcostValue = float(conf.get('policy', 'totalcost'))
    conf.set('policy', 'totalcost', str(totalcostValue + epsilon))
    with open(path, 'w') as configWrite:
            conf.write(configWrite)
    configWrite.close()
