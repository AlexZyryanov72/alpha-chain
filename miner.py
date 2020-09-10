import time
from wallets import Wallets


class Miner:
    def __init__(self, pipe_miner_to_chain, blockchain):
        self.pipe_miner_to_chain = pipe_miner_to_chain
        self.blockchain = blockchain


    def start(self):
        while True:
            wallet_address = Wallets().current_address
            # We must receive a reward for finding the proof.
            # The sender is "0" to signify that this node has mined a new coin.
            try:
                amount_block = self.blockchain.genesis_amount_miner / (2**((self.blockchain.chain[-1]['index'] + 1) //
                                                                           self.blockchain.block_cut_award))
            except:
                amount_block = 100

            self.blockchain.new_transaction(
                sender="0",
                recipient= wallet_address,
                amount=amount_block,
            )

            # Forge the new Block by adding it to the chain
            block = self.new_block()

            response = {
                'message': "New Block Forged",
                'time': time.ctime(block['timestamp']),
                'index': block['index'],
                'proof': block['proof'],
                'previous_hash': block['previous_hash'],
                'transactions': block['transactions']
            }
            print(response)
            self.pipe_miner_to_chain.send(block)

    def proof_of_work(self, block):
        """
        Simple Proof of Work Algorithm:

         - Find a number p' such that hash(pp') contains leading 4 zeroes
         - Where p is the previous proof, and p' is the new proof

        :param block: <dict> last Block
        :return: <int>
        """

        proof = 0
        while self.blockchain.valid_proof(block) is False:
            proof += 1
            block['proof'] = proof


    def new_block(self):
        """
        Create a new Block in the Blockchain
        :return: New Block
        """

        if self.blockchain.chain:
            index = self.blockchain.chain[-1]['index'] + 1
            previous_hash = self.blockchain.hash(self.blockchain.chain[-1])
        else:
            # Геннезис блок начальные данные
            index = 0
            previous_hash = '0'

        if index % self.blockchain.block_change_difficuly == 0 and index !=0:
            self.blockchain.change_difficulty()
        block = {
            'index': index,
            'timestamp': time.time(),
            'previous_hash': previous_hash,
            'difficulty': self.blockchain.difficulty,
            'proof': 0,
            'transactions': self.blockchain.current_transactions,

        }

        self.proof_of_work(block)
        # Reset the current list of transactions
        self.blockchain.current_transactions = []

        self.blockchain.chain.append(block)
        return block
