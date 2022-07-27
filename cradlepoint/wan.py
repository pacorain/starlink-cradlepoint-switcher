# SPDX-License-Identifier: Unlicense

from typing import TYPE_CHECKING, List, Optional

from warnings import warn

from cradlepoint.util import asyncproperty

if TYPE_CHECKING:
    from cradlepoint.api import CradlepointRouter


class WanDevice:
    def __init__(self, cradlepoint: 'CradlepointRouter', id: str = None, name: Optional[str]=None, status: Optional[dict]=None, config: Optional[dict]=None):
        self.api = cradlepoint
        if id:
            self.id = id
        elif status:
            self.id = status['config']['_id_']
        elif config:
            self.id = config['_id_']
        else:
            raise ValueError("Must pass ID, or status to obtain ID from")
        self._name = name
        self._status = status
        self._config_ix = None

    @classmethod
    async def from_api(cls, cradlepoint: 'CradlepointRouter') -> List['WanDevice']:
        devices = []
        wan_devices = await cradlepoint.status.wan.devices()
        for name, status in wan_devices.items():
            devices.append(cls(cradlepoint, name=name, status=status))
        return WanDeviceCollection(devices)

    async def matches_filter(self, **kwargs):
        for key, val in kwargs.items():
            if key in ('iface', 'port', 'sim'):
                info = (await self.status())['info']
                if key not in info:
                    return False
                if info[key] != val:
                    return False
        return True

    async def status(self):
        if self._status is None:
            if self._name is not None:
                self._status = await self.api.status.wan.devices[self._name]()
            else:
                for name, device in (await self.api.status.wan.devices()).items():
                    if device['config']['_id_'] == self.id:
                        self._name = name
                        self._status = device
        return self._status

    async def config(self):
        return await self.api.config.wan.rules2[self.id]()

    async def priority(self, new_val: Optional[float]=None):
        if new_val is None:
            config = await self.config()
            return config['priority']
        else:
            await self.api.config.wan.rules2[self.id].priority(new_val)
        

class WanDeviceCollection:
    def __init__(self, wans):
        self.wans = wans

    @property
    def all(self):
        return self.wans

    async def filter(self, **kwargs):
        results = []
        for wan in self.wans:
            if await wan.matches_filter(**kwargs):
                results.append(wan)
        return results

    async def filter_one(self, on_multiple='warn', **kwargs):
        results = await self.filter(**kwargs)
        if len(results) > 1:
            if on_multiple == 'raise':
                raise ValueError(f"Expected 1 or 0 results, got {len(results)}")
            elif on_multiple != 'ignore':
                warn("filter_one got more than one result. Returning the first result. Set on_multiple='ignore' to supress this warning, or on_multiple='raise' to raise an error.")
        elif len(results) == 0:
            return None
        return results[0]
 
    