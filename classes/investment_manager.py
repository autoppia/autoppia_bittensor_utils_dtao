import asyncio
from typing import Dict, List
import bittensor
from bittensor import AsyncSubtensor
from tabulate import tabulate
from colorama import Fore, Style
from .subnet_staker import SubnetStaker  # Adjust the import path if needed
from classes.dtao_helper import DTAOHelper


class InvestmentManager:
    def __init__(self, wallet: bittensor.wallet, subtensor: AsyncSubtensor):
        self.wallet = wallet
        self.subtensor = subtensor
        self.staker = SubnetStaker(wallet=self.wallet, subtensor=self.subtensor)
        self.helper = DTAOHelper(subtensor=subtensor)

    def _color_diff(self, value: float) -> str:
        """
        Displays difference with color and sign.
        e.g. +0.000001234 or -0.000000567
        """
        # Format with e.g. 9 decimals.
        diff_str = f"{value:+.9f}"
        if value > 0:
            return f"{Fore.GREEN}{diff_str}{Style.RESET_ALL}"
        elif value < 0:
            return f"{Fore.RED}{diff_str}{Style.RESET_ALL}"
        else:
            return f"{diff_str}"

    def _color_value(self, value: float, decimals=9) -> str:
        """
        Displays a float with a certain number of decimals, in cyan.
        """
        value_str = f"{value:.{decimals}f}"
        return f"{Fore.CYAN}{value_str}{Style.RESET_ALL}"

    async def dca(
        self,
        target_netuids: List[int],
        total_stake: float,
        increment: float,
    ) -> Dict[int, bittensor.Balance]:
        """
        Parallelized DCA (buy/stake).
        """
        stake_info: Dict[int, bittensor.Balance] = {}
        current_spent = 0.0
        iterations = 0

        while current_spent < total_stake:
            iterations += 1
            table_rows = []
            iteration_header = f"DCA Iteration #{iterations} (Spending so far: {current_spent:.9f}/{total_stake:.9f})"
            print(f"{Fore.YELLOW}{iteration_header}{Style.RESET_ALL}")

            tasks = []
            for netuid in target_netuids:
                if current_spent >= total_stake:
                    break
                old_stake = stake_info.get(netuid, bittensor.Balance.from_tao(0))
                tasks.append(asyncio.create_task(
                    self._stake_and_fetch(netuid, increment, old_stake)
                ))
                current_spent += increment

            results = await asyncio.gather(*tasks)

            for row in results:
                # row = (netuid, old_stake, new_stake, alpha_diff, price)
                netuid, old_stake, new_stake, alpha_diff, price = row
                stake_info[netuid] = new_stake

                table_rows.append([
                    netuid,
                    # Old alpha with 9 decimals
                    f"{float(old_stake.tao):.9f}",
                    # New alpha in cyan, 9 decimals
                    self._color_value(float(new_stake.tao), decimals=9),
                    # alpha diff with color
                    self._color_diff(alpha_diff),
                    # price with 9 decimals
                    f"{float(price):.9f}",
                    "Staked"
                ])

            if table_rows:
                headers = [
                    "NetUID",
                    "Old Alpha",
                    "New Alpha",
                    "Alpha Diff",
                    "Price",
                    "Action"
                ]
                print(tabulate(table_rows, headers=headers, tablefmt="fancy_grid"))

            tao_balance = await self.helper.get_balance(address=self.wallet.coldkeypub.ss58_address)
            print(
                f"Wallet TAO Balance after iteration #{iterations}: "
                f"{self._color_value(float(tao_balance.tao), decimals=9)}\n"
            )

            await self.staker.subtensor.wait_for_block()

        return stake_info

    async def _stake_and_fetch(
        self,
        netuid: int,
        increment: float,
        old_stake: bittensor.Balance
    ):
        subnet_info = await self.staker.subtensor.subnet(netuid)
        # Buy alpha with TAO amount = increment
        await self.staker.buy_alpha(netuid=netuid, tao_amount=increment)
        new_stake = await self.staker.get_alpha_balance(netuid)
        alpha_diff = float(new_stake.tao) - float(old_stake.tao)
        return netuid, old_stake, new_stake, alpha_diff, subnet_info.price

    async def sell_dca(
        self,
        subnets_and_percentages: Dict[int, float],
        dca_alpha_reduction: float
    ) -> Dict[int, bittensor.Balance]:
        """
        Parallelized DCA (sell/unstake).
        - subnets_and_percentages: netuid -> proportion
        - dca_alpha_reduction: how much alpha to sell each iteration (in TAO)
        """
        alpha_per_subnet = {}
        for netuid in subnets_and_percentages:
            alpha_per_subnet[netuid] = await self.staker.get_alpha_balance(netuid)

        total_alpha = sum(alpha_per_subnet.values())
        sum_of_percentages = sum(subnets_and_percentages.values())

        # Target alpha dict
        target_alpha_dict = {
            netuid: total_alpha * (pct / sum_of_percentages)
            for netuid, pct in subnets_and_percentages.items()
        }

        stake_info: Dict[int, bittensor.Balance] = {}
        iteration = 0

        while True:
            iteration += 1
            table_rows = []
            iteration_header = f"Sell DCA Iteration #{iteration}"
            print(f"{Fore.MAGENTA}{iteration_header}{Style.RESET_ALL}")

            # Update alpha balances
            for netuid in subnets_and_percentages:
                alpha_per_subnet[netuid] = await self.staker.get_alpha_balance(netuid)

            tasks = []
            for netuid, current_alpha in alpha_per_subnet.items():
                target_alpha = target_alpha_dict[netuid]
                reduction_balance = bittensor.Balance.from_tao(dca_alpha_reduction)

                # If current alpha is above target alpha + reduction_balance, unstake
                if current_alpha > (target_alpha + reduction_balance):
                    old_stake = current_alpha
                    tasks.append(asyncio.create_task(
                        self._unstake_and_fetch(netuid, dca_alpha_reduction, old_stake)
                    ))

            if not tasks:
                print("All subnets are at or below their target alpha distribution. Stopping.\n")
                break

            results = await asyncio.gather(*tasks)

            for row in results:
                # row = (netuid, old_stake, new_stake, alpha_diff, price)
                netuid, old_stake, new_stake, alpha_diff, price = row
                stake_info[netuid] = new_stake
                alpha_per_subnet[netuid] = new_stake

                table_rows.append([
                    netuid,
                    f"{float(old_stake.tao):.9f}",
                    self._color_value(float(new_stake.tao), decimals=9),
                    self._color_diff(alpha_diff),
                    f"{float(price):.9f}",
                    "Unstaked"
                ])

            if table_rows:
                headers = [
                    "NetUID",
                    "Old Alpha",
                    "New Alpha",
                    "Alpha Diff",
                    "Price",
                    "Action"
                ]
                print(tabulate(table_rows, headers=headers, tablefmt="fancy_grid"))

            tao_balance = await self.helper.get_balance(address=self.wallet.coldkeypub.ss58_address)
            print(
                f"Wallet TAO Balance after iteration #{iteration}: "
                f"{self._color_value(float(tao_balance.tao), decimals=9)}\n"
            )

            await self.staker.subtensor.wait_for_block()

        return stake_info

    async def _unstake_and_fetch(
        self,
        netuid: int,
        dca_alpha_reduction: float,
        old_stake: bittensor.Balance
    ):
        subnet_info = await self.staker.subtensor.subnet(netuid)
        # Sell alpha amount (in TAO terms)
        await self.staker.sell_alpha(netuid=netuid, alpha_amount=dca_alpha_reduction)
        new_stake = await self.staker.get_alpha_balance(netuid)
        alpha_diff = float(new_stake.tao) - float(old_stake.tao)
        return netuid, old_stake, new_stake, alpha_diff, subnet_info.price
