#!/usr/bin/python

import os


ORKAHOME = os.environ['ORKAHOME']

def getHWusage(avd):
    
    costDict={} 
    with open(ORKAHOME + "working/dump_" + str(avd) + ".txt",'r') as source:  
        #bool used to store if the routine shoul dbe writting to a dictionary
        write=False
        for lines in source:
            #the code is separated by blocks of length two
            #If we are writing and get to one of these separation blocks, 
            #we know that this is the end of the hardware usage
            if len(lines) == 2 and write:
                break
            #split each line and look for the estimated usage
            line = lines.split()

            if len(line)>1:
                if write:
		    if line[0].startswith("["):
			break;
                    elif line[0].startswith("Capacity"):
                        #remove the trailing comma
                        costDict["total battery usage"]=float(line[4][:-1])
                    #hardware usage, therefore should copy into dictionary
                    elif line[0] == "Uid":
                        #special case for Uids
                        if costDict.has_key("Process usage"):
                            costDict["Process usage"] += float(line[2])
                        else:
                            costDict["Process usage"] = float(line[2])
                    else:
                        #get full component name (these end with a ;)
                        i=0
                        name = ""
                        while not line[i].endswith(":"):
                            name += line[i] + " "
			    i+=1
                        #add last line
                        name += line[i][:-1]
                        #the next i will contain the energy costs
			if i == (len(line) - 1):
			    break
                        costDict[name] = line[i+1:]
                if len(line) > 3 and line[3] == "charge:":
		    print line
                    write = True
        source.close()

    return costDict

