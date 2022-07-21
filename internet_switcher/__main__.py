# SPDX-License-Identifier: Unlicense

import asyncio

from internet_switcher.core import InternetSwitcher

import logging


if __name__ == '__main__':
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logging.basicConfig()
    asyncio.run(InternetSwitcher.main())