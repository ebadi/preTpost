import sys
sys.path.append("dependencies")
from flask import Flask, render_template, request, send_from_directory, send_file
import os
import time
import configparser
import threading
import os.path
import subprocess
import traceback
#from flask_autoindex import AutoIndex
import shutil
import argparse
import uuid
import atexit

app = Flask(__name__)

def normalise(s):
     return s.replace("/home/pandora/repositories/phdthesis/vehicular-privacy/preTpost/", "[PTP]")

def insecureSandbox(reqId, program, inputFile, outputFile, extraParams, resources):
    """
    Unsecure Sandbox (no isolation and no time padding)
    """
    libdp.log("Sandbox Execution",
              msg=(reqId, normalise(program), normalise(inputFile), normalise(outputFile),
                   extraParams, resources))
    global absLibDir
    cmd = ['/usr/bin/python3',
           program,
           inputFile,
           outputFile,
           ]
    cmd.extend(extraParams)
    #print(" ".join(cmd))
    subprocess.call(cmd, env={"PYTHONPATH": "../libdp"},)

def secureSandbox(reqId, program, inputFile, outputFile, extraParams, resources):
    """
    Sandbox to avoid explicit flows (filesystem) and side channels (time).

    The process that has to be sandboxed is specified by
        1) The directory ('reqId')
        2) The program name ('program')
    Readonly 'input' and an empty 'output' files are mounted.
    Passing extra parameters to the program is possible via 'extraParams'.
    """

    libdp.log("Sandbox Execution",
              msg=(reqId, normalise(program), normalise(inputFile), normalise(outputFile),
                   extraParams, resources))
    global absLibDir
    for _ in range(0, int(resources['cpu'])):
        semCPU.acquire()

    def paddingMethod(timeout):
        time.sleep(timeout)

    def computation(timeout):
        # We don't mount input directories/files directly.
        # Instead we copy them into a temporarily directoly first.
        scriptDir = libdp.wd(reqId, "public")
        tmpInDir = libdp.wd(reqId, "tmpIn")
        tmpOutDir = libdp.wd(reqId, "tmpOut")
        # data directory is not accessable inside the sandbox
        dataDir = libdp.wd(reqId, "private")
        os.makedirs(tmpInDir)
        os.makedirs(tmpOutDir)
        try:
            shutil.copytree(dataDir + inputFile, tmpInDir + inputFile)
        except :
            pass
        try:
            shutil.copyfile(dataDir + inputFile, tmpInDir + inputFile)
        except :
            pass

        # TODO : mount instead of copying
        # for r in resources['mount'].split("|"):
        #     try:
        #         # TODO
        #         shutil.copyfile(r, tmpInDir + os.path.basename(r))
        #     except:
        #         pass
        cmd = ['/usr/bin/python3',
                   '/scripts/' + program,
                   '/input/' + inputFile,
                   '/output/' + outputFile
                   ]

        cmd.extend(extraParams)
        proc = subprocess.Popen(["nsjail/nsjail",
                                 "-Mo",
                                 "--verbose",
                                 "--quiet",
                                 "--env", "HOME=/",
                                 "--env", "LD_LIBRARY_PATH=/usr/lib/:/usr/lib/libblas/:/usr/lib/lapack/",
                                 "--user", "99999",
                                 "--group", "99999",
                                 "-R", "/bin/",
                                 "-R", "/lib/",
                                 "-R", "/lib64/",
                                 "-R", "/usr/",
                                 "-R", "/dev/urandom",
                                 "-R", "/sbin/",
                                 "--bindmount_ro", tmpInDir + ":/input/",
                                 "--bindmount_ro", scriptDir + ":/scripts/",
                                 "--bindmount_ro", absLibDir + ":/libdp/",
                                 "--bindmount", tmpOutDir + ":/output/",
                                 "--time_limit", str(resources['timeout']),
                                 "--rlimit_cpu", "10000",
                                 "--seccomp_string", "POLICY example { KILL { ptrace, process_vm_readv, process_vm_writev }} USE example DEFAULT ALLOW",  # No networking
                                 "--"] + cmd)
        proc.wait()
        try:
            # copy back the output.
            shutil.copyfile(tmpOutDir + outputFile, dataDir + outputFile)
        except:
            # TODO: Can absence of a file raise an exception and leak info
            libdp.log("Sandbox",  msg="No output from " + program)
        shutil.rmtree(tmpInDir)
        shutil.rmtree(tmpOutDir)


    thread1 = threading.Thread(target=computation, args=(int(resources['timeout']),))
    thread2 = threading.Thread(target=paddingMethod, args=(int(resources['timeout']) + 1,))
    thread1.start()
    thread2.start()
    thread1.join()
    thread2.join()
    libdp.log("Sandbox", msg="The padding thread meets the Sandbox")
    for _ in range(0, int(resources['cpu'])):
        semCPU.release()


