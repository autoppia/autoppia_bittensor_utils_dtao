#!/usr/bin/env python3
import asyncio
import bittensor
from dotenv import load_dotenv
from classes.subnet_staker import SubnetStaker
from utils.get_my_wallet import get_my_wallet

load_dotenv()


async def main():
    # Create the AsyncSubtensor instance
    subtensor = await bittensor.async_subtensor(network='test')

    # Get your wallet
    my_wallet = get_my_wallet()

    # Instantiate the SubnetStaker
    staker = SubnetStaker(wallet=my_wallet, subtensor=subtensor)

    # Subnets and respective percentages (must sum to 1.0)
    subnets_to_stake = [1, 277, 18, 5]
    subnets_percentages = [0.25, 0.25, 0.25, 0.25]

    # Initial balance
    old_balance = await subtensor.get_balance(my_wallet.coldkeypub.ss58_address)
    print(f"Starting TAO balance: {old_balance}")

    while True:
        try:
            # Wait for the next block
            current_block = await subtensor.get_current_block()
            print(f"Current block: {current_block}. Waiting for next block...")
            await subtensor.wait_for_block(current_block + 1)

            # Get updated balance
            new_balance = await subtensor.get_balance(my_wallet.coldkeypub.ss58_address)
            dividends = new_balance - old_balance

            # If there are dividends, stake them using your percentages
            # TODO There is an issue with transfers being interpreted as dividends. We should sove this.
            if dividends > bittensor.Balance(0) and dividends < bittensor.Balance(0.5):
                print(f"Dividends detected: {dividends}")
                for netuid, pct in zip(subnets_to_stake, subnets_percentages):
                    stake_amount_tao = dividends.tao * pct
                    if stake_amount_tao > 0:
                        await staker.buy_alpha(netuid=netuid, tao_amount=stake_amount_tao)
                        print(f"Staked {stake_amount_tao} TAO on netuid={netuid}.")
                # Update the old balance after staking
                old_balance = await subtensor.get_balance(my_wallet.coldkeypub.ss58_address)
                print(f"Balance after staking dividends: {old_balance}")
            else:
                print("No new dividends this block.")
        except KeyboardInterrupt:
            print("Exiting script.")
            break
        except Exception as e:
            print(f"Error in loop: {e}")
            await asyncio.sleep(5)  # Optional small delay before retry

if __name__ == "__main__":
    asyncio.run(main())
