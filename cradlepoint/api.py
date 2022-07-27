# SPDX-License-Identifier: Unlicense

import json
from typing import TYPE_CHECKING, Any, Awaitable, Union

import aiohttp

import os
import re
import logging

from internet_switcher.util.logging import LoggingMixin

if TYPE_CHECKING:
    from internet_switcher.config import Config

logger = logging.getLogger(__name__)


class CradlepointRouter(LoggingMixin):
    def __init__(self, config: 'Config'):
        self.session = aiohttp.ClientSession(
            base_url=f"http://{config.cradlepoint_server}",
            auth=aiohttp.BasicAuth(config.cradlepoint_username, config.cradlepoint_password)
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self):
        await self.close()

    def __getattr__(self, __name) -> 'Endpoint':
        num_attr = re.match(r"\_(\d+)", __name)
        if num_attr:
            __name = num_attr.group(1)
        return Endpoint(self, __name)

    async def get(self, path):
        return await self.request('GET', path)

    async def put(self, path, value):
        return await self.request('PUT', path, value=value)

    async def request(self, method: str, path, value=None):
        self.debug(f"Making {method.upper()} request to path {str(path)}")
        if value is not None:
            data = {'data': json.dumps(value)}
        else:
            data = None
        async with self.session.request(method=method, url='/api/' + str(path), data=data) as response:
            assert response.status == 200
            json_response = await response.json()
            assert json_response['success'] == True
            data = json_response['data']
            self.debug(f"Data: {json.dumps(data)[:100]}")
            return data

    async def is_valid(self) -> bool:
        """Check the config by making a request.

        This makes a request to /status/product_info and checks for an acceptable response.
        """
        try:
            await self.connect()
        except aiohttp.ClientConnectionError:
            logging.error("Could not connect to Cradlepoint", exc_info=True)
            return False
        except AssertionError:
            logging.error("Connected, but got invalid response", exc_info=True)
            return False

    async def connect(self):
        """Make a connection to the router
        
        The connection does not persist -- however, if a connection *cannot* be made, the function 
        will throw an error."""
        product_info = await self.status.product_info()
        product_name = product_info["product_name"]
        logger.info(f"Connected to: {product_name}")

    async def close(self):
        if not self.session.closed:
            await self.session.close()

    
class Endpoint:
    """Represents an endpoint on the Cradlepoint Router.

    The attributes represent subpaths of the endpoint. The endpoint can accessed as a coroutine that 
    both gets and sets the value (where applicable).

    For example, to get the primary WAN IP address:

    ```
    await api.status.wan.ipinfo.ip_address()
    ```

    To enable the modem's schedule, pass a value to the endpoint, e.g.:

    ```
    await api.config.lan.schedule.enabled(True)
    ```
    """
    def __init__(self, api: 'CradlepointRouter', path: str):
        self._api = api
        self._endpoint_path = path

    def __getattr__(self, __name: str) -> 'Endpoint':
        num_attr = re.match(r"\_(\d+)", __name)
        if num_attr:
            __name = num_attr.group(1)
        return Endpoint(self._api, os.path.join(self._endpoint_path, __name))

    def __getitem__(self, __name: Union[str, int]) -> 'Endpoint':
        return Endpoint(self._api, os.path.join(self._endpoint_path, str(__name)))

    def __call__(self, *args) -> Awaitable[Any]:
        return self.__acall__(*args)

    async def __acall__(self, *args) -> Any:
        if len(args) == 0:
            return await self._api.get(self)

        elif len(args) > 1:
            raise ValueError("More than one arg is not supported yet")

        else:
            return await self._api.put(self, args[0])

    def __repr__(self) -> str:
        return self._endpoint_path

    def __str__(self) -> str:
        return self._endpoint_path
