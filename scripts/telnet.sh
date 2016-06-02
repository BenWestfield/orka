#!/usr/bin/expect

#simple expect script that logs into the Anroid telnet port (5554)
#then sets the charging status to off
spawn telnet localhost 5554
expect "OK"
send "power ac off\n"
expect "OK"

