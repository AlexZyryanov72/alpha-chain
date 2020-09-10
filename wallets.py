import pickle
import os
from wallet import Wallet


class Wallets(object):
    """ Wallet stores private and public keys.
    Args:
    Attributes:
        wallets (dict): a wallets dict.
    """

    wallet_file = 'data/wallet.dat'

    def __init__(self):
        try:
            with open(self.wallet_file, 'rb') as f:
                self.wallets = pickle.load(f)
        except FileNotFoundError:
            self.wallets = {}
            self.wallets['wallets'] = {}

    def add_wallet(self):
        wallet = Wallet()
        if not self.wallets['wallets'].keys():
            self.current_address = wallet.address
        self.wallets['wallets'][wallet.address] = wallet
        self.save_to_file()
        return wallet

    def get_addresses(self):
        return [addr for addr in self.wallets['wallets'].keys()]


    @property
    def current_address(self):
        return self.wallets['current_address']

    @current_address.setter
    def current_address(self, addr):
        self.wallets['current_address'] = addr
        self.save_to_file()

    def get_wallet(self, addr):
        if addr in self.wallets['wallets'].keys():
            return self.wallets['wallets'][addr]
        else:
            return None

    def save_to_file(self):
        # Создаем папку если не существует
        dir = '/'.join(self.wallet_file.split('/')[:-1])
        if not os.path.exists(dir):
            os.makedirs(dir)

        with open(self.wallet_file, 'wb') as f:
            pickle.dump(self.wallets, f)