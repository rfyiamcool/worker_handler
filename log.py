from config import log_file
import logging

def get_logger(LOGFILE):
    logger = logging.getLogger('worker')
    logger.setLevel(logging.INFO)
    fh = logging.FileHandler(LOGFILE)
    fh.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    return logger

logger = get_logger(log_file)
