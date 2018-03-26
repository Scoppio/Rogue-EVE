import logging

logging.basicConfig(filename='debug.log', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)

# create logger
logger = logging.getLogger('Rogue-EVE')

# a simple way to define the log level using a dictionary
LOGLEVEL = {0: logging.DEBUG, 1:logging.INFO, 2: logging.WARNING, 3: logging.ERROR, 4: logging.CRITICAL}

logger.setLevel(LOGLEVEL[0])

# create file handler which logs even debug messages
fh = logging.FileHandler('file_path')
fh.setLevel(LOGLEVEL[0])

# create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(LOGLEVEL[0])
# create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)

# add the handlers to the logger
logger.addHandler(fh)
logger.addHandler(ch)

# 'application' code
logger.debug('debug message')
logger.info('info message')
logger.warning('warn message')
logger.error('error message')
logger.critical('critical message')
