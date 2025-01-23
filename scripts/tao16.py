#!/usr/bin/env python3
import asyncio
import bittensor

from src.shared.dtao_helper import DTAOHelper
from src.investing.tao16 import Tao16
from src.utils.get_my_wallet import get_my_wallet
from src.utils.colors import color_value

from tabulate import tabulate
from colorama import Fore, Style


async def main():
    subtensor = await bittensor.async_subtensor(network='test')
    my_wallet = get_my_wallet(unlock=True)

    helper = DTAOHelper(subtensor)
    start_balance = await helper.get_balance(my_wallet.coldkeypub.ss58_address)
    print(f"{Fore.GREEN}Starting TAO balance:{Style.RESET_ALL} {color_value(float(start_balance.tao), decimals=9)}\n")

    tao16 = Tao16(wallet=my_wallet, subtensor=subtensor)

    total_amount_to_stake = 1.0
    dca_increment = 0.1
    print(f"Will stake a total of {total_amount_to_stake} TAO in increments of {dca_increment}.\n")

    final_stakes = await tao16.dca_Tao16(total_stake=total_amount_to_stake, increment=dca_increment)

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

    end_balance = await helper.get_balance(my_wallet.coldkeypub.ss58_address)
    print(f"{Fore.GREEN}Ending TAO balance:{Style.RESET_ALL} {color_value(float(end_balance.tao), decimals=9)}")

    balance_diff = float(end_balance.tao) - float(start_balance.tao)
    print(f"Balance difference (End - Start): {color_value(balance_diff, decimals=9)} TAO")


if __name__ == "__main__":
    asyncio.run(main())