def userProcedure(reqId):
    """Respond to the requests."""
    libdp.log("userProcedure")
    reqParams = configparser.SafeConfigParser()
    reqParams.read(libdp.wd(reqId, "public") + config.reqInfo)

    preparameters = reqParams.get('config', 'preProcParameters').split()
    preresources = libdp.parseToDic(reqParams.get('config', 'preResources'))

    numOutput = int(reqParams.get('config', 'numOutput'))

    postparameters = reqParams.get('config', 'postProcParameters').split()
    postresources = libdp.parseToDic(reqParams.get('config', 'postResources'))

    # Public Policy
    sys.path.append(config.publicPolicy)
    publicpolicy = __import__(config.publicPolicy)
    if publicpolicy.policy(reqId=reqId):
        libdp.updateTotalCost(config.totalCostStorage,
                              libdp.measureRisk(reqId))
        os.makedirs (libdp.wd(reqId, "private") + config.sensitiveData)
        shutil.copyfile(config.sensitiveData + 'data.ini',
                        libdp.wd(reqId, "private") + config.sensitiveData + 'data.ini')

        # insecureSandbox(reqId=reqId,
        #          program=libdp.wd(reqId, "public") + config.preProc,
        #          inputFile=libdp.wd(reqId, "private") + config.sensitiveData,
        #          outputFile=libdp.wd(reqId, "private") + config.preProcResult,
        #          extraParams=preparameters,
        #          resources=preresources)

        secureSandbox(reqId=reqId,
                 program= config.preProc,
                 inputFile= config.sensitiveData,
                 outputFile= config.preProcResult,
                 extraParams=preparameters,
                 resources=preresources)

        # Private Policy
        sys.path.append(config.privatePolicy)
        privatepolicy = __import__(config.privatePolicy)
        if not privatepolicy.policy(reqId=reqId):
            # TODO: replace with dummy value
            print ("xxxxx")

        # insecureSandbox(reqId=reqId,
        #         program=os.getcwd() + "/" + config.Clamp + ".py",
        #         inputFile=libdp.wd(reqId, "private") + config.preProcResult,
        #         outputFile=libdp.wd(reqId, "private") + config.randomizedResult,
        #         extraParams=[libdp.wd(reqId, "public"), str(numOutput)],
        #         resources={'timeout': 1, 'cpu': 1,}
        #         )

        shutil.copyfile(config.Clamp + '.py', libdp.wd(reqId, "public") +  config.Clamp + '.py' )
        secureSandbox(reqId=reqId,
                program=  config.Clamp + ".py",
                inputFile= config.preProcResult,
                outputFile= config.randomizedResult,
                extraParams=["/scripts/", str(numOutput)],
                resources={'timeout': 1, 'cpu': 1,}
                )

        # insecureSandbox(reqId=reqId,
        #         program=libdp.wd(reqId, "public") + config.postProc,
        #         inputFile=libdp.wd(reqId, "private") + config.randomizedResult,
        #         outputFile=libdp.wd(reqId, "private") + config.postprocResult,
        #         extraParams=postparameters,
        #         resources=postresources)

        secureSandbox(reqId=reqId,
                program= config.postProc,
                inputFile= config.randomizedResult,
                outputFile= config.postprocResult,
                extraParams=postparameters,
                resources=postresources)

        return True
    else:
        # run out of budget
        libdp.errorXml(libdp.wd(reqId, "private") + config.postprocResult,
                       "Policy denies the request")
        return False


@app.route('/hello')
def hello():
    """For the testing purpose."""
    return render_template('index.html')


@app.route('/publicpolicy')
def sendPolicy():
    """Share the public policy."""
    return send_from_directory('publicpolicy', 'publicpolicy.py')


@app.route('/totalcost')
def sendTotalcost():
    """Share the current total budget."""
    totalCost = libdp.getTotalCost(config.totalCostStorage)
    return str(totalCost)


