import hashlib
import json
import os
import time
from uuid import uuid4
from multiprocessing import Process, Pipe
import requests
from flask import Flask, jsonify, request

DEFAULT_NODES = ("127.0.0.1:5000", "127.0.0.1:5001",)


class Blockchain:
    def __init__(self):
        self.current_transactions = []
        self.chain = []
        self.nodes = set()
        self.my_ip = ""
        self.genesis_amount_miner = 100 # Первоначальная сумма вознаграждения майнерам
        self.block_cut_award = 5 # Количество блоков урезания награды
        self.block_change_difficuly = 20 #количество блоков после которых меняется сложность
        self.block_time_mining = 10 # усрезненное время майнинга блока

        if not self.chain:
            self.difficulty = 0.0001
            self.set_difficulty(self.difficulty)
        self.run_node()

    def set_difficulty(self, difficulty):
        if difficulty == 0:
            target = 2 ** 256 - 1
        else:
            target = min(int((0xffff0000 * 2 ** (256 - 64) + 1) / difficulty - 1 + 0.5), 2 ** 256 - 1)

        self.difficulty_target = '%064x' % target

    def load_all_nodes(self):
        if not self.nodes:
            self.nodes = set(DEFAULT_NODES)

        for node in self.nodes.copy():
            try:
                response = requests.get(f'http://{node}/nodes/getnodes', verify=False)
                self.nodes.update(set(response.json()))
            except:
                pass

    def register_node(self):
        for node in self.nodes:
            try:
                if not self.my_ip:
                    self.my_ip = requests.get(f'http://{node}/nodes/getmyip', verify=False).json()
                    self.my_ip = f'{self.my_ip}:{port}'
                response = requests.post(f'http://{node}/nodes/setmyip', json={"my_ip": self.my_ip} , verify=False)
                self.nodes.update(set(response.json()))
            except:
                pass

    def run_node(self):
        self.load_all_nodes()
        self.register_node()
        print(self.nodes)

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

        if index % self.block_change_difficuly == 0 and index !=0:
            block_middle_time = (time.time() - self.chain[-self.block_change_difficuly]["timestamp"]) / self.block_change_difficuly
            self.difficulty = self.difficulty * self.block_time_mining / block_middle_time
            print(f'Сложность сети изменилась {self.difficulty}, среднее время на блок {block_middle_time}')
            self.set_difficulty(self.difficulty)
        block = {
            'index': index,
            'timestamp': time.time(),
            'previous_hash': previous_hash,
            'difficulty': self.difficulty,
            'proof': 0,
            'transactions': self.current_transactions,

        }

        proof = self.proof_of_work(block)
        # Reset the current list of transactions
        self.current_transactions = []

        self.chain.append(block)
        return block

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

    def proof_of_work(self, block):
        """
        Simple Proof of Work Algorithm:

         - Find a number p' such that hash(pp') contains leading 4 zeroes
         - Where p is the previous proof, and p' is the new proof

        :param last_block: <dict> last Block
        :return: <int>
        """

        proof = 0
        while self.valid_proof(block) is False:
            proof += 1
            block['proof'] = proof

        return proof


    def valid_proof(self, block):
        """
        Validates the Proof

        :param block: last block

        :return: <bool> True if correct, False if not.

        """
        guess = str(block).encode()
        guess_hash = hashlib.sha256(guess).hexdigest()

        return guess_hash <= self.difficulty_target


# Instantiate the Node
app = Flask(__name__)

from py_ecc import secp256k1
from _pysha3 import keccak_256

def privToPub(priv):
    int()
    priv = int(priv, 16).to_bytes(64, 'big')
    res = secp256k1.privtopub(priv)
    a = res[0].to_bytes(32, 'big')
    b = res[1].to_bytes(32, 'big')
    pub = int.from_bytes(a + b, 'big')
    return '0' * (128-len(hex(pub)[2:])) + hex(pub)[2:]
    # Generate a globally unique address for this node

def pubToAddr(pub):
    return keccak_256(bytes(pub, 'utf-8')).hexdigest()[24:]

private_key = os.urandom(64).hex()
public_key = privToPub(private_key)
node_identifier = pubToAddr(public_key)



@app.route('/nodes/getnodes', methods=['GET'])
def get_nodes():
    return jsonify(list(blockchain.nodes)), 200


@app.route('/nodes/getmyip', methods=['GET'])
def get_myip():
    return jsonify(request.remote_addr), 200


@app.route('/nodes/setmyip', methods=['POST'])
def set_myip():
    blockchain.nodes.add(request.json["my_ip"])
    print(blockchain.nodes)
    return jsonify([]), 200


@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()

    # Check that the required fields are in the POST'ed data
    required = ['sender', 'recipient', 'amount']
    if not all(k in values for k in required):
        return 'Missing values', 400

    # Create a new Transaction
    blockchain.new_transaction(values['sender'], values['recipient'], values['amount'])
    if blockchain.chain:
        index = blockchain.chain['index']
    else:
        index = 0
    response = {'message': f'Transaction will be added to Block {index}'}
    return jsonify(response), 201


@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200


@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    replaced = blockchain.resolve_conflicts()

    if replaced:
        response = {
            'message': 'Our chain was replaced',
            'new_chain': blockchain.chain
        }
    else:
        response = {
            'message': 'Our chain is authoritative',
            'chain': blockchain.chain
        }

    return jsonify(response), 200


def mine(a, blockchain):
    while True:
        # We must receive a reward for finding the proof.
        # The sender is "0" to signify that this node has mined a new coin.
        try:
            amount_block = blockchain.genesis_amount_miner / (2**((blockchain.chain[-1]['index'] + 1) // blockchain.block_cut_award))
        except:
            amount_block = 100

        blockchain.new_transaction(
            sender="0",
            recipient=node_identifier,
            amount=amount_block,
        )

        # Forge the new Block by adding it to the chain
        block = blockchain.new_block()

        response = {
            'message': "New Block Forged",
            'time': time.ctime(block['timestamp']),
            'index': block['index'],
            'proof': block['proof'],
            'previous_hash': block['previous_hash'],
            'transactions': block['transactions']
        }
        print(response)


if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=7003, type=int, help='port to listen on')
    parser.add_argument('-m', '--miner', help='start miner', action='store_const', const=True, default=False)
    args = parser.parse_args()
    port = args.port

    # Instantiate the Blockchain
    blockchain = Blockchain()

    a,b = Pipe()
    if args.miner:
        # Запускаем майнинг
        p1 = Process(target=mine, args=(a, blockchain))
        p1.start()

    # Запускаем сервер для приема транзакций
    p2 = Process(target=app.run(host='127.0.0.1', port=port), args=b)
    p2.start()



