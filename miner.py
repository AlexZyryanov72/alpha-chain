import time
import sys
from wallets import Wallets
import requests
from blockchain import Blockchain


class Miner:
    def __init__(self, pipe_miner, connect_address_node):
        self.pipe_miner = pipe_miner
        self.connect_address_node = connect_address_node
        self.blockchain = Blockchain()

    def start(self):
        while True:
            # read from main process command
            if self.pipe_miner.poll():
                command = self.pipe_miner.recv()
                if command == 'exit':
                    sys.exit(0)

            # send request for new job
            while True:
                try:
                    block = requests.post(f'http://{self.connect_address_node}/nodes/get_new_job', verify=False).json()
                    break
                except:
                    print('Not connect node mining for new job')

            block['recipient'] = Wallets().current_address
            block['proof'] = self.proof_of_work(block)

            # send request proof block
            while True:
                try:
                    block = requests.post(f'http://{self.connect_address_node}/nodes/set_proof_block',
                                          json=block, verify=False).json()
                    break
                except:
                    print('Not connect node mining for proof block')


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

        return proof