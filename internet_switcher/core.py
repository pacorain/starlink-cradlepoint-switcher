# SPDX-License-Identifier: Unlicense

import asyncio
from spacex.starlink.aio import AsyncStarlinkDish

from internet_switcher.config import Config
from internet_switcher.util.logging import LoggingMixin
from cradlepoint.api import CradlepointRouter


class InternetSwitcher(LoggingMixin):
    def __init__(self, config: Config):
        self.starlink = AsyncStarlinkDish(address=f"{config.starlink_ip_address}:{config.starlink_port}")
        self.cradlepoint = CradlepointRouter(config)

    @classmethod
    async def main(cls):
        cls.info("Loading config and initializing")
        config = Config.load()
        switcher = cls(config)

        try:
            cls.info("Testing connections")
            await switcher.connct()

            cls.info("Starting loop")
            # TODO: What do I put here?
        finally:
            cls.info("Closing connections")
            await switcher.close()

    async def connect(self):
        """Initiate connections needed to switch Internet connections"""
        await asyncio.gather(
            self.starlink.connect(),
            self.cradlepoint.connect()
        )

    async def close(self):
        """Closes the connections"""
        await asyncio.gather(
            self.starlink.close(),
            self.cradlepoint.close()
        )

            
