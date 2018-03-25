import sys
import os
sys.path.append('/libdp')
try:
    import config
    import libdp
except:
    raise

preProcResult = sys.argv[1]  # '/input/'
clmapedRandomisedResult = sys.argv[2]  # '/output/'
dataDir = sys.argv[3]  # data directory for request (where matrices are stored)
numOutput = int(sys.argv[4])

OutLines = [None] * numOutput
InLines = [None] * numOutput


def clamp(item, domain):
    """
    Enforce that the item is in the valid domain.

    In this case the first item is picked
    but random selection from domain is possible.
    """
    if item not in domain:
        print (item + ":Clamped")
        return domain[0]

    else:
        return item


try:
    InLines = libdp.fromXml(preProcResult, numOutput)
except:
    libdp.log("Private Policy and Clamping",
              "Bad outputs, will be replaced by dummy values")

# Plece holder for the private policy

for i in range(0, numOutput):
    if os.path.isfile(dataDir + str(i) + '.analysesMatrix'):
        mat, fn = libdp.loadTransitionMatrix(
            dataDir + str(i) + '.analysesMatrix')
        # print (mat , fn , InLines)
        InLines[i] = clamp(InLines[i], fn)  # Maybe randomly pick one
        OutLines[i] = libdp.randmizer(InLines[i], mat)
    elif os.path.isfile(dataDir + str(i) + '.analysesLaplace'):
        fd = open(dataDir + str(i) + '.analysesLaplace', "r")
        epsilon = float(fd.readline())
        try:
            # Clamp into the range [+1,-1]
            InLines[i] = max(min(float(InLines[i]), 1.0), -1.0)
        except:  # if index was not defined
            InLines[i] = 0.0
        OutLines[i] = str(libdp.laplace(epsilon, InLines[i]))
    else:
        print("wtf")
libdp.toXml(clmapedRandomisedResult, OutLines)
