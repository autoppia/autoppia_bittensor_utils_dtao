#!/usr/bin/env python3
import argparse
import asyncio
import bittensor

from src.shared.dtao_helper import DTAOHelper
from src.investing.tao_n import TaoN
from src.utils.get_my_wallet import get_my_wallet
from src.utils.colors import color_value

from tabulate import tabulate
from colorama import Fore, Style


def parse_args():
    parser = argparse.ArgumentParser(
        description="Invest in top N subnets using market cap weighting, similar to S&P 500 index."
    )
    parser.add_argument(
        "--total",
        type=float,
        default=1.0,
        help="Total TAO amount to invest (default: 1.0)"
    )
    parser.add_argument(
        "--days",
        type=float,
        default=1.0,
        help="Number of days to spread the DCA. (default: 1.0 day)"
    )
    parser.add_argument(
        "--network",
        type=str,
        default="test",
        choices=["test", "main"],
        help="Bittensor network to use (default: test)"
    )
    parser.add_argument(
        "--n",
        type=int,
        default=16,
        help="Number of top subnets to use (default: 16)"
    )
    return parser.parse_args()


async def main():
    args = parse_args()

    # Initialize async subtensor
    subtensor = await bittensor.async_subtensor(network=args.network).initialize()

    # Unlock or create your wallet
    my_wallet = get_my_wallet(unlock=True)

    # Check starting balance
    helper = DTAOHelper(subtensor)
    start_balance = await helper.get_balance(my_wallet.coldkeypub.ss58_address)
    print(
        f"{Fore.GREEN}Starting TAO balance:{Style.RESET_ALL} "
        f"{color_value(float(start_balance.tao), decimals=9)}\n"
    )

    # Create TaoN instance
    tao_n = TaoN(wallet=my_wallet, subtensor=subtensor, N=args.n)

    print(
        f"Will stake a total of {args.total} TAO over {args.days} days.\n"
        f"Targeting top {args.n} subnets on '{args.network}' network.\n"
    )

    # Execute the DCA process
    final_stakes = await tao_n.dca_TaoN(
        total_tao=args.total,
        days=args.days,
        N=args.n
    )

    # Show final results
    print(f"=== Final Tao{args.n} Alpha Distribution ===")
    table_rows = []
    total_staked = 0.0
    for netuid, alpha_balance in final_stakes.items():
        st_val = float(alpha_balance.tao)
        table_rows.append([netuid, color_value(st_val, decimals=9)])
        total_staked += st_val

    headers = ["NetUID", "Final Alpha"]
    print(tabulate(table_rows, headers=headers, tablefmt="fancy_grid"))

    print(f"\nTotal Staked: {color_value(total_staked, decimals=9)} TAO")

    # Check ending wallet balance
    end_balance = await helper.get_balance(my_wallet.coldkeypub.ss58_address)
    print(
        f"{Fore.GREEN}Ending TAO balance:{Style.RESET_ALL} "
        f"{color_value(float(end_balance.tao), decimals=9)}"
    )

    balance_diff = float(end_balance.tao) - float(start_balance.tao)
    print(f"Balance difference (End - Start): {color_value(balance_diff, decimals=9)} TAO")


if __name__ == "__main__":
    asyncio.run(main())
