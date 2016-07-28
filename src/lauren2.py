#!/usr/bin/python

import sys
import threading
import subprocess
from random import randint
import time
import csv
import os
import hardwareReader
import re
import datetime

#function to run a single process in a shell for its entirety
def runProcess(cmd):
    print "Running process " + cmd
    if not (isinstance(cmd,unicode) or isinstance(cmd,str)):
        raise AttributeError('invalid command supplied as parameter')
    p =subprocess.Popen(cmd,shell=True)
    p.wait()

    if p.returncode != 0:
        print "process wont run!!"
        error = "invalid command attempted to be executed in\
            runProcess - {}".format(cmd)
        raise RuntimeError(error)


#function to load the emulator and install the app
def loadEmulator(e,pName,monkey,emul):
    print "loading emulator"
    #set the event flag so that later part know the emulator is loaded
    cmd = "orka/orka/scripts/loadEmulator.sh orka/orka/working/dist/orka.apk "
    print "starting the emulator"
    cmd += pName + " " + monkey + " " + emul
    runProcess(cmd)
    print "emulator finished"

    print "event set"
    e.set()

#bwestfield
def analyseData(e,results):

	print "entering analyse data"

	#do no start analysing until the emulator is loaded and the test has been
	#run
	while not e.isSet():
		e.wait()

	#get API data
	results.append(analyseAPI())

	print "Total API energy usage"

	#dump battery stats into dump.txt
	runProcess("orka/orka/dependencies/android-sdk-linux/platform-tools/adb shell "
		+ "dumpsys batterystats > orka/orka/working/dump.txt")

	while not os.path.exists("orka/orka/working/dump.txt"):
		sleep(1)

	results.append(hardwareReader.getHWusage())
    
	#last thing to do is close the emulator
	runProcess("orka/orka/dependencies/android-sdk-linux/platform-tools/adb emu kill")

#bwestfield
#function that returns a dictionary containing the api costs
def loadAPIcosts():
    with open('orka/orka/dependencies/api costs.csv','r') as f:
        reader = csv.reader(f)
        costs=dict()
        for rows in reader:
            api = rows[0].split("(")
            value = rows[1]
            costs[api[0]]= value
    return costs


#bwestfield
#removes hidden characters and formats
def sanitise(api):
	sanitisedApi = api.replace("/",".")
	sanitisedApi = re.sub(r'\s+', '',sanitisedApi)
	return sanitisedApi


#bwestfield
#function that draws the APIs from logcat then compares to the list
#of API costs. Returns a dictionary of Routine object
def analyseAPI():
	METHOD_NAME = 3
	#index of the string that will be used when decideding on how to log
	LINE_DIRECT = 2
	API_LOCATION =5

	#download logcat and save to file
	time.sleep(2)
    
	runProcess("orka/orka/dependencies/android-sdk-linux/platform-tools/adb "
		+ "logcat bwestfield:I *:S > orka/orka/working/output.txt &")

	#two second delay to make sure the output has saved
	time.sleep(2)

	#dictionary of methods. Each method stores a counter, this stores the
	#number of instance of each api call
	meth={}
    
	#store the current method we are in
	method =''
	with open("orka/orka/working/output.txt",'r') as log:
		for lines in log:
			line = lines.split(' ')
			#then one of the inserted logs
			if line[0].startswith("I/bwestfield"):
				#if method call
				if line[LINE_DIRECT] =='entering':
					method = sanitise(line[METHOD_NAME])
					if not meth.has_key(method):
						#if not in dictionary, add method
						routine = results.Routine(method,1)
						meth[routine.getName()] = routine
					else:
						meth[method].addCall()
				elif line[LINE_DIRECT] =='making':
 					api = sanitise(line[API_LOCATION])
					if method != '':
						meth[method].addApi(api)
	log.close()

	#CR-soon bwestfield for bwestfield: This process could be moved
	#into the above loop
	costs = loadAPIcosts()

	#add the API costs to the number of calls
	for routines in meth.values():
		apiDict = routines.getApis()
		#used so as not to amend dict during iteration
		deleteList=[]
		for key in apiDict.keys():
			if costs.has_key(key):
				routines.assignApiCost(key,float(costs[key]))
			else:
				deleteList.append(key)
		for x in range(len(deleteList)):
			routines.removeApi(deleteList[x])

	#CR-soon bwestfield: data no longer needs to be serialized
	#serialise the data so it can be sent as json
	serial_meth=[]
	for value in meth.values():
		serial_meth.append(value.to_JSON())
	return serial_meth


def main(argv):

	results = []

	pName = argv[0]
	monkey_script = argv[1]
	emul = argv[3]
	machine = argv[2]

	print machine

	e = threading.Event()
	t1 = threading.Thread(name = "loadE", target=loadEmulator,
		args=(e, pName, monkey_script, emul))
	
	t1.start()

	analyseData(e, results)

        f = open('orka-matrix0' + machine + '-' + datetime.datetime, 'w')
        f.write(results)
        f.close()


	return


if __name__ == "__main__":
	main(sys.argv[1:])
