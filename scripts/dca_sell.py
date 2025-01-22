#!/usr/bin/env python3

import asyncio
import bittensor

from classes.dtao_helper import DTAOHelper
from classes.investment_manager import InvestmentManager
from classes.subnet_staker import SubnetStaker
from utils.get_my_wallet import get_my_wallet


async def main():
    # Create the AsyncSubtensor instance
    subtensor = await bittensor.async_subtensor(network='test')

    my_wallet = get_my_wallet()

    # Instantiate helpers
    helper = DTAOHelper(subtensor)
    investor = InvestmentManager(wallet=my_wallet, subtensor=subtensor)
    staker = SubnetStaker(wallet=my_wallet, subtensor=subtensor)

    # Check initial balance
    start_balance = await helper.get_balance(my_wallet.coldkeypub.ss58_address)
    print(f"Starting TAO balance: {start_balance}")

    # Example: subnets and percentages of staked alpha we want to sell
    # (i.e. 25% on netuid=1, 30% on netuid=277, etc.)
    subnets_and_percentages = {
        1: 0.25,
        277: 0.30,
        18: 0.10,
        5: 0.75,
    }

    # DCA increment for each iteration (in alpha, not TAO)
    dca_alpha_reduction = 0.01

    # Perform the percentage-based DCA sell
    final_stakes = await investor.sell_dca(
        subnets_and_percentages=subnets_and_percentages,
        dca_alpha_reduction=dca_alpha_reduction
    )

    print("=== Final Stake Info After Unstake ===")
    for netuid, stake_balance in final_stakes.items():
        print(f"Netuid: {netuid}, Remaining Stake: {stake_balance}")

    # Check final wallet balance
    end_balance = await helper.get_balance(my_wallet.coldkeypub.ss58_address)
    print(f"Ending TAO balance: {end_balance}")


if __name__ == "__main__":
    asyncio.run(main())
