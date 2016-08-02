#!/usr/bin/python

import subprocess
import time
import sys
import getopt
import os
import inject
import threading
import hardwareReader
import csv
import re

ORKAHOME = os.environ['ORKAHOME']

#bwestfield and lc3311
#function to return app, monkey script and emulators from command-line args
def get_app_script_emul(argv):
	app =''
	monkey_script =''
	emul = ''

	help_text ="usage: ./main.py -a <app_name> -s <monkey_script> -m <emulator>"

	try:
		opts,args = getopt.getopt(argv,"ha:s:m:",["app=","script=","emul="])
	except getopt.GetoptError:
		fail_error(help_text)

	for opt,arg in opts:
		if opt == "-h" or len(argv) == 0:
			print help_text
			sys.exit()
		elif opt in ("-a","--app"):
			app = arg
		elif opt in ("-s","--script"):
			monkey_script = arg
		elif opt in ("-m","--emul"):
			emul = arg

	if app == '' or monkey_script == '' or emul == '':
		fail_error(help_text)
	
	return app,monkey_script,emul

#bwestfield
#function to get the package name from the app
def packageName(app):
	if not isinstance(app,str):
		#NB bwestfield, if this is ever changed back to a web app, this needs
		#to check the type is unicode
		print "supplied app name is of type {}, expected a \
			string".format(type(app))
		raise AttributeError('invalid parameter type')

	if not os.path.isfile(app):
		print "bad file path  - {}".format (app)
		error = "cannot find specified app - {}".format(app)
		raise OSError(error)

	if not os.path.exists(ORKAHOME + "dependencies/android-sdk/build-tools/22.0.1/aapt"):
		raise OSError("missing dependecies. Android 22.0.1 required in \
			$ORKAHOME/dependencies/android-sdk/")
    
	#NB bwestfield: This could pass -o to grep to only get the match, but I
	#haven't been able to write a regex that matches only the package name
	command = ORKAHOME + "dependencies/android-sdk/build-tools/22.0.1/aapt \
		dump badging {} | grep package:\ name ".format(app)
	word = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)

	#NB bwestfield: this is the work around for not being able to extract package na$
	# using grep
	package =  str(word.communicate()[0]).split(' ')
	for x in range(0,len(package)):
		if package[x].startswith("name"):
			name = package[x].split('\'')
			print "Found package name {}".format(name[1])
			return name[1]

#bwestfield
#calls the smali/injector functions
def injector(app, packDir):
	runProcess(ORKAHOME + "scripts/decompiler.sh " + app + " " + packDir)

	inject.inject(ORKAHOME + "/working/smali/" + packDir+ "/*")

	#recompile app
	runProcess("java -jar " + ORKAHOME + "dependencies/apktool_2.0.1.jar b " +
		ORKAHOME + "working/ -o " + ORKAHOME + "working/dist/orka.apk")

	#sign the app as debug
	runProcess("jarsigner -keystore " + ORKAHOME + "dependencies/debug.keystore "
		+ ORKAHOME + "working/dist/orka.apk androiddebugkey -storepass android ")
	return

#bwestfield
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
def loadEmulator(e,pName,monkey,emul,port):
    print "loading emulator"
    #set the event flag so that later part know the emulator is loaded
    cmd = ORKAHOME + "scripts/loadEmulator.sh " + ORKAHOME + "working/dist/orka.apk "
    print "starting the emulator"
    cmd += pName + " " + monkey + " " + emul + " " + port
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
        runProcess(ORKAHOME + "dependencies/android-sdk/platform-tools/adb shell "
                + "dumpsys batterystats > " + ORKAHOME + "working/dump.txt")

        while not os.path.exists(ORKAHOME + "working/dump.txt"):
                sleep(1)

        results.append(hardwareReader.getHWusage())

        #last thing to do is close the emulator
        runProcess(ORKAHOME + "dependencies/android-sdk/platform-tools/adb emu kill")

#bwestfield
#function that returns a dictionary containing the api costs
def loadAPIcosts():
    with open(ORKAHOME + 'dependencies/api costs.csv','r') as f:
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
	print "enter API"

        METHOD_NAME = 3
        #index of the string that will be used when decideding on how to log
        LINE_DIRECT = 2
        API_LOCATION =5

        #download logcat and save to file
        time.sleep(2)

        runProcess(ORKAHOME + "dependencies/android-sdk-linux/platform-tools/adb "
                + "logcat bwestfield:I *:S > " + ORKAHOME + "working/output.txt &")

        #two second delay to make sure the output has saved
        time.sleep(2)

        #dictionary of methods. Each method stores a counter, this stores the
        #number of instance of each api call
        meth={}

        #store the current method we are in
        method =''
        with open(ORKAHOME + "working/output.txt",'r') as log:
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

	app, monkey_script, emul = get_app_script_emul(argv)

	print "Running Orka"

	results1 = []
	results2 = []

	#get package name and directory
	pName = packageName(app)    
	packDir = ''
	packName = pName.split('.')
	for x in range(0,len(packName)):
		packDir += packName[x] + '/'
	packDir = packDir[:-1]

	#inject logging into app
	injector(app, packDir)

	e1 = threading.Event()

	t1 = threading.Thread(name = "loadE", target=loadEmulator,
			args=(e1,pName,monkey_script,"n7","5554"))

	t1.start()



	e2 = threading.Event()
	t2 = threading.Thread(name = "loadE", target=loadEmulator,
			args=(e2,pName,monkey_script,"none","5556"))
	t2.start()

        analyseData(e1, results)
	analyseData(e2, results)

	print results1
	print results2

#	f = open(emul, 'r')

#	lines = f.readline()
#	lines = lines.split(' ')

#	j = 5
#	for i in lines:
#		runProcess("xterm -hold -e ssh matrix0" + str(j) + " -X \'~/orka/orka/src/lauren2.py " + app + " " + monkey_script + " " + str(j) + " " + i + "\' &")
#		j += 3

#	runProcess('./lauren2.py ' + pName + ' ' + monkey_script + ' n7')

#    runProcess("xterm -hold -e " + cmd + " n7 &")
#    time.sleep(20)
#    runProcess("xterm -hold -e " + cmd + " 12-07-nexus6 &")

if __name__ == "__main__":
    main(sys.argv[1:])

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
