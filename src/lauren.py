#!/usr/bin/python

import subprocess
import time
import sys
import getopt
import os
import inject

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

	if not os.path.exists("orka/orka/dependencies/android-sdk-linux/build-tools/22.0.1/aapt"):
		raise OSError("missing dependecies. Android 22.0.1 required in \
			~/orka/orka/dependencies/android-sdk-linux/")
    
	#NB bwestfield: This could pass -o to grep to only get the match, but I
	#haven't been able to write a regex that matches only the package name
	command = "~/orka/orka/dependencies/android-sdk-linux/build-tools/22.0.1/aapt \
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
	runProcess("~/orka/orka/scripts/decompiler.sh " + app + " " + packDir)

	inject.inject("~/orka/orka/working/smali/" + packDir+ "/*")

	#recompile app
	runProcess("java -jar ~/orka/orka/dependencies/apktool_2.0.1.jar b" +
		" ~/orka/orka/working/ -o ~/orka/orka/working/dist/orka.apk")

	#sign the app as debug
	runProcess("jarsigner -keystore ~/orka/orka/dependencies/debug.keystore"
		+ " ~/orka/orka/working/dist/orka.apk androiddebugkey -storepass android ")
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

def main(argv):
	app, monkey_script, emul = get_app_script_emul(argv)

	print "Running Orka"

	result = []

	#get package name and directory
	pName = packageName(app)    
	packDir = ''
	packName = pName.split('.')
	for x in range(0,len(packName)):
		packDir += packName[x] + '/'
	packDir = packDir[:-1]

	#inject logging into app
	injector(app, packDir)

	f = open(emul, 'r')

	lines = f.readline()
	lines = lines.split(' ')

	j = 5
	for i in lines:
		runProcess("xterm -hold -e ssh matrix0" + str(j) + " -X \'~/orka/orka/src/lauren2.py " + app + " " + monkey_script + " " + str(j) + " " + i + "\' &")
		j += 3

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

