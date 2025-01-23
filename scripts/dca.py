#!/usr/bin/env python3
import asyncio
import bittensor
import argparse
from src.shared.dtao_helper import DTAOHelper
from src.investing.investment_manager import InvestmentManager
from src.utils.get_my_wallet import get_my_wallet


def parse_arguments():
    parser = argparse.ArgumentParser(description="Perform DCA staking into multiple subnets.")
    parser.add_argument(
        "--netuids",
        type=int,
        nargs='*',  # Accepts an empty list if no arguments are provided
        default=[],  # Sets the default value to an empty list
        help="List of netuids to stake into (e.g., 1 277 18 5)."
    )
    parser.add_argument(
        "--increment",
        type=float,
        required=True,
        help="Increment amount for DCA staking."
    )
    parser.add_argument(
        "--total",
        type=float,
        required=True,
        help="Total amount to stake across the specified netuids."
    )
    return parser.parse_args()


async def main():
    args = parse_arguments()

    # Create the AsyncSubtensor instance
    subtensor = await bittensor.async_subtensor(network='test')

    my_wallet = get_my_wallet(unlock=True)

    # Instantiate helpers
    helper = DTAOHelper(subtensor)
    investor = InvestmentManager(wallet=my_wallet, subtensor=subtensor)

    # Check balance
    start_balance = await helper.get_balance(my_wallet.coldkeypub.ss58_address)
    print(f"Starting TAO balance: {start_balance}")

    # Perform DCA into the specified subnets
    final_stakes = await investor.dca(
        target_netuids=args.netuids,
        total_stake=args.total,
        increment=args.increment
    )

    print("=== Final Stake Info ===")
    for netuid, stake_balance in final_stakes.items():
        print(f"Netuid: {netuid}, Final Stake: {stake_balance}")

    # Check final balance
    end_balance = await helper.get_balance(my_wallet.coldkeypub.ss58_address)
    print(f"Ending TAO balance: {end_balance}")

if __name__ == "__main__":
    asyncio.run(main())
