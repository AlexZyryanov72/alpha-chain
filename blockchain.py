import hashlib
import json
import time
import requests
from wallets import Wallets
from wallets import Wallet
from py_ecc.secp256k1 import ecdsa_raw_sign, ecdsa_raw_recover, privtopub
from _pysha3 import keccak_256


class Blockchain:
    def __init__(self):
        self.current_transactions = []
        self.chain = []
        self.genesis_amount_miner = 5           # Первоначальная сумма вознаграждения майнерам
        self.block_cut_award = 60*60*24*365*2   # Количество блоков урезания награды
        self.block_change_difficuly = 60        # количество блоков после которых меняется сложность
        self.block_time_mining = 60              # middle time mining in seconds


    def difficulty(self, block):
        count_change_difficulty = block['index'] // self.block_change_difficuly

        # if 0 <= index_block < self.block_change_difficuly
        if count_change_difficulty == 0:
            return 0.00000001
        else:
            # find previous difficulty
            previous_difficulty_last_block = count_change_difficulty * self.block_change_difficuly - 1
            previous_difficulty = self.chain[previous_difficulty_last_block]['difficulty']

            # search middle previos time mining for block
            if count_change_difficulty * self.block_change_difficuly == block['index']:
                time_finish = block['timestamp']
            else:
                time_finish = self.chain[previous_difficulty_last_block + 1]['timestamp']
            time_start = self.chain[previous_difficulty_last_block - self.block_change_difficuly + 1]["timestamp"]
            block_middle_time = (time_finish - time_start) / self.block_change_difficuly
            # search difficulty for this block what mining was block_time_mining for block
            return previous_difficulty * self.block_time_mining / block_middle_time

    def difficulty_target(self, difficulty):
        if difficulty == 0:
            target = 2 ** 256 - 1
        else:
            target = min(int((0xffff0000 * 2 ** (256 - 64) + 1) / difficulty - 1 + 0.5), 2 ** 256 - 1)
        return '%064x' % target

    def valid_chain(self, chain):
        """
        Determine if a given blockchain is valid

        :param  chain: A blockchain
        :return      : True if valid, False if not
        """

        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            # Check that the hash of the block is correct
            last_block_hash = self.hash(last_block)
            if block['previous_hash'] != last_block_hash:
                return False

            # Check that the Proof of Work is correct
            if self.valid_proof(block) is False:
                return False

            last_block = block
            current_index += 1

        return True

    def sign(self, data, address):
        """
            Signing a document at the wallet address with a private key

        :param    data: data transaction
               address: address wallet
        :return       : signatura
        """

        if address == "0":
            return ""

        priv = Wallets().get_wallet(address).private_key
        priv = int(priv, 16).to_bytes(64, 'big')

        data = keccak_256(bytes(json.dumps(data), 'utf-8')).digest()
        ans = ecdsa_raw_sign(data, priv)
        res = '0x'
        for j in range(3):
            if j > 0:
                res += '0' * (64 - len(hex(ans[j])[2:])) + hex(ans[j])[2:]
            else:
                res += '0' * (2 - len(hex(ans[j])[2:])) + hex(ans[j])[2:]
        return res

    def sign_to_pub(self, data, sign):
        """
        Recovers the owner's public key using the document and its signature

        :param    data: data transaction
        :param    sign: signatura data transaction
        :return       : public key owner this document
        """

        sign = (int(sign[0:4], 16), int(sign[4:68], 16), int(sign[68:], 16),)
        data = keccak_256(bytes(json.dumps(data), 'utf-8')).digest()
        pub = ecdsa_raw_recover(data, sign)
        pub = pub[0].to_bytes(32, 'big') + pub[1].to_bytes(32, 'big')
        pub = int.from_bytes(pub, 'big')
        pub = ('0' * (128 - len(hex(pub)[2:])) + hex(pub)[2:])
        return Wallet.public_to_address(pub)


    def new_transaction(self, sender, recipient, amount):
        """
        Creates a new transaction

        :param    sender: Address of the Sender
        :param recipient: Address of the Recipient
        :param    amount: Amount
        :return:        : Transaction json format
        """

        transaction = {'sender': sender, 'recipient': recipient, 'amount': amount,
                       'index': len(self.current_transactions)}
        sign = self.sign(transaction, sender)

        return {'transaction' : transaction,
                'sign': self.sign(transaction, sender),
                'hash':  self.hash(transaction)}


    def miner_amount_payment(self, block):
        """
        Determining the amount of payment to the miner for the block

        :param     block: Block for which the payout amount is calculated
        :return:        : Amount payment
        """
        return self.genesis_amount_miner / (2**((block['index']) // self.block_cut_award))


    def new_block(self):
        """
        Create a new Block in the Blockchain
        :return: New Block
        """

        if self.chain:
            index = self.chain[-1]['index'] + 1
            previous_hash = self.hash(self.chain[-1])
        else:
            # Геннезис блок начальные данные
            index = 0
            previous_hash = '0'

        block = {
            'index': index,
            'timestamp': time.time(),
            'previous_hash': previous_hash,
            'proof': 0,
            'transactions': self.current_transactions,

        }

        block['difficulty'] = self.difficulty(block)
        return block

    def valid_proof(self, block):
        """
        Validates the Proof
        :param block: last block
        :return: <bool> True if correct, False if not.
        """

        return self.hash(block) <= self.difficulty_target(block['difficulty'])

    @property
    def last_block(self):
        return self.chain[-1]


    @property
    def len_chain(self):
        try:
            return self.chain[-1]['index'] + 1
        except Exception:
            return 0

    @staticmethod
    def hash(data):
        """
        Creates a SHA-256 hash of a Block

        :data: Block or Transaction
        """

        # We must make sure that the Dictionary is Ordered, or we'll have inconsistent hashes
        string = json.dumps(data, sort_keys=True).encode()
        return hashlib.sha256(string).hexdigest()



