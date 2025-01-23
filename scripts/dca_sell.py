#!/usr/bin/env python3

import asyncio
import bittensor
import argparse

from src.shared.dtao_helper import DTAOHelper
from src.investing.investment_manager import InvestmentManager
from src.utils.get_my_wallet import get_my_wallet


async def main():
    parser = argparse.ArgumentParser(
        description="Perform percentage-based DCA selling for specific subnets."
    )
    parser.add_argument(
        "--netuids",
        type=int,
        nargs='+',
        required=True,
        help="List of netuids to operate on (e.g., 1 277 18 5)."
    )
    parser.add_argument(
        "--percentages",
        type=float,
        nargs='+',
        required=True,
        help="List of percentages corresponding to the netuids (e.g., 0.25 0.3 0.2 0.1)."
    )
    parser.add_argument(
        "--reduction",
        type=float,
        default=5.0,
        help="DCA increment for each iteration in alpha (default: 5)."
    )
    args = parser.parse_args()

    # Ensure the lengths of netuids and percentages match
    if len(args.netuids) != len(args.percentages):
        print("Error: The number of netuids must match the number of percentages.")
        return

    # Construct the subnets_and_percentages dictionary
    subnets_and_percentages = dict(zip(args.netuids, args.percentages))

    # Create the AsyncSubtensor instance
    subtensor = await bittensor.async_subtensor(network='test')

    my_wallet = get_my_wallet(unlock=True)

    # Instantiate helpers
    helper = DTAOHelper(subtensor)
    investor = InvestmentManager(wallet=my_wallet, subtensor=subtensor)

    # Check initial balance
    start_balance = await helper.get_balance(my_wallet.coldkeypub.ss58_address)
    print(f"Starting TAO balance: {start_balance}")

    # Perform the percentage-based DCA sell
    final_stakes = await investor.sell_dca(
        subnets_and_percentages=subnets_and_percentages,
        dca_alpha_reduction=args.reduction
    )

    print("=== Final Stake Info After Unstake ===")
    for netuid, stake_balance in final_stakes.items():
        print(f"Netuid: {netuid}, Remaining Stake: {stake_balance}")

    # Check final wallet balance
    end_balance = await helper.get_balance(my_wallet.coldkeypub.ss58_address)
    print(f"Ending TAO balance: {end_balance}")


if __name__ == "__main__":
    asyncio.run(main())
