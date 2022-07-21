# SPDX-License-Identifier: Unlicense

import asyncio
from spacex.starlink.aio import AsyncStarlinkDish

from internet_switcher.config import Config
from internet_switcher.util.logging import LoggingMixin
from cradlepoint.api import CradlepointRouter


class InternetSwitcher(LoggingMixin):
    @classmethod
    async def main(cls):
        cls.info("Loading config and initializing")
        config = Config.load()

        starlink = AsyncStarlinkDish(address=f"{config.starlink_ip_address}:{config.starlink_port}")
        cradlepoint = CradlepointRouter(config)

        try:
            cls.info("Testing connections")
            await asyncio.gather(
                starlink.connect(),
                cradlepoint.connect()
            )

            cls.info("Starting loop")
            # TODO: What do I put here?
        finally:
            cls.info("Closing connections")
            await starlink.close()
            await cradlepoint.close()

            
