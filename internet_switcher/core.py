# SPDX-License-Identifier: Unlicense

import asyncio
from spacex.starlink.aio import AsyncStarlinkDish
from cradlepoint.wan import WanDevice

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
        self.connections = asyncio.create_task(self.fetch_connections())
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
                await monitor.wait(30)  # TODO: Set from config
                stats = monitor.flush_stats()
                if stats['attempts'] == 0:
                    self.error("The Starlink monitor process does not appear to be attempting status checks.")
                    if not self.config.ignore_errors:
                        raise ConnectionError("The Starlink monitor process does not appear to be attempting status checks.")
                self.debug(f"Starlink stats:\n\tAttempts:\t{stats['attempts']}\n\tResponses:\t{stats['responses']}\n\tConnected:\t{stats['connected']}")
        finally:
            self.debug("Stopping Dishy monitoring")
            monitor.stop()

    async def fetch_connections(self):
        self.debug("Fetching Ethernet and Cellular connections")
        devices = await WanDevice.from_api(self.cradlepoint)
        ethernet, cellular = await asyncio.gather(
            devices.filter_one(iface='eth0.1'),
            devices.filter_one(sim='sim1')
        )
        self.debug("Connections are ready!")
        assert ethernet is not None
        assert  cellular is not None
        return ethernet, cellular

    async def handle_stable_connection(self):
        self.debug("Handling stabalized connection")
        ethernet, cellular = await self.connections
        eth_priority = await ethernet.priority()
        cell_priority = await cellular.priority()
        self.debug(f"Priority: eth={eth_priority}, cell={cell_priority}")
        if eth_priority < cell_priority:
            self.debug("Doing nothing - ethernet is already prioritized!")
        self.info("Prioritizing ethernet")
        await cellular.priority(eth_priority + 1.1)

    async def handle_unstable_connection(self):
        self.debug("Handling unstable connection")
        ethernet, cellular = await self.connections
        eth_priority = await ethernet.priority()
        cell_priority = await cellular.priority()
        self.debug(f"Priority: eth={eth_priority}, cell={cell_priority}")
        if eth_priority > cell_priority:
            self.debug("Doing nothing - cell is already prioritized!")
        self.info("Prioritizing cellular")
        await cellular.priority(eth_priority - 1.1)
