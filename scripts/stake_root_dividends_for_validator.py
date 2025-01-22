#!/usr/bin/env python3

import argparse
import asyncio
import bittensor
from dotenv import load_dotenv
from tabulate import tabulate

from utils.colors import color_diff, color_value
from utils.get_my_wallet import get_my_wallet
from classes.subnet_staker import SubnetStaker
from classes.dtao_helper import DTAOHelper

load_dotenv()


async def main(validator_hotkey:str):

    subtensor = await bittensor.async_subtensor(network='test')
    my_wallet = get_my_wallet()

    staker = SubnetStaker(wallet=my_wallet, subtensor=subtensor)
    helper = DTAOHelper(subtensor=subtensor)

    subnets_to_stake = [1, 277, 18, 5]
    subnets_percentages = [0.25, 0.25, 0.25, 0.25]

    old_stake = await helper.get_stake(
        netuid=0,
        coldkey_ss58=my_wallet.coldkeypub.ss58_address,
        hotkey_ss58=validator_hotkey
    )

    old_balance = await helper.get_balance(my_wallet.coldkeypub.ss58_address)
    print(f"Starting TAO balance: {color_value(float(old_balance.tao))}\n")

    old_alpha_balances = {}
    for netuid in subnets_to_stake:
        old_alpha_balances[netuid] = await staker.get_alpha_balance(netuid)

    print("Initial Alpha balances on each subnet:")
    table_rows = []
    for netuid in subnets_to_stake:
        table_rows.append([
            netuid,
            color_value(float(old_alpha_balances[netuid].tao))
        ])
    print(tabulate(table_rows, headers=["NetUID", "Alpha"], tablefmt="fancy_grid"), "\n")

    while True:
        try:
            current_block = await subtensor.get_current_block()
            print(f"Current block: {current_block}. Waiting for next block...\n")
            await subtensor.wait_for_block(current_block + 1)

            new_stake = await helper.get_stake(
                netuid=0,
                coldkey_ss58=my_wallet.coldkeypub.ss58_address,
                hotkey_ss58=validator_hotkey
            )
            dividends = new_stake - old_stake
            if dividends > bittensor.Balance(0):
                print(f"Dividends detected: {color_value(float(dividends.tao))} TAO\n")

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
                            color_value(float(new_subnet_alpha.tao)),
                            color_diff(alpha_diff),
                            "Staked"
                        ])

                if stake_rows:
                    headers = ["NetUID", "Old Alpha", "New Alpha", "Alpha Diff", "Action"]
                    print(tabulate(stake_rows, headers=headers, tablefmt="fancy_grid"))

                old_balance = await helper.get_balance(my_wallet.coldkeypub.ss58_address)
                print(f"\nBalance after staking dividends: {color_value(float(old_balance.tao))}\n")

            else:
                print("No new dividends this block.\n")

        except KeyboardInterrupt:
            print("Exiting script.")
            break
        except Exception as e:
            print(f"Error in loop: {e}")
            await asyncio.sleep(5)

    print("\nFinal Alpha balances on each subnet:")
    final_table_rows = []
    for netuid in subnets_to_stake:
        final_alpha = await staker.get_alpha_balance(netuid)
        diff = float(final_alpha.tao) - float(old_alpha_balances[netuid].tao)
        final_table_rows.append([
            netuid,
            color_value(float(old_alpha_balances[netuid].tao)),
            color_value(float(final_alpha.tao)),
            color_diff(diff)
        ])
    print(tabulate(final_table_rows, headers=["NetUID", "Old Alpha", "Final Alpha", "Diff"], tablefmt="fancy_grid"))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--validator_hotkey",
        type=str,
        required=True,
        help="SS58 address of the validator hotkey to sell dividends from"
    )
    args = parser.parse_args()
    validator_hotkey = args.validator_hotkey

    asyncio.run(main(validator_hotkey=validator_hotkey))
