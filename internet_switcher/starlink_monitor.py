import asyncio
from datetime import datetime, timedelta

from typing import Awaitable, Callable, Coroutine, Optional

from spacex.starlink.aio import AsyncStarlinkDish
from spacex.starlink import DishStatus, CommunicationError

from internet_switcher.util.logging import LoggingMixin


class StarlinkStateTrigger:
    def __init__(self, monitor: 'StarlinkMonitor', name: str, func: Callable[[Optional[DishStatus]], None]):
        pass


class StarlinkMonitor(LoggingMixin):
    """Checks for changes in connection stability to Starlink, and fires events when it changes."""
    def __init__(self, starlink: AsyncStarlinkDish):
        self.starlink = starlink
        self.task = None
        self.running = False
        self.is_stable = None
        self.unstable_actions = []
        self.stable_actions = []
        self._reset_stats()
        self.pending = None
        self.connected_since = None

    def on_stable(self, func: Callable[[], Awaitable[None]]):
        """Call a method whenever the connection becomes stable."""
        self.stable_actions.append(func)

    def on_unstable(self, func: Callable[[], Awaitable[None]]):
        """Call a method when the connection becomes unstable."""
        self.unstable_actions.append(func)

    def flush_stats(self):
        """Fetch and reset the statistics for the running monitor."""
        current_stats = dict(self.stats)
        self._reset_stats()
        return current_stats

    def _reset_stats(self):
        self.stats = {
            'attempts': 0,
            'responses': 0,
            'connected': 0
        }

    def start(self):
        """Start the loop that checks whether the connection is stable or unstable."""
        self.running = True
        self.debug("Creating the loop task")
        self.task = asyncio.create_task(self._loop())

    def stop(self):
        self.running = False
        self.is_stable = None

    async def wait(self, seconds: float):
        """Similar to asyncio.sleep, but immediately raises exceptions if one is thrown."""
        stop_time = datetime.now() + timedelta(seconds=seconds)
        while True:
            if self.task.done():
                # Raise exceptions
                await self.task
            if datetime.now() < stop_time:
                # Yield to other tasks
                await asyncio.sleep(0.05)
            else:
                break

    async def _loop(self):
        while self.running:
            try:
                await self._check_connection()
            except CommunicationError:
                self.debug("Failed communication - marked as failure")
            finally:
                self.stats['attempts'] += 1
            await asyncio.sleep(0.25)  # TODO: Configure
            

    async def _check_connection(self):
        status = await self.starlink.fetch_status()
        self.stats['responses'] += 1
        self.stats['connected'] += 1 if status.connected else 0
        
        if self.is_stable is None:
            prefix = 'un' if not status.connected else ''
            self.debug(f"Initial check made. Marking conneciton as {prefix}stable")
            self.is_stable = status.connected
        
        elif not status.connected:
            self.connected_since = None
            if self.is_stable is True:
                await self._handle_unstable()
            
        elif status.connected and self.is_stable is False:
            if self.connected_since is None:
                self.debug("Got first connectected response")
                self.connected_since = datetime.now()
            elif datetime.now() - self.connected_since >= timedelta(seconds=15):  # TODO: Make configurable
                await self._handle_stable()
                

    async def _handle_unstable(self):
        self.debug("Conneciton became unstable.")
        self.is_stable = False
        await self._check_pending()
        if len(self.unstable_actions) == 0:
            self.debug("No unstable actions to run.")
        else:
            self.debug(f"Running {len(self.unstable_actions)} unstable actions")
            self.pending = asyncio.gather(*[action() for action in self.unstable_actions])

    async def _handle_stable(self):
        self.debug("Connection became stable.")
        self.is_stable = True
        await self._check_pending()
        if len(self.stable_actions) == 0:
            self.debug("No stable actions to run.")
        else:
            self.debug(f"Running {len(self.stable_actions)} stable actions")
            self.pending = asyncio.gather(*[action() for action in self.stable_actions])

    async def _check_pending(self):
        if self.pending is not None and not self.pending.done():
            self.warning("The previous connection change task is still running.")
            self.pending.cancel()
        elif self.pending is not None:
            # Raise any exceptions
            await self.pending
            self.pending = None
        