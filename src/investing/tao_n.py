import bittensor
from typing import Dict
import asyncio
from tabulate import tabulate
from colorama import Fore, Style

from bittensor import AsyncSubtensor
from src.investing.investment_manager import InvestmentManager
from src.utils.colors import color_diff, color_value


class TaoN:
    def __init__(
        self,
        wallet: bittensor.wallet,
        subtensor: AsyncSubtensor,
        N: int = 16
    ):
        self.wallet = wallet
        self.subtensor = subtensor
        self.manager = InvestmentManager(wallet, subtensor)
        self.N = N

    async def get_top_N_weights(self, N: int = None) -> Dict[int, float]:
        if N is None:
            N = self.N

        subnets = await self.subtensor.get_all_subnets()
        if not subnets:
            return {}

        print(
            f"\n{Fore.GREEN}Explanation:{Style.RESET_ALL} "
            f"We compute market cap = price (TAO) * alpha_out (TAO). "
            f"Then we sort by descending market cap and pick top {N}. "
            f"Weight = (market cap / sum_of_topN_marketcaps).\n"
        )

        info_list = []
        for d in subnets:
            mcap = float(d.price.tao) * float(d.alpha_out.tao)
            info_list.append((d.netuid, float(d.price.tao), float(d.alpha_out.tao), mcap))

        info_list.sort(key=lambda x: x[3], reverse=True)
        top_n = info_list[:N]

        total_mcap = sum(x[3] for x in top_n)
        if total_mcap <= 0:
            return {}

        table_rows = []
        weights = {}
        for (netuid, price_val, alpha_out_val, mcap) in top_n:
            weight = mcap / total_mcap
            weights[netuid] = weight
            table_rows.append([
                netuid,
                f"{price_val:.9f}",
                f"{alpha_out_val:.9f}",
                f"{mcap:.9f}",
                f"{weight:.6f}"
            ])

        headers = ["NetUID", "Price (TAO)", "Alpha Out (TAO)", "Market Cap", "Weight"]
        print(tabulate(table_rows, headers=headers, tablefmt="fancy_grid"))

        print(f"\nFinal Weights Dict (top {N}): {weights}\n")
        input("Press Enter to proceed or Ctrl+C to cancel and inspect weights... ")

        return weights

    async def dca_TaoN(
        self,
        total_stake: float,
        increment: float,
        N: int = None
    ) -> Dict[int, bittensor.Balance]:
        if N is None:
            N = self.N

        stake_info: Dict[int, bittensor.Balance] = {}
        current_spent = 0.0
        iterations = 0

        weights = await self.get_top_N_weights(N)
        if not weights:
            print("No subnets or zero total market cap. Aborting.")
            return {}

        weighted_subnets = list(weights.items())

        while current_spent < total_stake:
            iterations += 1
            table_rows = []
            header = f"TaoN DCA Iteration #{iterations} (Spent: {current_spent:.9f}/{total_stake:.9f})"
            print(f"{Fore.YELLOW}{header}{Style.RESET_ALL}")

            tasks = []
            for netuid, w in weighted_subnets:
                if current_spent >= total_stake:
                    break

                stake_amount = increment * w
                if (current_spent + stake_amount) > total_stake:
                    stake_amount = total_stake - current_spent
                if stake_amount <= 0:
                    continue

                old_stake = stake_info.get(netuid, bittensor.Balance.from_tao(0))
                print(f"Staking {stake_amount:.9f} TAO on netuid={netuid} (weight={w:.6f}).")
                tasks.append(asyncio.create_task(
                    self._stake_and_fetch(netuid, stake_amount, old_stake)
                ))
                current_spent += stake_amount

            results = await asyncio.gather(*tasks)

            for row in results:
                netuid, old_stake, new_stake, alpha_diff, price = row
                stake_info[netuid] = new_stake
                table_rows.append([
                    netuid,
                    f"{float(old_stake.tao):.9f}",
                    color_value(float(new_stake.tao), decimals=9),
                    color_diff(alpha_diff),
                    f"{float(price.tao):.9f}",
                    "Staked"
                ])

            if table_rows:
                headers = ["NetUID", "Old Alpha", "New Alpha", "Alpha Diff", "Price", "Action"]
                print(tabulate(table_rows, headers=headers, tablefmt="fancy_grid"))

            tao_balance = await self.manager.helper.get_balance(
                address=self.wallet.coldkeypub.ss58_address
            )
            print(
                f"Wallet TAO Balance after iteration #{iterations}: "
                f"{color_value(float(tao_balance.tao), decimals=9)}\n"
            )

            await self.subtensor.wait_for_block()

        return stake_info

    async def _stake_and_fetch(
        self,
        netuid: int,
        amount: float,
        old_stake: bittensor.Balance
    ):
        subnet_info = await self.subtensor.subnet(netuid)
        await self.manager.staker.buy_alpha(netuid=netuid, tao_amount=amount)
        new_stake = await self.manager.staker.get_alpha_balance(netuid)
        alpha_diff = float(new_stake.tao) - float(old_stake.tao)
        return netuid, old_stake, new_stake, alpha_diff, subnet_info.price
