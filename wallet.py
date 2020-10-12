import os
from py_ecc import secp256k1
from _pysha3 import keccak_256


class Wallet(object):
    """ Wallet stores private and public keys.
    Args:
    Attributes:
        _private_key (string): a private key.
        _public_key (string): a public key.
        _address (string): a wallet address.
    """

    def __init__(self):
        self._private_key = self.generate_private_key()
        self._public_key = self.priv_to_pub(self._private_key)
        self._address = self.public_to_address(self._public_key)

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

    def generate_private_key(self):
        from _pysha3 import sha3_256

        data = ''
        for i in range(100):
            data += str(os.urandom(64).hex())
        return sha3_256(bytes(data[:len(data) // 2], 'utf-8')).hexdigest() + \
               sha3_256(bytes(data[len(data) // 2:], 'utf-8')).hexdigest()

    def public_to_address(self, public_key):
        address = keccak_256(bytes(public_key, 'utf-8')).hexdigest()[24:]
        return self.address_check_sum(address)

    def priv_to_pub(self, private_key):
        priv = int(private_key, 16).to_bytes(64, 'big')
        pub = secp256k1.privtopub(priv)
        pub = pub[0].to_bytes(32, 'big') + pub[1].to_bytes(32, 'big')
        pub = int.from_bytes(pub, 'big')
        return '0' * (128-len(hex(pub)[2:])) + hex(pub)[2:]

    def address_check_sum(self, address):
        address = address.lower()
        hash_addr = bin(int(keccak_256(address.encode()).hexdigest(), 16))
        hash_addr = '0' * (256 - len(hash_addr)) + hash_addr[2:]
        res = ''
        for i in range(len(address)):
            if address[i].isalpha() and hash_addr[4*i] == '1':
                res += address[i].upper()
            else:
                res += address[i]
        return res

    def check_valid_address(self, address):
        return address == self.address_check_sum(address)

    @property
    def private_key(self):
        return self._private_key

    @property
    def public_key(self):
        return self._public_key

    @property
    def address(self):
        return self._address
