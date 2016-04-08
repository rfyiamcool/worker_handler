#!/usr/bin/env python
# -*- coding:utf-8 -*-
import os
import time

def daemonize():
    pid=os.fork() # fork1
    if pid<0: # error
        print "fork1 error"
        return -1
    elif pid>0: # parent.
        exit(0)
    os.chdir(os.getcwd()) 
    os.setsid()
    pid=os.fork() # fork 2
    if pid<0:
        print "fork2 error"
        return -1
    elif pid>0:
        exit(0)
    os.umask(0)
    os.close(0)
    os.close(1)
    os.close(2)
    fd=os.open('/dev/null', 2)
    os.dup(fd)
    os.dup(fd)

if __name__ == "__main__":
    daemonize()
    time.sleep(30)
