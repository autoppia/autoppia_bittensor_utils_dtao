#!/usr/bin/env python3
import bittensor
from bittensor.core.chain_data import DynamicInfo


async def get_subnet_owner_hotkey(netuid:int):
    subtensor = await bittensor.async_subtensor(network='test')
    data:DynamicInfo = await subtensor.subnet(netuid=netuid)
    hotkey = data.owner_hotkey
    print(hotkey)
    return hotkey
