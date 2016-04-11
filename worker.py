#!/usr/bin/env python
# -*- coding:utf-8 -*-
import os
import time

from log import logger

#你的业务逻辑
def kworker_handler():
    time.sleep(5)
    return True

def worker_handler():
    time.sleep(0.01)
    logger.info('this is worker_handler')
