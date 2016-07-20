#!/usr/bin/python

import subprocess

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

def main(cmd):
    runProcess("xterm -e " + cmd)

if __name__ == "__main__":
    main("./main.py -a ../HelloWorld_v1.0_apkpure.com.apk -s ../m2.py -m n7")
