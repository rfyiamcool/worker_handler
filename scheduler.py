#!/usr/bin/env python
# -*- coding:utf-8 -*-
import os
import time
import signal
import logging
from multiprocessing import Process
from setproctitle import setproctitle

from config import *
from log import logger
from daemonize import daemonize

logging.basicConfig(level=logging.DEBUG,format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s')

#你的业务逻辑
def worker(args):
    setproctitle("Monitor :Worker")   #设置进程的名字
    global is_running
    counter = 0
    while is_running:
        counter += 1
        if counter >= max_requests:
            raise("beyond max_requests")
        print "child pid %s"%os.getpid()
        time.sleep(0.1)


def kworker(args):
    setproctitle("Monitor :kworker")   #设置进程的名字
    global is_running
    time.sleep(5)


#接收信号，比如 kill，或者是键盘 ctrl c
def sig_handler(num, stack):
    logger.info('receiving signal, exiting...')
    global is_running
    is_running = False

#添加进程
def sig_add(num, stack):
    logger.info('receiving add signal, Add Process...')
    global jobs
    res = fork_process(process_num)
    jobs.update(res)

#亲切的干掉一个进程
def sig_reduce(num, stack):
    logger.info('receiving signal, Reduce Process...')
    global jobs
    for pid,pid_obj in jobs.iteritems():
        print pid,pid_obj
        jobs[pid]['is_running'] = False
        time.sleep(5)
        if pid_obj['obj'].is_alive():
            pid_obj['obj'].terminate()
#            os.kill(pid, signal.SIGKILL)
            logger.info('receiving reduce signal,%s be killed'%pid)
        return

#fork进程
def fork_process(x):
    jobs = {}
    for i in xrange(x):
        detail = {}
        p = Process(target = worker, args = (i,))
        p.start()
        detail['obj'] = p
        detail['is_running'] = True
        jobs[p.pid] = detail
    return jobs

#探测一个进程的状态
def check_status(pid):
    try:
        os.kill(pid,0)
        return True
    except:
        return False

#管理进程总控
def spawn_worker():
    global jobs
    parent_id = os.getpid()
    p = Process(target = kworker, args = ("1",))
    p.start()
    detail = {}
    detail['obj'] = p
    detail['is_running'] = True
    jobs[p.pid] = detail
    res = fork_process(process_num)
    jobs.update(res)
    while is_running:
        print jobs
        time.sleep(0.01)
        #第一种方法，调用非阻塞waitpid方法收尸
        if len(jobs) < process_num:
            res = fork_process(process_num - len(jobs))
            jobs.update(res)
        for pid in jobs.keys():
            try:
                if not check_status(pid):
#                if not jobs[pid]['obj'].is_alive():
                    del jobs[pid]
                os.waitpid(pid, os.WNOHANG)
            except:
                pass
    else:
        time.sleep(3)
        for pid in jobs:
            try:
                os.kill(pid,signal.SIGKILL)
            except:
                pass


if __name__ == '__main__':
    if daemon_flag:
        daemonize()
    setproctitle("Monitor :Master")
    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)
    signal.signal(signal.SIGTTIN, sig_add)
    signal.signal(signal.SIGTTOU, sig_reduce)
    #第二种方法，直接忽视子进程退出前发出的sigchld信号，交给内核，让内核来收拾，其实也是让内核用waitpid来解决。
    signal.signal(signal.SIGCHLD, signal.SIG_IGN)
    logger.info('main process: %d start', os.getpid())
    spawn_worker()
    logger.info('main: %d kill all jobs done', os.getpid())

