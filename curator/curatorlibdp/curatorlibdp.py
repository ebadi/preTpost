import time
import requests
import agentlist
from xml.etree.ElementTree import Element, SubElement, tostring, fromstring, parse


class ReqResList:
    def __init__(self):
        self.ReqReslist = [ReqRes(agent) for agent in agentlist.agents]

    def __repr__(self):
        return str(self.ReqReslist)

    def runIdenticalQuery(self,         pre , preParam, preresource, 
                          typeDataList, post, postParam,postresource):
        for i in range(0, len(self.ReqReslist)):
            self.ReqReslist[i].sendAnalysis(
                pre=pre,
                preParam=preParam,
                preresource = preresource,
                typeDataList=typeDataList,
                post=post,
                postParam=postParam,
                postresource=postresource
                )
        timeoutPolicy = 2
        timeoutT = 2
        timeoutPost = 2
        time.sleep(preresource['timeout'] + timeoutPolicy + timeoutT + timeoutPost)
        for i in range(0, len(self.ReqReslist)):
            self.ReqReslist[i].collectResults()


class ReqRes:
    def __init__(self, agent):
        self.budget = 0.0
        # List of tuples (name, cost, result)
        self.results = dict()
        self.reqId = ''
        self.uri = agent
        self.numOutput = 1
        try:
            r = requests.get(self.uri + 'remainedBudget')
            self.budget = float(r.text.split()[0])
        except:
            self.budget = 0

    def sendAnalysis(self, pre, preParam, preresource, typeDataList, post,
                     postParam, postresource):
        """Send an analysis to the agent."""
        self.numOutput = len(typeDataList)
        l = dict()
        for i in range(0, self.numOutput):
            aType, aData = typeDataList[i]
            l.update({'analysesData[' + str(i) + ']': aData})
            l.update({'type[' + str(i) + ']': aType})

        l.update({'preresource': 'timeout:' + str(preresource['timeout']) + ';cpu:' +  str(preresource['cpu'])  + ';mount:' +  preresource['mount']})
        l.update({'numoutputs': self.numOutput})
        l.update({'preparameters': preParam})
        l.update({'postparameters': postParam})
        l.update({'postresource': 'timeout:' + str(postresource['timeout']) + ';cpu:' +  str(postresource['cpu'])  + ';mount:' +  postresource['mount']})

        multiple_files = [('preprocProg',
                          ('preProcProgPredicates.py',  open(pre, 'rb'))),
                          ('postprocProg',
                          ('postProcProgPredicates.py', open(post, 'rb'))),
                          ]
        try:
            req = requests.post(
                url=self.uri + "process",
                data=l,
                files=multiple_files)
            self.reqId = req.text
        except Exception as e:
            print(str(e))
            pass

    def __repr__(self):
        """To print the current budget, the request and the response"""
        return (
            "\nreqId:" + self.reqId +
            " uri:" + self.uri +
            " budget:" + str(self.budget) +
            " results:{" + self.result2str() + "}"
             )

    def result2str(self):
        s = ""
        for k, v in (self.results).items():
            s += (str(k) + '=' + str(v) + ',')
        return(s)

    def collectResults(self):
        """Collect results from agents."""
        resp = requests.get(self.uri + "result/" + self.reqId)
        try:
            tree = fromstring(resp.text)
            for tags in tree.iter('result'):
                if int(tags.attrib['id']) < self.numOutput:
                    self.results[int(tags.attrib['id'])] = tags.text
        except:
            self.results = None
