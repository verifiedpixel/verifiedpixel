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
