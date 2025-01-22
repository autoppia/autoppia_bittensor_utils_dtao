# dtao_helper.py

import bittensor
from typing import Union, Optional
from bittensor import AsyncSubtensor


class DTAOHelper:
    def __init__(self, subtensor: AsyncSubtensor):
        self.subtensor = subtensor

    async def add_stake(
        self,
        wallet: bittensor.wallet,
        hotkey: str,
        netuid: int,
        tao_amount: Union[float, bittensor.Balance, int]
    ):
        if isinstance(tao_amount, (float, int)):
            tao_amount = bittensor.Balance.from_tao(tao_amount)

        return await self.subtensor.add_stake(
            wallet=wallet,
            hotkey=hotkey,
            netuid=netuid,
            tao_amount=tao_amount,
        )

    async def unstake(
        self,
        wallet: bittensor.wallet,
        hotkey: str,
        netuid: int,
        amount: Union[float, bittensor.Balance, int]
    ):
        if isinstance(amount, (float, int)):
            amount = bittensor.Balance.from_tao(amount)

        return await self.subtensor.unstake(
            wallet=wallet,
            hotkey=hotkey,
            netuid=netuid,
            amount=amount,
        )

    async def get_stake(
        self,
        hotkey_ss58: str,
        coldkey_ss58: str,
        netuid: int
    ) -> bittensor.Balance:
        return await self.subtensor.get_stake(
            hotkey_ss58=hotkey_ss58,
            coldkey_ss58=coldkey_ss58,
            netuid=netuid
        )

    async def all_subnets(
        self,
        block_number: Optional[int] = None
    ):
        return await self.subtensor.all_subnets(block_number)

    async def subnet(
        self,
        netuid: int,
        block_number: Optional[int] = None
    ):
        # Delegates to subtensor.subnet (which returns a DynamicInfo)
        return await self.subtensor.subnet(netuid, block_number)

    async def get_balance(
        self,
        address: str,
    ) -> bittensor.Balance:
        addresses_balances_dict = await self.subtensor.get_balance(address)
        return addresses_balances_dict[address]

    async def metagraph(
        self,
        netuid: int,
        block: Optional[int] = None
    ) -> bittensor.Metagraph:
        return await self.subtensor.metagraph(netuid, block)

    async def get_current_block(self) -> int:
        return await self.subtensor.get_current_block()

    async def wait_for_block(self, block: Optional[int] = None):
        return await self.subtensor.wait_for_block(block)
