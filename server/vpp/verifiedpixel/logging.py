import logging


logger = logging.getLogger('superdesk')
logger.setLevel(logging.INFO)


LOGGING_TEMPLATE = "\033[1m\033[03{color}mVerifiedPixel: \033[0m{msg}"


def info(msg):
    return logger.info(LOGGING_TEMPLATE.format(msg=msg, color=6))


def warning(msg):
    return logger.warning(LOGGING_TEMPLATE.format(msg=msg, color=3))


def error(msg):
    return logger.error(LOGGING_TEMPLATE.format(msg=msg, color=1))


def success(msg):
    return logger.info(LOGGING_TEMPLATE.format(msg=msg, color=2))


def debug(msg):
    return logger.debug(LOGGING_TEMPLATE.format(
        msg="DEBUG: {msg}".format(msg=msg), color=4
    ))


def print_task_exception(f):
    def wrapped(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            debug(e)
            raise(e)
    return wrapped
