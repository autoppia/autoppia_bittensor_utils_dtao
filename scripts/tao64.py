#!/usr/bin/env python3

import argparse
import asyncio
import bittensor
from .tao64 import Tao64
from bittensor import AsyncSubtensor


async def main():
    parser = argparse.ArgumentParser(description="TAO64 CLI")
    parser.add_argument("--wallet_coldkey", type=str, required=True, help="Path to coldkey file")
    parser.add_argument("--wallet_hotkey", type=str, required=True, help="Path to hotkey file")
    parser.add_argument("--total_stake", type=float, default=100.0, help="Total TAO to stake")
    parser.add_argument("--increment", type=float, default=10.0, help="Increment amount per iteration")

    args = parser.parse_args()

    # Create a Bittensor wallet from provided paths
    wallet = bittensor.wallet(
        path=".",
        name="default",
        hotkey=args.wallet_hotkey,
        coldkey=args.wallet_coldkey
    )
    # Example usage of your AsyncSubtensor
    subtensor = AsyncSubtensor(
        network="mock",  # or your actual network
    )

    tao64 = Tao64(wallet=wallet, subtensor=subtensor)
    await tao64.dca_tao64(
        total_stake=args.total_stake,
        increment=args.increment
    )

if __name__ == "__main__":
    asyncio.run(main())
