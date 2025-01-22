import bittensor
import os
from dotenv import load_dotenv

load_dotenv()


def get_my_wallet():

    my_wallet = bittensor.wallet(
        name=os.getenv("BT_WALLET_NAME"),
        hotkey=os.getenv("BT_HOTKEY_NAME")
    )
    my_wallet.unlock_coldkey()
    return my_wallet
