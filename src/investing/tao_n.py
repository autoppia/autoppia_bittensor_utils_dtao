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
        N: int = 16,
        block_time_seconds: float = 12.0,
        minimum_stake: float = 0.0001  # Example guard to prevent micropayment errors
    ):
        """
        :param N: pick top N subnets by (price * alpha_out).
        :param block_time_seconds: approximate seconds between blocks (Bittensor ~12s).
        :param minimum_stake: skip subnets if daily stake portion is below this threshold.
        """
        self.wallet = wallet
        self.subtensor = subtensor
        self.manager = InvestmentManager(wallet, subtensor)
        self.N = N
        self.block_time_seconds = block_time_seconds
        self.minimum_stake = minimum_stake

    async def get_top_N_emission_weights(self, N: int = None) -> Dict[int, float]:
        """
        Computes a market-cap-like metric = price(TAO) * alpha_out(TAO) and
        picks top N subnets. Weight = (market cap / sum_of_topN_market_caps).
        """
        if N is None:
            N = self.N

        subnets = await self.subtensor.all_subnets()
        if not subnets:
            return {}

        print(
            f"\n{Fore.GREEN}Explanation:{Style.RESET_ALL} "
            f"Compute 'market cap' = price(TAO)*alpha_out(TAO). Then pick top {N} subnets, "
            f"and weight them by their fraction of the sum of these market caps.\n"
        )

        info_list = []
        for d in subnets:
            mcap = float(d.price.tao) * float(d.alpha_out.tao)
            info_list.append((d.netuid, float(d.price.tao), float(d.alpha_out.tao), mcap))

        # Sort descending by market cap
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
        total_tao: float,
        days: float,
        N: int = None
    ) -> Dict[int, bittensor.Balance]:
        """
        Distributes `total_tao` across `days` worth of block iterations (one DCA action per block).
        In each block, invests an equal fraction of `total_tao` multiplied by each subnet's weight,
        skipping minuscule stake amounts that might cause 'out of range for u64' errors.

        :param total_tao: total TAO to stake by the end of `days`.
        :param days: number of days over which to DCA.
        :param N: pick top N subnets (by emission/market cap).
        """
        if N is None:
            N = self.N

        start_balance = await self.manager.helper.get_balance(self.wallet.coldkeypub.ss58_address)
        print(f"Starting TAO balance: {start_balance}")

        print(
            f"\nWill stake a total of {total_tao} TAO, spread evenly across ~{days} days. "
            f"One iteration per block (~{self.block_time_seconds}s)."
        )

        # Number of blocks in the specified days
        blocks_per_day = int((24 * 3600) / self.block_time_seconds)
        total_blocks = int(blocks_per_day * days)
        if total_blocks < 1:
            print(f"Days={days} too small; no blocks to iterate. Aborting.")
            return {}

        weights = await self.get_top_N_emission_weights(N)
        if not weights:
            print("No subnets or zero total market cap. Aborting.")
            return {}

        # We will stake `stake_per_block` each block, plus leftover on final iteration
        stake_per_block = total_tao / total_blocks
        leftover = 0.0

        stake_info: Dict[int, bittensor.Balance] = {}
        spent_so_far = 0.0

        for block_index in range(total_blocks):
            # For the last iteration, add leftover so we fully use total_tao
            if block_index == total_blocks - 1:
                stake_to_spend = stake_per_block + leftover
            else:
                stake_to_spend = stake_per_block

            iteration_header = (
                f"DCA Iteration #{block_index+1} / {total_blocks} "
                f"(Spent so far: {spent_so_far:.9f}/{total_tao:.9f})"
            )
            print(f"{Fore.YELLOW}{iteration_header}{Style.RESET_ALL}")

            tasks = []
            allocated_this_block = 0.0

            for netuid, w in weights.items():
                portion = stake_to_spend * w
                if portion < self.minimum_stake:
                    # Skip if portion is below the minimum stake threshold
                    continue

                # If adding this portion overshoots total_tao, clamp
                if (spent_so_far + allocated_this_block + portion) > total_tao:
                    portion = total_tao - (spent_so_far + allocated_this_block)

                if portion <= 0:
                    break

                old_stake = stake_info.get(netuid, bittensor.Balance.from_tao(0))
                tasks.append(
                    asyncio.create_task(
                        self._stake_and_fetch(netuid, portion, old_stake)
                    )
                )
                allocated_this_block += portion

            # leftover from this block’s plan if we skip minuscule allocations
            leftover_block = stake_to_spend - allocated_this_block
            leftover += leftover_block

            # Perform all stakings in parallel
            results = await asyncio.gather(*tasks)

            # Update stake_info and show a table of changes
            table_rows = []
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

            spent_so_far += allocated_this_block

            if table_rows:
                headers = ["NetUID", "Old Alpha", "New Alpha", "Alpha Diff", "Price", "Action"]
                print(tabulate(table_rows, headers=headers, tablefmt="fancy_grid"))

            tao_balance = await self.manager.helper.get_balance(self.wallet.coldkeypub.ss58_address)
            print(
                f"Wallet TAO Balance after iteration #{block_index+1}: "
                f"{color_value(float(tao_balance.tao), decimals=9)}\n"
            )

            # Wait for the next block
            await self.subtensor.wait_for_block()

            # If we've basically staked the entire total already, we can stop early
            if spent_so_far >= total_tao - 1e-12:
                print("We have staked the full allocation. Breaking early.\n")
                break

        print(
            f"Finished DCA over ~{days} days ({total_blocks} blocks). "
            f"Final staked amount ~ {spent_so_far:.9f} / {total_tao:.9f}"
        )
        return stake_info

    async def _stake_and_fetch(
        self,
        netuid: int,
        amount: float,
        old_stake: bittensor.Balance
    ):
        subnet_info = await self.subtensor.subnet(netuid)
        # Actually call the chain to stake
        await self.manager.staker.buy_alpha(netuid=netuid, tao_amount=amount)
        new_stake = await self.manager.staker.get_alpha_balance(netuid)
        alpha_diff = float(new_stake.tao) - float(old_stake.tao)
        return netuid, old_stake, new_stake, alpha_diff, subnet_info.price
