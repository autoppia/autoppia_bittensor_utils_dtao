import asyncio
from typing import Dict, List
import bittensor
from bittensor import AsyncSubtensor
from tabulate import tabulate
from colorama import Fore, Style
from src.shared.subnet_staker import SubnetStaker
from src.shared.dtao_helper import DTAOHelper
from src.utils.colors import color_diff, color_value


class InvestmentManager:
    def __init__(self, wallet: bittensor.wallet, subtensor: AsyncSubtensor):
        self.wallet = wallet
        self.subtensor = subtensor
        self.staker = SubnetStaker(wallet=self.wallet, subtensor=self.subtensor)
        self.helper = DTAOHelper(subtensor=subtensor)

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
                    f"{float(old_stake.tao):.9f}",
                    color_value(float(new_stake.tao), decimals=9),
                    color_diff(alpha_diff),
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
                f"{color_value(float(tao_balance.tao), decimals=9)}\n"
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
        await self.staker.buy_alpha(netuid=netuid, tao_amount=increment)
        new_stake = await self.staker.get_alpha_balance(netuid)
        alpha_diff = float(new_stake.tao) - float(old_stake.tao)
        return netuid, old_stake, new_stake, alpha_diff, subnet_info.price

    async def sell_dca(
        self,
        subnets_and_percentages: Dict[int, float],
        dca_sell_percentage: float
    ) -> Dict[int, bittensor.Balance]:
        """
        Parallelized DCA (sell/unstake) using a per-iteration sell percentage.

        - subnets_and_percentages: netuid -> portion of current alpha to sell in total.
          (e.g. 0.5 means sell 50% of your current alpha on that netuid)
        - dca_sell_percentage: portion to sell each iteration from what remains *to be sold*.
          (e.g. 0.2 means each iteration sells 20% of the portion we still need to sell.)
        """
        # Optionally, if user passes e.g. `--sell_percentage 100` to mean 1.0 fraction, adjust here:
        if dca_sell_percentage > 1.0:
            dca_sell_percentage /= 100.0

        # Current stake for each netuid
        alpha_per_subnet = {}
        for netuid in subnets_and_percentages:
            alpha_per_subnet[netuid] = await self.staker.get_alpha_balance(netuid)

        print("Subnet Stakes (before selling):")
        for netuid, alpha in alpha_per_subnet.items():
            print(f"  NetUID {netuid}: {alpha}")

        # How much alpha each netuid wants to keep after all sells
        # (i.e. total alpha minus the portion to sell)
        target_alpha_dict = {}
        for netuid, current_alpha in alpha_per_subnet.items():
            sell_fraction = subnets_and_percentages[netuid]
            alpha_to_keep = current_alpha - current_alpha * sell_fraction
            target_alpha_dict[netuid] = alpha_to_keep

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
                # If we're already at or below the target, no action needed
                if current_alpha <= target_alpha:
                    continue

                # How much alpha is still left to sell
                alpha_left_to_sell = current_alpha - target_alpha
                # This iteration we sell dca_sell_percentage of that leftover portion
                iteration_sell_amount = alpha_left_to_sell * dca_sell_percentage

                # If this iteration_sell_amount is tiny or puts us below the target, clamp
                if (current_alpha - iteration_sell_amount) < target_alpha:
                    iteration_sell_amount = alpha_left_to_sell

                # If there's anything > 0 to sell, queue the task
                if iteration_sell_amount > 0:
                    old_stake = current_alpha
                    tasks.append(
                        asyncio.create_task(
                            self._unstake_and_fetch(netuid, iteration_sell_amount, old_stake)
                        )
                    )

            # If no tasks, we are done
            if not tasks:
                print("All subnets have reached or are below their target alpha. Stopping.\n")
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
                    color_value(float(new_stake.tao), decimals=9),
                    color_diff(alpha_diff),
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
                f"{color_value(float(tao_balance.tao), decimals=9)}\n"
            )

            # Wait for the next block before the next iteration
            await self.staker.subtensor.wait_for_block()

        return stake_info

    async def _unstake_and_fetch(
        self,
        netuid: int,
        sell_amount: float,
        old_stake: bittensor.Balance
    ):
        """
        Sell alpha_amount (in TAO terms).
        """
        subnet_info = await self.staker.subtensor.subnet(netuid)
        await self.staker.sell_alpha(netuid=netuid, alpha_amount=sell_amount)
        new_stake = await self.staker.get_alpha_balance(netuid)
        alpha_diff = float(new_stake.tao) - float(old_stake.tao)
        return netuid, old_stake, new_stake, alpha_diff, subnet_info.price
