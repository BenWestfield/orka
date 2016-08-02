#!/bin/bash

##script that loads an emulator and installs the program given as the
#arguement.
## This early version should only load one emulator. Later versions should take
#an emulator as an arguement

#if get time, sort out this parameter list so that it uses options rther than
#specified parameters
#rename the first arguement
#need to add the package to parameter list
APP=$1
PACKAGE=$2
MONKEY=${3}
AVD=$4
ADB=$ORKAHOME/dependencies/android-sdk/platform-tools/adb

#load the emulator
$ORKAHOME/dependencies/android-sdk/tools/emulator -avd $AVD -wipe-data &\
#-qemu -m 512 -enable-kvm &
#adding a slight delay to allow the emulator to start 
sleep 1
#wait for the emulator to load
$ADB wait-for-device
while true;do
     LOADED=$($ADB shell getprop sys.boot_completed | tr -d '\r')
#     'echo $LOADED
     if [ "$LOADED" = "1" ];
        then
            echo "emulator loaded"
            break
    fi
done

#unlock screen
$ADB shell input keyevent 82
#load the app
while [ ! -f $ORKAHOME/working/dist/orka.apk ];
do
    sleep 1
done
$ADB install $ORKAHOME/working/dist/orka.apk

#add slight wait before running telnet
sleep 4
$ORKAHOME/scripts/telnet.sh

      
#run monkey script
echo "running monkeyrunner script"
$ORKAHOME/dependencies/android-sdk/tools/monkeyrunner "$MONKEY"
    
