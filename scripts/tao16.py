#!/usr/bin/env python3
import asyncio
import argparse
import bittensor
from src.shared.dtao_helper import DTAOHelper
from src.investing.tao16 import Tao16
from src.utils.get_my_wallet import get_my_wallet
from src.utils.colors import color_value
from tabulate import tabulate
from colorama import Fore, Style


def parse_args():
    parser = argparse.ArgumentParser(
        description="Invest in top 16 subnets using market cap weighting, similar to S&P 500 index."
    )
    parser.add_argument(
        "--total",
        type=float,
        default=1.0,
        help="Total TAO amount to invest (default: 1.0)"
    )
    parser.add_argument(
        "--increment",
        type=float,
        default=0.1,
        help="DCA increment size (default: 0.1)"
    )
    parser.add_argument(
        "--network",
        type=str,
        default="test",
        choices=["test", "main"],
        help="Bittensor network to use (default: test)"
    )
    return parser.parse_args()


async def main():
    args = parse_args()

    # Initialize Bittensor components
    subtensor = await bittensor.async_subtensor(network=args.network)
    my_wallet = get_my_wallet(unlock=True)
    helper = DTAOHelper(subtensor)

    # Get starting balance
    start_balance = await helper.get_balance(my_wallet.coldkeypub.ss58_address)
    print(f"{Fore.GREEN}Starting TAO balance:{Style.RESET_ALL} {color_value(float(start_balance.tao), decimals=9)}\n")

    # Initialize TAO16 strategy
    tao16 = Tao16(wallet=my_wallet, subtensor=subtensor)
    print(f"Will stake {args.total} TAO in increments of {args.increment} on {args.network}net.\n")

    # Execute investment strategy
    final_stakes = await tao16.dca_Tao16(total_stake=args.total, increment=args.increment)

    # Display results
    print("=== Final Tao16 Alpha Distribution ===")
    table_rows = []
    total_staked = 0.0

    for netuid, alpha_balance in final_stakes.items():
        st_val = float(alpha_balance.tao)
        table_rows.append([netuid, color_value(st_val, decimals=9)])
        total_staked += st_val

    headers = ["NetUID", "Final Alpha"]
    print(tabulate(table_rows, headers=headers, tablefmt="fancy_grid"))
    print(f"\nTotal Staked: {color_value(total_staked, decimals=9)} TAO")

    # Display final balances
    end_balance = await helper.get_balance(my_wallet.coldkeypub.ss58_address)
    print(f"{Fore.GREEN}Ending TAO balance:{Style.RESET_ALL} {color_value(float(end_balance.tao), decimals=9)}")
    balance_diff = float(end_balance.tao) - float(start_balance.tao)
    print(f"Balance difference: {color_value(balance_diff, decimals=9)} TAO")

if __name__ == "__main__":
    asyncio.run(main())
