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
import results

ORKAHOME = os.environ['ORKAHOME']
ORKASDK = os.environ['ORKASDK']

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

	if not os.path.exists(ORKASDK + "build-tools/22.0.1/aapt"):
		raise OSError("missing dependecies. Android 22.0.1 required in \
			$ORKASDK")
    
	#NB bwestfield: This could pass -o to grep to only get the match, but I
	#haven't been able to write a regex that matches only the package name
	command = ORKASDK + "build-tools/22.0.1/aapt \
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
	print "decompiling"
	runProcess(ORKAHOME + "scripts/decompiler.sh " + app + " " + packDir)

	print "injecting"
	inject.inject(ORKAHOME + "working/smali/" + packDir + "/*")

	#recompile app
	print "recompiling"
	runProcess("java -jar " + ORKAHOME + "dependencies/apktool_2.2.0.jar b " +
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
def analyseData(e,port):

	result = []	

        print "entering analyse data"

        #do no start analysing until the emulator is loaded and the test has been
        #run
        while not e.isSet():
                e.wait()

        #get API data
        result.append(analyseAPI())

        print "Total API energy usage"

        #dump battery stats into dump.txt
        runProcess(ORKASDK + "platform-tools/adb -s emulator-" + port + " shell "
                + "dumpsys batterystats > " + ORKAHOME + "working/dump.txt")

        while not os.path.exists(ORKAHOME + "working/dump.txt"):
                sleep(1)

        result.append(hardwareReader.getHWusage())

	print port
	print result
	print "MAIN: methods is " + str(len(result[0]))
    	print "MAIN: hardware is " + str(len(result[1]))
	
	#getRelativeUses(result[1])

        #last thing to do is close the emulator
        runProcess(ORKASDK + "platform-tools/adb -s emulator-" + port + " emu kill")

	

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

        runProcess(ORKASDK + "platform-tools/adb "
                + "logcat -v brief bwestfield:I *:S > " + ORKAHOME + "working/output.txt &")

        #two second delay to make sure the output has saved
        time.sleep(2)

        #dictionary of methods. Each method stores a counter, this stores the
        #number of instance of each api call
        meth={}
	print "meth ", meth

        #store the current method we are in
        method =''
        with open(ORKAHOME + "working/output.txt",'r') as log:
                for lines in log:
                        line = lines.split(' ')
			print line
                        #then one of the inserted logs
                        if line[0].startswith("I/bwestfield"):
                                #if method call
                                if line[LINE_DIRECT] =='entering':
                                        method = sanitise(line[METHOD_NAME])
                                        if not meth.has_key(method):
                                                #if not in dictionary, add method
                                                routine = results.Routine(method,1)
                                                meth[routine.getName()] = routine
						print meth[routine.getName()]
                                        else:
                                                meth[method].addCall()
                                elif line[LINE_DIRECT] =='making':
					print line[API_LOCATION]
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

#Outputting the resutls
#function to relate the total application usage to
#more meaningful item such as watching HD video or
#web browsing
def getRelativeUses(hardwareUse):
    totalUse = hardwareUse['total battery usage']
    #percentage of the battery drained (capacity listed as 1000 in
  #Dumpsys)
    drainPercent = totalUse /1000
    results =[]
    results.append(totalUse)
    #web browsing (9 hrs or 32400 seconds)
    print "Relative uses of energy on the NEXUS 7"
    print "the energy used by this programme could have instead run"
    print "the below activity for the shown time (in seconds)"
    print "Web browsing: %f" % round(drainPercent * 32400,4)
    #HD Video (10 hours or 36000 seconds)
    print "HD Video: %f"% round(drainPercent * 36000,4)
    #3D gaming (4 hours or 14400 seconds)
    print "3D gaming: %f" % round(drainPercent * 14400,4)

def main(argv):

	app, monkey_script, emul = get_app_script_emul(argv)

	print "Running Orka"


	#get package name and directory
	pName = packageName(app)    

	packDir = ''
	packName = pName.split('.')
	for x in range(0,len(packName)):
		packDir += packName[x] + '/'
	packDir = packDir[:-1]

	print packDir

	#inject logging into app
	injector(app, packDir)

	lines = [line.rstrip('\n') for line in open(emul)]

	j = 5554

	for i in lines:
		e = threading.Event()
		t = threading.Thread(name = "loadE", target=loadEmulator,
			args=(e, pName, monkey_script, i, str(j)))
		t.start()
	        t2 = threading.Thread(name = "results", target=analyseData,
                        args=(e, str(j)))
		t2.start()
		j += 2




	"""
	threads = []
	j = 4

	for i in lines:
		e = threading.Event()
		t = threading.Thread(name = "loadE", target=loadEmulator,
			args=(e, pName, monkey_script, i, "555" + str(j)))
		t.start()
		threads.append(t)

	for t in threads:
		t.join()

	print "emulators loaded"
	"""

	"""
	e1 = threading.Event()

	t1 = threading.Thread(name = "loadE", target=loadEmulator,
			args=(e1,pName,monkey_script,"n7","5554"))

	t1.start()



	e2 = threading.Event()
	t2 = threading.Thread(name = "loadE", target=loadEmulator,
			args=(e2,pName,monkey_script,"none","5556"))
	t2.start()

	t3 = threading.Thread(name = "res1", target=analyseData,
			args=(e1, "5554"))
	t3.start()

	t4 = threading.Thread(name = "res2", target=analyseData,
			args=(e2, "5556"))

	t4.start()
	"""

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

