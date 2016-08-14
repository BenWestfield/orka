#!/usr/bin/python

#
#Injection code
#
#written 3rd July 2015, Ben Westfield
#
#Smali injector for part of the Orka
# green code system made for my thesis at Imperial
#College London.
#
#This works with the custom logging classes made for android apps.

#The basic premise is that it loads a file the looks for all method invokations
#and API calls. It will then add a new line containing the 
#
#paramters:
#directory of smali code

import  os,  glob, fnmatch
import sys

#adds the code to print out the name of a new method
def addLogMethod(output):
    output.write('    invoke-static {}, Lcom/test/bbutton/Logger;->methodLog()I\n\n')

#function to return list of parameters and their types
def getLastParam(fi):
    PARAMLOC = 0 #const storing the parameter location
    #store current position
    pos = fi.tell()
    param ={} 

    #stores the parameters type
    pType = ""
    #adding invisible parameter for this
    param[0] = 'L'
    while True:
        line = next(fi)
        lineArray = line.split()
        #while there are more parameters, keep looping
        if (not len(lineArray) > 0) or lineArray[PARAMLOC] != '.param':
            break
        #objects always start with L and others are just letters
        param[int(lineArray[PARAMLOC+1][1])] = lineArray[len(lineArray)-1][0]

    #return to start of file
    fi.seek(pos)
    return param

#adds a specified line to the output file
def addLine(line,output):
    for i,elem in enumerate(line):
        output.write(str(line[i])+' ')

#add api logs
def addLogAPI(registerNumber,api,output):
    output.write('     const-string v'+str(registerNumber)+', "' + api+'"\n\n')
    output.write('     invoke-static/range {v'+str(registerNumber)+' .. v'+ \
                str(registerNumber) + '}, Lcom/test/bbutton/Logger;->apliLog(Ljava/lang/String;)I\n\n')

#returns true if the given string starts with an API
def findAPI(line):
    if line.startswith('Landroid/'):
        return True
    return False

##function that returns a string up to the first semicolon. Api calls end with
# a ; (with the method following a -> therefore this is used to identify these. Note: i is changed in this func
def printToSemi(line,i):
    string =''
    while line[i[0]] != ';':
        string += line[i[0]]
        countInc(i)
    #final method call is separated by a ;_>
    #iterator currently faces the ;, therefore if the next two chars are
    #->copy the method as well
    if line[i[0]+1] =="-" and line[i[0]+2] ==">":
        i[0] +=3
        string+='/'
        #append until reach the (
        while line[i[0]] != '(':
            string+= line[i[0]]
            countInc(i)
    return string 

#due to python not allowing immutable objects to be passed by
#reference/changed, this increases the counter for the api functions
def countInc(num):
   num[0] +=1


#returns a list of all apis in the given string
def getAPI(line):
    #start at 1 because we do not want the preceeding /
   #if we are not at the end of the string there might be more 
    i = [1]
    return printToSemi(line,i)

#function that checks if the parameters need to be moved back into the first 16
#registers. 
def needMoveParam(local,parameters):
   #if there are 16 locals, then there is no need to move
   #or continue
    if local >= 16:
        return False
    elif local < 16 and (local + parameters) >=16:
        #adding a local will push a parameter out of 4-bit registers 
        return True
    #base case
    return False

#function that searches until the end of a method for invoked APIs
#returning true if any are found
def hasApis(source):
    pos = source.tell()
    apiPresent = False
    while True:
        line =source.readline()
        lineArray = line.split()
        if len(lineArray) > 0:
            if lineArray[0].startswith('invoke-'):
                #if find API in last part of line
                if findAPI(lineArray[len(lineArray)-1]):
                    apiPresent = True
                    break
            if lineArray[0]=='.end':
                break
    source.seek(pos)
    return apiPresent

#returns error if a character cannot be cast into an int
def is_number(i):
    try:
        int(i)
        return True
    except ValueError:
        return False

#function to remap parameters that have been moved
def remapParameters(line,pMap):
    #stores the index of where p is in the string
    i = -1
    i =line.find('p')
    #if p is not in string
    if i ==-1:
        return line
    j=1
    tag = "p"
    #keep adding characters until first non digit
    #(done so p100 does no match with p1 or p10)
    while (i+j) <= len(line)-1 and is_number(line[i+j]):
        tag += line[i+j]
        j += 1

    if tag in pMap:
        return line[0:i] + pMap[tag] +\
            remapParameters(line[i+j:],pMap)
    else:
        #if not a good mapping, ignore
        return line[0:i+j] + \
            remapParameters(line[i+j:],pMap)


#function ot extract the total number of parameters from the parameter dict
def getTotalParams(parameters):
    total = 0
    for value in parameters.values():
        if value.startswith('J') or value.startswith('D'):
            total += 2
        else:
            total += 1
    return total


