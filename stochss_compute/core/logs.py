'''
Logging utility for StochSS-Compute.
'''
import logging

GLOBAL_LOG_LEVEL = logging.INFO
GLOBAL_LOG_NAME = 'StochSS-Compute'
# pylint: disable=invalid-name unused-variable redefined-outer-name
def _set_log_level(log_level):
    GLOBAL_LOG_LEVEL = log_level
# pylint: enable=invalid-name unused-variable redefined-outer-name

def get_logger(name = GLOBAL_LOG_NAME):
    '''
    Always returns the same instance given the specified name.
    '''
    _ = logging.getLogger(name)
    _.setLevel(GLOBAL_LOG_LEVEL)
    _.propagate = False

    if not _.handlers:
        _formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        _handler = logging.StreamHandler()
        _handler.setFormatter(_formatter)
        _.addHandler(_handler)

    return _

log = get_logger()
