#!/usr/bin/expect

set PORT [lindex $argv 0];

#simple expect script that logs into the Anroid telnet port (5554)
#then sets the charging status to off
spawn telnet localhost $PORT
expect "OK"
send "auth O27xCNHe1BGmyGT6\n"
expect "OK"
send "power ac off\n"
expect "OK"

