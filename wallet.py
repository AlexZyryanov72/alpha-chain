import os
from py_ecc import secp256k1
from _pysha3 import keccak_256


class Wallet(object):
    """ Wallet stores private and public keys.
    Args:
    Attributes:
        _private_key (string): a private key.
        _public_key (string): a public key.
        _hash_public_key (string): a hash of public key.
        _address (string): a wallet address.
    """

    def __init__(self):
        self._private_key = os.urandom(64).hex()
        self._public_key = self._priv_to_pub()
        self._hash_public_key = keccak_256(bytes(self._public_key, 'utf-8')).hexdigest()
        self._address = self._hash_public_key[24:]
        while True:
            pass1 = input("Input password: ")
            pass2 = input("Repeat password: ")
            if pass1 == pass2:
                break
            else:
                print("You password do not match. Try again.")
        print('Create new wallet. Save private key and password in a safe place.')
        print(f'Address key: {self.address}')
        print(f'Public  key: {self.public_key}')
        print(f'Private key: {self.private_key}')

    def _priv_to_pub(self):
        priv = int(self._private_key, 16).to_bytes(64, 'big')
        res = secp256k1.privtopub(priv)
        a = res[0].to_bytes(32, 'big')
        b = res[1].to_bytes(32, 'big')
        pub = int.from_bytes(a + b, 'big')
        return '0' * (128-len(hex(pub)[2:])) + hex(pub)[2:]

    @property
    def private_key(self):
        return self._private_key

    @property
    def public_key(self):
        return self._public_key

    @property
    def hash_public_key(self):
        return self._hash_public_key

    @property
    def address(self):
        return self._address
