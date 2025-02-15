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
        nargs='*',
        default=[],
        help="List of netuids to operate on (e.g., 1 277 18 5)."
    )
    parser.add_argument(
        "--percentages",
        type=float,
        nargs='*',
        default=[],
        help="List of percentages corresponding to the netuids (e.g., 0.25 0.3 0.2 0.1)."
    )
    parser.add_argument(
        "--sell_percentage",
        type=float,
        default=0.05,
        help="Percentage of total stake to sell in each iteration (0 < sell_percentage < 1)."
    )
    args = parser.parse_args()

    if len(args.netuids) != len(args.percentages):
        print("Error: The number of netuids must match the number of percentages.")
        return

    subnets_and_percentages = dict(zip(args.netuids, args.percentages))

    subtensor = await bittensor.async_subtensor().initialize()
    my_wallet = get_my_wallet(unlock=True)

    helper = DTAOHelper(subtensor)
    investor = InvestmentManager(wallet=my_wallet, subtensor=subtensor)

    start_balance = await helper.get_balance(my_wallet.coldkeypub.ss58_address)
    print(f"Starting TAO balance: {start_balance}")

    final_stakes = await investor.sell_dca(
        subnets_and_percentages=subnets_and_percentages,
        dca_sell_percentage=args.sell_percentage
    )

    print("=== Final Stake Info After Unstake ===")
    for netuid, stake_balance in final_stakes.items():
        print(f"Netuid: {netuid}, Remaining Stake: {stake_balance}")

    end_balance = await helper.get_balance(my_wallet.coldkeypub.ss58_address)
    print(f"Ending TAO balance: {end_balance}")

if __name__ == "__main__":
    asyncio.run(main())
