#!/bin/bash
#
###############################
##### reCompiler v0.1
#
#
#written by Benjamin Westfield as part of thesis for Msc Computer Science at
#Imperial college London
#
#This script will change all .smali1 files (created by the inject.py program
#and turn these into .smali. The files are then combined back into an apk file


#parameters:
#directory of the smali code (needs to be in single ')

#make sure the directory exists


PATH=$1
#check the .smali1 code exists
#bash has issues with wild cards in if exists. Rerouting ls ourput from
#standard error. If this = 0, then the files exist
if ls "$PATH/*.smali1" 1> /dev/null 2>&1;
    then
        echo "cannot find the instrumented files, have the scripts been run
        correctly?"
        exit
fi


echo -n "recompiling app...."
#recompiles the app and renames it orka.pak
java -jar $ORKAHOME/dependencies/apktool_2.0.1.jar b ../working/ -o test.apk 

echo "complete"
