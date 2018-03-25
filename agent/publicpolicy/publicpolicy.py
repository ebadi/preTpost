import os
import sys
import shutil
import configparser
absLibDir = os.path.abspath(os.path.join(os.getcwd(), os.pardir, 'libdp/'))
sys.path.append(absLibDir)
try:
    import config
    import libdp
except:
    raise


def policy(reqId):
    """Public policy."""
    budget = libdp.getBudget('publicpolicy/' + config.budgetStorage)
    accCost = libdp.getTotalCost(config.totalCostStorage)
    cost = libdp.measureRisk(reqId)
    reqParams = configparser.SafeConfigParser()
    reqParams.read(libdp.wd(reqId, "public") + config.reqInfo)

    preAccessbileFile = set(['configData', 'trafficData', 'passwordData'])
    preresources = libdp.parseToDic(reqParams.get('config', 'preResources'))
    preFiles = set(preresources['mount'].split("|"))

    postAccessbileFile = set(['environementData'])
    postresources = libdp.parseToDic(reqParams.get('config', 'postResources'))
    postFiles = set(postresources['mount'].split("|"))

    print(">>", preresources)
    if int(preresources['timeout']) > 3:
        return False
    if int(postresources['cpu']) > 2:
        return False


    libdp.log("Public Policy", costTotalBudget=(cost, accCost, budget))
    return (cost+accCost < budget) & (preFiles <= preAccessbileFile) & (postFiles <=  postAccessbileFile)
