#!/usr/bin/python

#------------------------------
#--	Injector --
#------------------------------
#- first verion of the injector
#- 

#------------------------------

#import pygal
import sys, getopt
import os 
import subprocess 
import csv 
import time 
import results
import threading
import inject
import hardwareReader
import re

ADB = "../dependencies/android-sdk-linux/platofrm-tools/adb"
EMULATOR = "../dependencies/android-sdk-linux/tools/emulator"
EMU = "n7"

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
    if not os.path.exists("../dependencies/android-sdk-linux/build-tools/22.0.1/aapt"):
        raise OSError("missing dependecies. Android 22.0.1 required in \
            ../dependencies/android-sdk-linux/")
    #NB bwestfield: This could pass -o to grep to only get the match, but I
    #haven't been able to write a regex that matches only the package name
    command = "../dependencies/android-sdk-linux/build-tools/22.0.1/aapt \
         dump badging {} | grep package:\ name ".format(app)
    word = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
    #NB bwestfield: this is the work around for not being able to extract package name 
    # using grep
    package =  str(word.communicate()[0]).split(' ')
    for x in range(0,len(package)):
        if package[x].startswith("name"):
            name = package[x].split('\'')
            print "Found package name {}".format(name[1])
            return name[1]

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

#calls the smali/injector functions
def injector(APP,packDir):
    #run the decompiler
    runProcess("../scripts/decompiler.sh " + APP + " " + packDir)
    inject.inject("../working/smali/" + packDir+ "/*")
    #recompile
    runProcess("java -jar ../dependencies/apktool_2.0.1.jar b" +
    " ../working/ -o ../working/dist/orka.apk")

    #sign the app as debug
    runProcess("jarsigner -keystore ../dependencies/debug.keystore"
    + " ../working/dist/orka.apk androiddebugkey -storepass android ")
    print "\n\napp injected"
    return 
#function that returns a dictionary containing the api costs
def loadAPIcosts():
    with open('../dependencies/api costs.csv','r') as f:
        reader = csv.reader(f)
        costs=dict()
        for rows in reader:
            api = rows[0].split("(")
            value = rows[1]
            costs[api[0]]= value
    return costs

#removes hidden characters and formats
def sanitise(api):
    sanitisedApi = api.replace("/",".")
    sanitisedApi = re.sub(r'\s+', '',sanitisedApi)
    return sanitisedApi

#function that draws the APIs from logcat then compares to the list
#of API costs. Returns a dictionary of Routine object
def analyseAPI():
    METHOD_NAME = 3
    #index of the string that will be used when decideding on how to log
    LINE_DIRECT = 2
    API_LOCATION =5
    #download logcat and save to file
    time.sleep(2)
    runProcess("../dependencies/android-sdk-linux/platform-tools/adb "
    + "logcat bwestfield:I *:S > ../working/output.txt &")
    #two second delay to make sure the output has saved
    time.sleep(2)
    #dictionary of methods. Each method stores a counter, this stores the
    #number of instance of each api call
    meth={}
    #store the current method we are in
    method =''
    with open("../working/output.txt",'r') as log:
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

#function to load the emulator and install the app
def loadEmulator(e,pName,monkey):
    print "loading emulator" 
    #set the event flag so that later part know the emulator is loaded
    cmd = "../scripts/loadEmulator.sh ../working/dist/orka.apk "
    print "starting the emulator"
    cmd += pName + " " + monkey
    runProcess(cmd)
    print "emulator finished"

    print "event set"
    e.set()

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
    runProcess("../dependencies/android-sdk-linux/platform-tools/adb shell "
        + "dumpsys batterystats > ../working/dump.txt")

    while not os.path.exists("../working/dump.txt"):
        sleep(1)
    results.append(hardwareReader.getHWusage())
    #last thing to do is close the emulator
    runProcess("../dependencies/android-sdk-linux/platform-tools/adb emu kill")
    

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


"""
def generateGraph (results):
     routines = results[0]
     apiChart = pygal.Pie(width=600, height =500)
     apiChart.title = "Total API energy usage by routine (J)"
  
     total =0
     for x in xrange(len(routines)):
         total += routines[x].getTotalApiUsage()
     print "###############Total Usage of the app:"
     print total

     #add to the pie chart
     for x in xrange(len(routines)):
        name = routines[x].getName()
        apiChart.add(name,[{'value':\
                    routines[x].getTotalApiUsage()/total,\
                    'label':name + "\n"  +
                    str(round(routines[x].getTotalApiUsage(),6))\
                    + "J"
                    }])

     apiChart.render_to_png('/tmp/chart.png')

     #get the data to populate the table
     #highestRoutines = getHighestRoutines(routines)
 
     #check if there are existing cookies 
     #hasCookies= hasPrevious()
     #cookie = setCookies(total,highestRoutines)
 
     #make the hardware chart
     #hwChart= pygal.Pie(width=700,height=500)
     #hwChart.title = "Total hardware usage:"
     #for key,value in hardware.iteritems():
     #    if key != "total battery usage":
     #        usage = float(value)/float(hardware['total battery usage'])
     #        hwChart.add(
     #        key
     #        , [{
     #        'value':usage,
     #        'label':"usage = " +str(round(value,6))
     #        }])
 
     #make charts
     #costChart = apiChart.render(is_unicode=True)
     #hwChart = hwChart.render(is_unicode=True)
"""

def generateGraph(results):
    print "worked"

def fail_error (text): 
    print text
    sys.exit(2)

def get_app_and_script (argv):
    app =''
    monkey_script =''
    help_text ="usage: orka.py -app <app_name> -script <monkey_script>"
    try:
        opts,args = getopt.getopt(argv,"ha:s:",["app=","script="])
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
    if app == '' or monkey_script == '':
        fail_error(help_text)
    return app,monkey_script

#main applicaiton. Takes the app name and the monkey script
def main(argv):
    app,monkey_script = get_app_and_script(argv)
    print "Running Orka"
    print "Loading emulator " +  EMU
    print "\n\n\----------"
    print "\n\nBeginning code injecttion"
    print "Loading apk file"
    
    results =[]
    pName = packageName(app)
    packName =  pName.split('.')

    packDir = ''
    for x in range(0,len(packName)):
        packDir += packName[x] + '/'
    #remove last /
    packDir = packDir[:-1]
    #inject logging into app
    injector(app,packDir)
    
    e = threading.Event()
    t1 = threading.Thread(name = "loadE", target=loadEmulator,
                            args=(e,pName,monkey_script))
    t1.start()

    analyseData(e,results)
    print "MAIN: methods is " + str(len(results[0]))
    print "MAIN: hardware is " + str(len(results[1]))
    #delete the App and script
    print results
    #CR bwestfield: reapply cleaning of ./working/
#    runProcess("rm -f " + app)
 #   runProcess("rm -f " + monkeyScript)
    getRelativeUses(results[1])
    generateGraph(results)
    return results

if __name__ == "__main__":
#change the main to instead search for command line arguments
    main(sys.argv[1:])

