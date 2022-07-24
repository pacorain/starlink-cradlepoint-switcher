# SPDX-License-Identifier: Unlicense

import logging

class LoggingMeta(type):
    def __new__(cls, name, bases, dct):
        logger = logging.getLogger(f"{__name__}.{name}")
        dct.update({
            'debug': logger.debug,
            'info': logger.info,
            'warning': logger.warning,
            'error': logger.error,
            'critical': logger.critical,
            'log': logger.log,
            '_logger': logger
        })
        mixin = super().__new__(cls, name, bases, dct)
        return mixin

class LoggingMixin(object, metaclass=LoggingMeta):
    pass
