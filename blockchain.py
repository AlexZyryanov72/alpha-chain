import hashlib
import json
import time
import requests


class Blockchain:
    def __init__(self):
        self.current_transactions = []
        self.chain = []
        self.genesis_amount_miner = 100         # Первоначальная сумма вознаграждения майнерам
        self.block_cut_award = 5                # Количество блоков урезания награды
        self.block_change_difficuly = 20        # количество блоков после которых меняется сложность
        self.block_time_mining = 10             # усрезненное время майнинга блока


    def difficulty(self, block):
        count_change_difficulty = block['index'] // self.blockchain.block_change_difficuly

        # if 0 <= index_block < self.block_change_difficuly
        if count_change_difficulty == 0:
            return 0.0001
        else:
            # find previous difficulty
            previous_difficulty_last_block = count_change_difficulty * self.blockchain.block_change_difficuly - 1
            previous_difficulty = self.chain[previous_difficulty_last_block]['difficulty']

            # search middle previos time mining for block
            if count_change_difficulty * self.blockchain.block_change_difficuly == block['index']:
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

        :param chain: A blockchain
        :return: True if valid, False if not
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

    def new_transaction(self, sender, recipient, amount):
        """
        Creates a new transaction to go into the next mined Block

        :param sender: Address of the Sender
        :param recipient: Address of the Recipient
        :param amount: Amount
        :return: The index of the Block that will hold this transaction
        """
        transaction = {'sender': sender, 'recipient': recipient, 'amount': amount,
                       'index': len(self.current_transactions)}
        self.current_transactions.append({'transaction' : transaction, 'hash':  self.hash(transaction)})

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
        """
        self.proof_of_work(block)
        # Reset the current list of transactions
        self.blockchain.current_transactions = []

        self.blockchain.chain.append(block)
        """
        # Search amount pay miner
        try:
            amount_block = self.genesis_amount_miner / (2**((self.chain[-1]['index'] + 1) // self.block_cut_award))
        except:
            amount_block = self.genesis_amount_miner # first pay genesis

        # We must receive a reward for finding the proof.
        # The sender is "0" to signify that this node has mined a new coin.
        self.new_transaction(
            sender="0",
            amount=amount_block,
        )
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



