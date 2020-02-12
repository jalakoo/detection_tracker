import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# create a file handler
handler = logging.FileHandler('logs/info.log')
handler.setLevel(logging.INFO)

# create a logging format
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

# add the handlers to the logger
logger.addHandler(handler)

SHOULD_LOG = False

def enable_logging():
    global SHOULD_LOG
    SHOULD_LOG = True

def info(message):
    global SHOULD_LOG
    log(message, SHOULD_LOG)

def log(message, should_log=False):
    if should_log == True:
        logger.info(message)