@app.route('/remainedBudget')
def sendRemainedBudget():
    """Share the remaining budget."""
    totalCost = libdp.getTotalCost(config.totalCostStorage)
    budget = libdp.getBudget('publicpolicy/' + config.budgetStorage)
    return str(budget - totalCost)


@app.route('/form')
def showForm():
    """Submission form."""
    return render_template('form.html')


@app.route('/result/<string:reqId>')
def result(reqId):
    """Share the results and accessible to the aggregator."""
    try:
        return send_file(os.path.join(libdp.wd(reqId, "private")
                                      + config.postprocResult))
    except:
        return "Not found or not yet ready. <B> Please refresh. </B>"


@app.route('/process', methods=["POST"])
def uploadAnalysis(*analysis):
    """
    Process the requests.

    An analysis consists of these parts
    1) Preprocessing function
    2) Differential private mechanisms (here in the form a matrix)
    3) Post processing function
    """
    try:
        # reqId = the current time stamp as a string
        reqId = uuid.uuid1().hex[:3] #TODO : FIX, use all bytes
        os.makedirs(libdp.wd(reqId, "private"))
        os.makedirs(libdp.wd(reqId, "public"))
        request.files['preprocProg'].save(libdp.wd(reqId, "public")
                                          + config.preProc)
        request.files['postprocProg'].save(libdp.wd(reqId, "public")
                                           + config.postProc)
        counter = 0
        numoutputs = int(request.values.get("numoutputs"))
        for counter in range(0, numoutputs):
            analyseType = request.values.get("type[" + str(counter) + "]")
            if analyseType == 'analysesMatrix':
                f = open(libdp.wd(reqId, "public")
                         + str(counter) + '.analysesMatrix', "w")
                libdp.log("Analyses Matrix",
                          data=request.values.get(
                                "analysesData[" + str(counter) + "]"))
                f.write(
                    request.values.get("analysesData[" + str(counter) + "]"))
                f.close()
                counter += 1
            elif analyseType == 'analysesLaplace':
                f = open(libdp.wd(reqId, "public")
                         + str(counter) + '.analysesLaplace', "w")
                libdp.log("Analyses Laplace",
                          data=(counter, request.values.get(
                                "analysesData[" + str(counter) + "]")))
                f.write(request.values.get(
                    "analysesData[" + str(counter) + "]"))
                f.close()
                counter += 1
            else:
                libdp.log("Analysis Execution", msg="Unknown Analysis")
                raise Exception('Analysis Execution', 'Unknown Analysis')

        parser = configparser.SafeConfigParser()
        parser.add_section('config')
        parser.set('config', 'preProcParameters', request.values.get("preparameters"))
        parser.set('config', 'preResources', request.values.get("preresource"))

        parser.set('config', 'numOutput', str(counter))

        parser.set('config', 'postProcParameters', request.values.get("postparameters"))
        parser.set('config', 'postResources', request.values.get("postresource"))
        parser.write(
            open(libdp.wd(reqId, "public") + config.reqInfo, "w"))
    except:
        traceback.print_exc()

    libdp.log("Running sandbox")
    threadx = threading.Thread(target=userProcedure, args=(reqId,))
    threadx.start()
    return str(reqId)


parser = argparse.ArgumentParser(description="preTpost")
parser.add_argument(
    "--port", "-p",
    type=int,
    help="Port to listen on",
    default=5000,
)
parser.add_argument(
    "--parallel", "-x",
    type=int,
    help="Number of parallel requests",
    default=1,
)
parser.add_argument(
    "--verbose", "-v",
    type=bool,
    help="Verbose mode",
    default=True,
)
parser.add_argument(
    "--path", "-r",
    help="Request upload path (remove and recreate the directory)",
)
args = parser.parse_args()

if __name__ == '__main__':
    absLibDir = os.path.abspath(os.path.join(os.getcwd(), os.pardir, 'libdp/'))
    sys.path.append(absLibDir)
    try:
        import config
        import libdp

    except:
        raise
    # Initialization
    debug = args.verbose
    semCPU = threading.Semaphore(args.parallel)
    if not args.path:
        args.path = libdp.uploadDir
    if os.path.exists(args.path):
        shutil.rmtree(args.path)
    os.makedirs(libdp.uploadDir)

    # if debug:
    # AutoIndex(app, browse_root=libdp.uploadDir)
    app.run(use_reloader=False, debug=debug, host='0.0.0.0', port=args.port)


def cleanup():
    try:
        shutil.rmtree(args.path)
    except Exception:
        pass


atexit.register(cleanup)
