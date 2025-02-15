import bittensor
import os
from dotenv import load_dotenv

load_dotenv()


def get_my_wallet(unlock=False):

    my_wallet = bittensor.wallet(
        name=os.getenv("BT_WALLET_NAME"),
        hotkey=os.getenv("BT_HOTKEY_NAME")
    )

    if unlock:
        password = os.getenv("COLDKEY_PASSWORD")
        my_wallet.coldkey_file.save_password_to_env(password)
        my_wallet.unlock_coldkey()

    return my_wallet
