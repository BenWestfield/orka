#!/bin/bash

##############################
#decompiler script, version 0.1
#written by Benjamin Westfield for masters thesis for Msc Computer Science from
#Imperial College London
#date 2nd July 2015
##############################
#takes two parameters:
#first is the name of the APK file
#second is the package name, with / instead of . (needed to find output dir)
#automated scrip to decompile an apk file into smali using Apktool. This also
#adds the smali version of the Logger class to the root directory. This allows
#calls to be made to this class


FILENAME=$1
PACKAGE=$2
echo 'Starting to decompile file'
echo 'loading apk file'
#copy apk into a temp directory if it exits, else throw exception
if ! [ -e $FILENAME ]
    then        
        echo "cannot find $FILENAME, please check the path"
        exit
fi

echo "decompiling apk file"
echo
#decompile with ApkTool, the -f will clear the working directory
java -jar ../dependencies/apktool_2.0.1.jar d $FILENAME -o ../working/ --force

echo "finished decompiling app"

echo -n "Inserting Logging functions" 
cp "../dependencies/Logger.smali" "../working/smali/$PACKAGE/Logger.smali"
echo "decompiling complete"
exit

