import bittensor
from bittensor import AsyncSubtensor
from typing import Union


class SubnetStaker:
    def __init__(self, wallet: bittensor.wallet, subtensor: AsyncSubtensor):
        """
        SubnetStaker now holds a reference to the wallet (and subtensor)
        so we don't need to pass 'wallet' around to each method.
        """
        self.wallet = wallet
        self.subtensor = subtensor

    async def buy_alpha(
        self,
        netuid: int,
        tao_amount: float,
        hotkey: str = None
    ) -> bittensor.Balance:
        """
        Stakes (buys alpha) by staking `tao_amount` TAO to the subnet owner's hotkey
        or a specified hotkey.
        """
        subnet_info = await self.subtensor.subnet(netuid)
        if subnet_info is None:
            raise ValueError(f"Subnet {netuid} not found.")

        # Convert to bittensor.Balance if float or int
        if isinstance(tao_amount, (float, int)):
            tao_amount = bittensor.Balance.from_tao(tao_amount)

        if hotkey is None:
            hotkey = subnet_info.owner_hotkey

        # Perform the stake
        response = await self.subtensor.add_stake(
            wallet=self.wallet,
            netuid=netuid,
            hotkey=hotkey,
            tao_amount=tao_amount
        )

        # Fetch updated alpha balance (staked amount)
        new_alpha = await self.get_alpha_balance(netuid, hotkey)
        print(
            f"[buy_alpha] Staked {tao_amount} TAO into netuid={netuid}, "
            f"price={subnet_info.price}, new_alpha={new_alpha}, response={response}"
        )

        # Wait for the next block (optional)
        await self.subtensor.wait_for_block()
        return new_alpha

    async def sell_alpha(
        self,
        netuid: int,
        alpha_amount: float,
        hotkey: str = None
    ) -> bittensor.Balance:
        """
        Unstakes (sells alpha) by unstaking `alpha_amount` from the specified hotkey
        or the subnet owner's hotkey.
        """
        subnet_info = await self.subtensor.subnet(netuid)
        if subnet_info is None:
            raise ValueError(f"Subnet {netuid} not found.")

        if isinstance(alpha_amount, (float, int)):
            alpha_amount = bittensor.Balance.from_tao(alpha_amount)

        if hotkey is None:
            hotkey = subnet_info.owner_hotkey

        response = await self.subtensor.unstake(
            wallet=self.wallet,
            netuid=netuid,
            hotkey=hotkey,
            amount=alpha_amount,
        )

        # For verification, check how much alpha remains staked
        remaining_alpha = await self.get_alpha_balance(netuid, hotkey)
        print(
            f"[sell_alpha] Unstaked {alpha_amount} alpha from netuid={netuid}, "
            f"price={subnet_info.price}, remaining_alpha={remaining_alpha}, response={response}"
        )

        await self.subtensor.wait_for_block()
        return remaining_alpha

    async def get_alpha_balance(
        self,
        netuid: int,
        hotkey: str = None
    ) -> bittensor.Balance:
        """
        Returns how much alpha the wallet currently has staked on the subnet for a specific hotkey.
        """
        subnet_info = await self.subtensor.subnet(netuid)

        if subnet_info is None:
            return bittensor.Balance.from_tao(0)

        if hotkey is None:
            hotkey = subnet_info.owner_hotkey

        staked = await self.subtensor.get_stake(
            coldkey_ss58=self.wallet.coldkeypub.ss58_address,
            hotkey_ss58=hotkey,
            netuid=netuid
        )
        return staked

    async def alpha_to_tao_value(
        self,
        netuid: int,
        alpha_amount: Union[float, bittensor.Balance]
    ) -> bittensor.Balance:
        """
        Converts alpha_amount to how many TAO that alpha is worth, 
        using the DynamicInfo price from the chain (mocked if none).
        """
        subnet_info = await self.subtensor.subnet(netuid)
        if subnet_info is None:
            return bittensor.Balance.from_tao(0)

        if isinstance(alpha_amount, (float, int)):
            alpha_amount = bittensor.Balance.from_tao(alpha_amount)

        # Using alpha_to_tao from DynamicInfo (mock if none)
        return subnet_info.alpha_to_tao(alpha_amount)

    async def alpha_to_dollar_value(
        self,
        netuid: int,
        alpha_amount: Union[float, bittensor.Balance],
        tao_price_usd: float
    ) -> float:
        """
        Returns how many USD the given alpha_amount is worth, 
        given an external TAO price in USD (mock or real).
        """
        tao_balance = await self.alpha_to_tao_value(netuid, alpha_amount)
        return float(tao_balance) * tao_price_usd

    async def tao_to_alpha_value(
        self,
        netuid: int,
        tao_amount: Union[float, bittensor.Balance]
    ) -> bittensor.Balance:
        """
        Converts a TAO amount to how many alpha that is worth (mock).
        """
        subnet_info = await self.subtensor.subnet(netuid)
        if subnet_info is None:
            return bittensor.Balance.from_tao(0)

        if isinstance(tao_amount, (float, int)):
            tao_amount = bittensor.Balance.from_tao(tao_amount)

        # Using tao_to_alpha from DynamicInfo (mock if none)
        return subnet_info.tao_to_alpha(tao_amount)

    async def tao_to_dollar_value(
        self,
        tao_amount: Union[float, bittensor.Balance],
        tao_price_usd: float
    ) -> float:
        """
        Returns how many USD the given TAO amount is worth, 
        given an external TAO price in USD (mock or real).
        """
        if isinstance(tao_amount, (float, int)):
            tao_amount = bittensor.Balance.from_tao(tao_amount)
        return float(tao_amount) * tao_price_usd
