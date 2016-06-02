#from collections import Counter
#import re
import json


#class used to store the results of the log check. Has space for the number of
#calls and the apis that are called
class Routine:
    #only created when there has been at least one call
      
    def __init__(self,name,numberCalls):
        self.routineName = name
        self.calls=numberCalls
        self.Apis={}
 
    def copyApi(self,apiDict):
        self.Apis = apiDict
  
    def assignApiCost(self,api,cost):
        self.Apis[api] *= cost

    def removeApi(self,api):
        if self.Apis.has_key(api):
            del self.Apis[api]
    def to_JSON(self):
        objDict={}
        objDict['routineName'] = self.routineName
        
        objDict['calls'] = self.calls
        objDict['Apis'] = self.Apis
        return objDict
        
    def addCall(self):
        self.calls+=1

    def getRoutineName(self):
        return self.name
    
    def getTotalApiUsage(self):
        total = 0
        for value in self.Apis.values():
            total+= float(value)
        print self.routineName + " usage = " \
            + str(total)
        return total 

    def getAverageCost(self):
        return getTotalApiUsage() / self.calls

    def getName(self):
        return self.routineName

    def getApis(self):
        return self.Apis

    def getCalls(self):
        return self.calls

    def addApi(self,apiName):
        if self.Apis.has_key(apiName):
            self.Apis[apiName]+=1
        else:
            self.Apis[apiName] =1
 
