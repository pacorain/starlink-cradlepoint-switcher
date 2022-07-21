# SPDX-License-Identifier: Unlicense

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from cradlepoint.api import CradlepointRouter


class WanRuleCollection:
    """Methods for querying and manipulating connection rules on the router.
    
    Most methods return one or a collection of WanRule instances.
    """
    def __init__(self, api: CradlepointRouter):
        self.api = api

    async def all(self): 
        wans = await self.api.get("config/wan/rules2")
        for wan in wans:
            yield WanRule(self.api, wan['_id_'], config=wan)


class WanRule:
    def __init__(self, api: CradlepointRouter, id: str, config: Optional[dict]=None):
        self.api = api
        self.id = id
        self.config = config

    
    