#main injetor functions
def injector(f):

    print "injecting %s" %(f)

   #recurse if it is a directory 
    if os.path.isdir(f):
        files = glob.glob(f)
        if not files:
            print "directory error"
        else:
            print "files is good"
        for root, dirnames, filenames in os.walk(f):
            for x in range(0,len(filenames)):
                print "running for new file"
                injector(os.path.join(f,filenames[x]))

            for x in range(0,len(dirnames)):
                injector(dirnames[x])

    elif os.path.isfile(f):
        apiCalls = []
        param={}

        with open(f,'r') as source:
            ignoreMethod = False
            remappedParam = False
            parameterMap = {}
            #ignore files that are not part of the app
            fileName = source.name
            if (fnmatch.fnmatch(fileName,'*R$*.smali') 
                or fileName.endswith("R.smali") 
                or fileName.endswith("Logger.smali")):
                source.close()
                return 

            output = open(fileName+'1','w')
            #used in gotofix
            depth = 0
            gotoApiCalls = []

            while True:
                lines = source.readline()
                #skip blank lines
                if lines =='':
                    break
                if remappedParam:
                    #only move after all parameters are decalre
                    if lines.find('.param') == -1:
                        lines = remapParameters(lines,parameterMap)

                line = lines.split(' ')
                #loop through each string and decission based on this
                for i in range(0,len(line)):
                   #ignore spaces
                    if line[i] !='':
                        if line[i].startswith('.method'):
                           #ignore contructors 
                            if line[i+1].startswith('public')\
                                and line[i+2].startswith('constructor')\
                                and line[i+3].startswith('<init>()V'):
                                ignoreMethod = True 
                                break
                            elif not hasApis(source):
                                print "no API calls, ignoring"
                                ignoreMethod = True
                                break

                        #methods safe to print after
                        if ((line[i].startswith('.end') and \
                                line[i+1].startswith('method'))
                            or line[i].startswith('.line') 
                            or line[i].startswith('return')):
                            #if there are apiCalls in the list, and
                            #the method is not being ignored then print
                            if len(apiCalls) > 0 and ignoreMethod ==False:
                                for j in range(0,len(apiCalls)):
                                    addLogAPI(newReg,apiCalls[j],output)
                                apiCalls = []
                            
                            if line[i].startswith('.end') and \
                                line[i+1].startswith('method'):
    
                                #reset everything at end of method
                                ignoreMethod = False
                                parameterMap ={}
                                param={}
                            break

                        #used to skip constructors and methods without apis
                        if ignoreMethod:
                            break
                        if line[i].startswith(':goto'):
                            #if a goto detected, need to start using a
                            #different list to store the apis so that only those
                            #on that level are logged before goto commands

                            #the depth location stores a list of all apis at
                            #that depth
                            lists= []
                            try:
                                print "index exists"
                                gotoApiCalls[depth] = []
                            except:
                                print "adding new index"
                                gotoApiCalls.append(lists)
                            depth +=1
                            break

                        if line[i]. startswith('goto') \
                            and line[i+1].startswith(':goto'):
                            #a loop commands has been found, log all apis for
                            #that tier
                            if depth >0:
                                #in a loop
                                for x in range(len(gotoApiCalls[depth-1])):
                                    addLogAPI(newReg,gotoApiCalls[depth-1][x],output)
                            #delete apis from the list to be logged, and lower
                            #the tier to the new in the stack
                            #check added so do not drop off tier
                                if depth >1:
                                    gotoApiCalls[depth-1] = []
                                else: 
                                    gotoApiCalls = []
                                depth -= 1
                            break

                        if line[i].startswith('.locals'):
                            #increment the locals variable 
                            addedReg = int(line[i+1])
                            param= getLastParam(source)
                            #get parameters
                            numParameters = getTotalParams(param)
                            #add one new register to locals
                            line[i+1] = addedReg +1 
                            remappedParam = needMoveParam(addedReg,numParameters)
                            #move the spare register
                            if remappedParam:
                                for key, value in sorted(param.iteritems()):
                                    #move two registers for 64bit types
                                    parameterMap['p' + str(key)]\
                                            = 'v' + str(addedReg)
                                    if value =='J' or value =='D':
                                        parameterMap['p' + str(key+1)]\
                                            = 'v' + str(addedReg+1)
                                        addedReg += 2
                                    else:
                                        addedReg += 1
                                    
                            newReg = addedReg 
                            line.append('\n') # for some reason the ending
                                              #new line is cut off
                            break

                        elif line[i] == '.prologue\n':
                            #log entering a new method after the prologue line
                            addLogMethod(output)
                            #move parameters 
                            if remappedParam:
                                for key,item in sorted(param.iteritems()):
                                    reg = 'p'+str(key)
                                    mapping = parameterMap[reg]
                                    #only doubles and longs use two
                                    #registers, so use move-wide for them
                                    if item == 'J' or item =='D':
                                        output.write('     move-wide/16 '\
                                            + mapping + ', ' + reg + '\n\n')
                                    elif item =='L':
                                        output.write('     move-object/from16 '\
                                            + mapping +', ' + reg +'\n\n')
                                    else:
                                        output.write('     move/from16 '\
                                            + mapping +', ' + reg +'\n\n')
                            break

                        elif line[i].startswith('invoke-'):
                            #find if API is being invoked
                            for j in range(i+1,len(line)):
                                if findAPI(line[j]):
                                    writeMethods = True
                                    #check if in a loop, if so only this should
                                    #be appended to a list that occured in the
                                    #loop
                                    if depth >0:
                                        #append to the end of the list in that
                                        #depth
                                        gotoApiCalls[depth-1].append(getAPI(line[j]))
                                    else:
                                        apiCalls.append(  getAPI(line[j]))
                           #we do not want to print as it is not safe to 
                            #call the new method yet. It is better to store these
                            #then wait until the next line/method
                            break

                addLine(line,output)

        output.close()
        source.close()
        #overwrite the original file


def inject(fileDir):

    print fileDir
    #glob finds pathname specified by the unix shell style
    files = glob.glob(fileDir)
    if not files:
        print 'directory does not exist'
        return

    for f in files:
        injector(f)

def main(argv):
    inject(sys.argv[1])


if __name__ == "__main__":
    main(sys.argv[1:])
