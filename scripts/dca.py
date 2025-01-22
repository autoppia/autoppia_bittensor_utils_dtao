#!/usr/bin/env python3
import asyncio
import bittensor
from dotenv import load_dotenv
from classes.dtao_helper import DTAOHelper
from classes.investment_manager import InvestmentManager
from classes.subnet_staker import SubnetStaker
from utils.get_my_wallet import get_my_wallet


load_dotenv()


async def main():

    # Create the AsyncSubtensor instance
    subtensor = await bittensor.async_subtensor(network='test')

    my_wallet = get_my_wallet()

    # Instantiate helpers
    helper = DTAOHelper(subtensor)
    investor = InvestmentManager(wallet=my_wallet, subtensor=subtensor)
    staker = SubnetStaker(wallet=my_wallet, subtensor=subtensor)

    # Check balance
    start_balance = await helper.get_balance(my_wallet.coldkeypub.ss58_address)
    print(f"Starting TAO balance: {start_balance}")

    # Example 3: Parallel DCA into multiple subnets
    subnets_to_stake = [1,277,18,5]
    total_amount_to_stake = 1
    dca_increment = 0.1
    final_stakes = await investor.dca(
        target_netuids=subnets_to_stake,
        total_stake=total_amount_to_stake,
        increment=dca_increment
    )
    print("=== Final Stake Info ===")
    for netuid, stake_balance in final_stakes.items():
        print(f"Netuid: {netuid}, Final Stake: {stake_balance}")

    # Check final balance
    end_balance = await helper.get_balance(my_wallet.coldkeypub.ss58_address)
    print(f"Ending TAO balance: {end_balance}")


if __name__ == "__main__":
    asyncio.run(main())
