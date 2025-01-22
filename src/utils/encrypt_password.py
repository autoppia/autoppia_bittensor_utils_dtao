""""
Password on .env to unlock coldkey must be encrypted using this script
"""


def encrypt_password(key: str, value: str) -> str:
    encrypted_chars = []
    for i, ch in enumerate(value):
        encrypted_char = chr(ord(ch) ^ ord(key[i % len(key)]))
        encrypted_chars.append(encrypted_char)
    return "".join(encrypted_chars)


# This is example. I have wallets on ~.bittensor/wallets and my username is usuario1. Thats why my envvar for password is that.
env_var_name = "BT_PW__HOME_USUARIO1__BITTENSOR_WALLETS_TEST-WALLET_COLDKEY"
real_password = "password"

xor_encrypted = encrypt_password(env_var_name, real_password)
print("Put this in your .env file under", env_var_name, ":", xor_encrypted)
