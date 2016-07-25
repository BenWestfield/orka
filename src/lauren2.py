#!/usr/bin/python

import sys
import threading
import subprocess
from random import randint

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
    cmd = "orka/orka/scripts/loadEmulator.sh ../working/dist/orka.apk "
    print "starting the emulator"
    cmd += pName + " " + monkey + " " + emul
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

def main(argv):

	print "lauren2"

	results = []

	pName = argv[0]
	monkey_script = argv[1]
	emul = argv[2]

	e = threading.Event()
	t1 = threading.Thread(name = "loadE", target=loadEmulator,
		args=(e, pName, monkey_script, emul))
	
	t1.start()

	return


if __name__ == "__main__":
	main(sys.argv[1:])
