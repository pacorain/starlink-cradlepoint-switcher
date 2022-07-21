# SPDX-License-Identifier: Unlicense

import logging

class LoggingMeta(type):
    def __new__(cls, name, bases, dct):
        mixin = super().__new__(cls, name, bases, dct)
        mixin._logger = logging.getLogger(f"{__name__}.{name}")
        mixin.debug = mixin._logger.debug
        mixin.info = mixin._logger.info
        mixin.warning = mixin._logger.warning
        mixin.error = mixin._logger.error
        mixin.critical = mixin._logger.critical
        mixin.log = mixin._logger.log
        return mixin

class LoggingMixin(object, metaclass=LoggingMeta):
    pass
