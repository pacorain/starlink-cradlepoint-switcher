# SPDX-License-Identifier: Unlicense

import asyncio
from spacex.starlink.aio import AsyncStarlinkDish

from internet_switcher.config import Config
from internet_switcher.starlink_monitor import StarlinkMonitor
from internet_switcher.util.logging import LoggingMixin
from cradlepoint.api import CradlepointRouter


class InternetSwitcher(LoggingMixin):
    def __init__(self, config: Config):
        self.config = config
        self.starlink = AsyncStarlinkDish(address=f"{config.starlink_ip_address}:{config.starlink_port}")
        self.cradlepoint = CradlepointRouter(config)
        self.running = False

    @classmethod
    async def main(cls):
        cls.info("Loading config and initializing")
        config = Config.load()
        switcher = cls(config)

        try:
            cls.info("Testing connections")
            await switcher.connect()

            cls.info("Starting")
            await switcher.run()
        finally:
            cls.info("Closing connections")
            await switcher.close()

    async def connect(self):
        """Initiate connections needed to switch Internet connections"""
        await asyncio.gather(
            self.starlink.connect(),
            self.cradlepoint.connect()
        )
        self.running = True

    async def run(self):
        monitoring_task = asyncio.create_task(self.monitor_starlink())
        await monitoring_task

    async def close(self):
        """Closes the connections"""
        self.running = False
        await asyncio.gather(
            self.starlink.close(),
            self.cradlepoint.close()
        )

    async def monitor_starlink(self):
        monitor = StarlinkMonitor(self.starlink)
        monitor.on_stable(self.handle_stable_connection)
        monitor.on_unstable(self.handle_unstable_connection)
        self.info("Starting Dishy monitoring")
        monitor.start()
        try:
            while self.running:
                await asyncio.sleep(30)  # TODO: Set from config
                stats = monitor.flush_stats()
                if stats['attempts'] == 0:
                    self.error("The Starlink monitor process does not appear to be attempting status checks.")
                    if not self.config.ignore_errors:
                        raise ConnectionError("The Starlink monitor process does not appear to be attempting status checks.")
                self.debug(f"Starlink stats:\n\tAttempts:\t{stats['attempts']}\n\tResponses:\t{stats['responses']}\n\tConnected:\t{stats['connected']}")
        finally:
            self.debug("Stopping Dishy monitoring")
            monitor.stop()

    async def handle_stable_connection(self):
        pass

    async def handle_unstable_connection(self):
        pass


            
