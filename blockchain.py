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

        self.change_difficulty()

    def change_difficulty(self):
        if self.chain:
            block_middle_time = (time.time() - self.chain[-self.block_change_difficuly]["timestamp"]) / \
                                self.block_change_difficuly
            self.difficulty = self.difficulty * self.block_time_mining / block_middle_time
            print(f'Сложность сети изменилась {self.difficulty}, среднее время на блок {block_middle_time}')
        else:
            self.difficulty = 0.0001

        if self.difficulty == 0:
            target = 2 ** 256 - 1
        else:
            target = min(int((0xffff0000 * 2 ** (256 - 64) + 1) / self.difficulty - 1 + 0.5), 2 ** 256 - 1)

        self.difficulty_target = '%064x' % target


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
            print(f'{last_block}')
            print(f'{block}')
            print("\n-----------\n")
            # Check that the hash of the block is correct
            last_block_hash = self.hash(last_block)
            if block['previous_hash'] != last_block_hash:
                return False

            # Check that the Proof of Work is correct
            if not self.valid_proof(last_block['proof'], block['proof'], last_block_hash):
                return False

            last_block = block
            current_index += 1

        return True

    def resolve_conflicts(self):
        """
        This is our consensus algorithm, it resolves conflicts
        by replacing our chain with the longest one in the network.

        :return: True if our chain was replaced, False if not
        """

        neighbours = self.nodes
        new_chain = None

        # We're only looking for chains longer than ours
        max_length = len(self.chain)

        # Grab and verify the chains from all the nodes in our network
        for node in neighbours:
            response = requests.get(f'http://{node}/chain')

            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']

                # Check if the length is longer and the chain is valid
                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain

        # Replace our chain if we discovered a new, valid chain longer than ours
        if new_chain:
            self.chain = new_chain
            return True

        return False


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

    @property
    def last_block(self):
        return self.chain[-1]

    @staticmethod
    def hash(data):
        """
        Creates a SHA-256 hash of a Block

        :data: Block or Transaction
        """

        # We must make sure that the Dictionary is Ordered, or we'll have inconsistent hashes
        string = json.dumps(data, sort_keys=True).encode()
        return hashlib.sha256(string).hexdigest()


    def valid_proof(self, block):
        """
        Validates the Proof

        :param block: last block

        :return: <bool> True if correct, False if not.

        """

        return self.hash(block) <= self.difficulty_target
