'''
stochss_compute.core.log_config

Global Logging Configuration
'''

from logging import getLogger

def init_logging(name):
    '''
    Call after import to initialize logs in a module file.
    To follow convention, use predefined __name__.

    Like so:

    from stochss_compute.core.log_config import init_logs
    logger = init_logs(__name__)

    :returns: A module specific logger with level set by global LOG_LEVEL.
    :rtype: logging.Logger
    '''
    logger = getLogger(name)
    return logger
    