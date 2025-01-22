#!/usr/bin/env python3
import asyncio
import bittensor
from dotenv import load_dotenv
from tabulate import tabulate
from colorama import Fore, Style

from utils.get_my_wallet import get_my_wallet
from classes.subnet_staker import SubnetStaker
from classes.dtao_helper import DTAOHelper


load_dotenv()


def _color_diff(value: float) -> str:
    diff_str = f"{value:+.9f}"
    if value > 0:
        return f"{Fore.GREEN}{diff_str}{Style.RESET_ALL}"
    elif value < 0:
        return f"{Fore.RED}{diff_str}{Style.RESET_ALL}"
    else:
        return diff_str


def _color_value(value: float, decimals: int = 9) -> str:
    value_str = f"{value:.{decimals}f}"
    return f"{Fore.CYAN}{value_str}{Style.RESET_ALL}"


async def main():

    # Create the AsyncSubtensor instance
    subtensor = await bittensor.async_subtensor(network='test')

    my_wallet = get_my_wallet()

    staker = SubnetStaker(wallet=my_wallet, subtensor=subtensor)
    helper = DTAOHelper(subtensor=subtensor)

    # Subnets and respective percentages (must sum to 1.0)
    subnets_to_stake = [1, 277, 18, 5]
    subnets_percentages = [0.25, 0.25, 0.25, 0.25]

    old_balance = await helper.get_balance(my_wallet.coldkeypub.ss58_address)
    print(f"Starting TAO balance: {_color_value(float(old_balance.tao))}\n")

    # Track initial alpha balances
    old_alpha_balances = {}
    for netuid in subnets_to_stake:
        old_alpha_balances[netuid] = await staker.get_alpha_balance(netuid)

    print("Initial Alpha balances on each subnet:")
    table_rows = []
    for netuid in subnets_to_stake:
        table_rows.append([
            netuid,
            _color_value(float(old_alpha_balances[netuid].tao))
        ])
    print(tabulate(table_rows, headers=["NetUID", "Alpha"], tablefmt="fancy_grid"), "\n")

    while True:
        try:
            current_block = await subtensor.get_current_block()
            print(f"Current block: {current_block}. Waiting for next block...\n")
            await subtensor.wait_for_block(current_block + 1)

            print(await subtensor.get_stake_for_coldkey(coldkey_ss58=my_wallet.coldkeypub.ss58_address))
            input()
            new_balance = await helper.get_balance(my_wallet.coldkeypub.ss58_address)
            dividends = new_balance - old_balance

            if dividends > bittensor.Balance(0) and dividends < bittensor.Balance(0.5):
                print(f"Dividends detected: {_color_value(float(dividends.tao))} TAO\n")

                # Keep track of staking changes in a table
                stake_rows = []
                for netuid, pct in zip(subnets_to_stake, subnets_percentages):
                    stake_amount_tao = dividends.tao * pct
                    if stake_amount_tao > 0:
                        old_subnet_alpha = await staker.get_alpha_balance(netuid)
                        await staker.buy_alpha(netuid=netuid, tao_amount=stake_amount_tao)
                        new_subnet_alpha = await staker.get_alpha_balance(netuid)
                        alpha_diff = float(new_subnet_alpha.tao) - float(old_subnet_alpha.tao)
                        stake_rows.append([
                            netuid,
                            f"{float(old_subnet_alpha.tao):.9f}",
                            _color_value(float(new_subnet_alpha.tao)),
                            _color_diff(alpha_diff),
                            "Staked"
                        ])

                if stake_rows:
                    headers = ["NetUID", "Old Alpha", "New Alpha", "Alpha Diff", "Action"]
                    print(tabulate(stake_rows, headers=headers, tablefmt="fancy_grid"))

                old_balance = await helper.get_balance(my_wallet.coldkeypub.ss58_address)
                print(f"\nBalance after staking dividends: {_color_value(float(old_balance.tao))}\n")

            else:
                print("No new dividends this block.\n")

        except KeyboardInterrupt:
            print("Exiting script.")
            break
        except Exception as e:
            print(f"Error in loop: {e}")
            await asyncio.sleep(5)

    # Final alpha balances
    print("\nFinal Alpha balances on each subnet:")
    final_table_rows = []
    for netuid in subnets_to_stake:
        final_alpha = await staker.get_alpha_balance(netuid)
        diff = float(final_alpha.tao) - float(old_alpha_balances[netuid].tao)
        final_table_rows.append([
            netuid,
            _color_value(float(old_alpha_balances[netuid].tao)),
            _color_value(float(final_alpha.tao)),
            _color_diff(diff)
        ])
    print(tabulate(final_table_rows, headers=["NetUID", "Old Alpha", "Final Alpha", "Diff"], tablefmt="fancy_grid"))

if __name__ == "__main__":
    asyncio.run(main())
