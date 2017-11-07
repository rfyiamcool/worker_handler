#!/usr/bin/env python
# -*- coding:utf-8 -*-
import os
import time
import signal
import logging
from multiprocessing import Process, Value

from setproctitle import setproctitle

from config import process_num, daemon_flag, pid_file
from log import logger
from daemonize import daemonize
from worker import kworker_handler, worker_handler


jobs = {}
is_running = True
running_status = Value('d', True)


#判断进程及lock是否存在
def set_exists_pid():
    continue_status = False
    if os.path.exists(pid_file):
        with open(pid_file, 'r') as f:
            pid = f.read()
        if len(pid) == 0:
            continue_status = True
        else:
            pid = int(pid)
            if check_status(pid):
                return False
            else:
                continue_status = True
    else:
        continue_status = True

    if continue_status:
        with open(pid_file, 'w') as f:
            logger.info('write pid %s'%os.getpid())
            f.write(str(os.getpid()))
    return continue_status


#接收信号，比如 kill，或者是键盘 ctrl c
def sig_handler(num, stack):
    logger.info('receiving signal, exiting...')
    global is_running
    global running_status
    running_status.value = False
    is_running = False


#添加进程
def sig_add(num, stack):
    logger.info('receiving add signal, Add Process...')
    #res = fork_process(process_num)
    res = fork_process(1)
    jobs.update(res)


#亲切的干掉一个进程
def sig_reduce(num, stack):
    logger.info('receiving signal, Reduce Process...')
    for pid, pid_obj in jobs.iteritems():
        jobs[pid]['is_running'] = False
        time.sleep(5)
        if pid_obj['obj'].is_alive():
            pid_obj['obj'].terminate()
#            os.kill(pid, signal.SIGKILL)
            logger.info('receiving reduce signal,%s be killed'%pid)
            return


#调用工作函数的入口
def request_worker(func, process_name):
    setproctitle(process_name)   #设置进程的名字
#    global running_status
    logger.info("child pid %s"%os.getpid())
    # counter = 0
    while running_status.value:
        s = func()
        if s:   #如果有返回值，那么判断该任务只想运行一次
            break


#fork进程
def fork_process(x):
    jobs = {}
    for i in xrange(x):
        detail = {}
        p = Process(target=request_worker, args=(worker_handler, "Monitor :worker"))
        p.start()
        detail['obj'] = p
        detail['is_running'] = True
        jobs[p.pid] = detail
    return jobs


#探测一个进程的状态
def check_status(pid):
    try:
        os.kill(pid, 0)
        return True
    except:
        return False


#管理进程总控
def spawn_worker():
    # parent_id = os.getpid()
    p = Process(target=request_worker, args=(kworker_handler, "Monitor :kworker"))
    p.start()
    detail = {}
    detail['obj'] = p
    detail['is_running'] = True
    jobs[p.pid] = detail
    res = fork_process(process_num)
    jobs.update(res)
    while is_running:
        time.sleep(0.01)
        #第一种方法，调用非阻塞waitpid方法收尸
        if len(jobs) < process_num:
            res = fork_process(process_num-len(jobs))
            jobs.update(res)
        for pid in jobs.keys():
            try:
                if not check_status(pid):
                    del jobs[pid]
                os.waitpid(pid, os.WNOHANG)
            except:
                pass
    else:
        _c = 0
        # interval = 0.1
        while 1:
            logger.info(str(_c))
            logger.info(str(jobs))
            if _c >= 30 or len(jobs) == 0:
                break
            for pid in jobs.keys():
                if not check_status(pid):
                    jobs.pop(pid)
                _c += 1
            time.sleep(0.1)
        for pid in jobs:
            try:
                os.kill(pid, signal.SIGKILL)
            except:
                pass
    os.remove(pid_file)


if __name__ == '__main__':
    if daemon_flag:
        daemonize()

    if not set_exists_pid():
        logger.error("service is alive")
        exit(0)

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
