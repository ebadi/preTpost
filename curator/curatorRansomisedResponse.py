import sys
sys.path.append('curatorlibdp')
import curatorlibdp
sys.path.append('../libdp')
import libdp


if __name__ == '__main__':
    cost = 3
    data0 = libdp.buildStairCaseMatrix(cost/2.0, ["1", "-1"])
    data1 = libdp.buildStairCaseMatrix(cost/2.0, ["1", "-1"])
    timeoutPre = 2
    analysis = curatorlibdp.ReqResList()
    analysis.runIdenticalQuery(
        pre='analysis/randomized-response/preproc.py',
        preParam=str(cost/2.0),
        preresource= {'timeout' : 1 , 'cpu' : 2, 'mount':"configData|passwordData"},
        typeDataList=[('analysesMatrix', data0),
                      ('analysesMatrix', data1)],
        post='analysis/randomized-response/postproc.py',
        postParam=str(cost/2.0),
        postresource= {'timeout' : 1 , 'cpu' : 2, 'mount':"environementData"},
    )

    print(analysis.ReqReslist)
    tally0 = 0
    tally1 = 0
    count = 0

    for i in range(0, len(analysis.ReqReslist)):
        if analysis.ReqReslist[i] is not None:
            if analysis.ReqReslist[i].results is not None:
                count += 1
                tally0 += float(analysis.ReqReslist[i].results[0])
                tally1 += float(analysis.ReqReslist[i].results[1])

    print(tally0 / count, tally1 / count)
