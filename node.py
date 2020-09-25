from flask import Flask, jsonify, request
from blockchain import Blockchain
import time
import sys
import requests
from threading import Thread


class FullNode:
    def __init__(self, pipe_node, port):
        self.DEFAULT_NODES = ("127.0.0.1:7777", "127.0.0.1:7778",)
        self.pipe_node = pipe_node
        self.port = port
        self.blockchain = Blockchain()
        self.nodes = set()
        self.my_ip = 0

    def load_all_nodes(self):
        if not self.nodes:
            self.nodes = set(self.DEFAULT_NODES)

        for node in self.nodes.copy():
            try:
                response = requests.get(f'http://{node}/nodes/getnodes', verify=False)
                self.nodes.update(set(response.json()))
            except Exception:
                pass # Node not connect

    def register_node(self):
        for node in self.nodes:
            try:
                if self.my_ip == 0:
                    self.my_ip = requests.get(f'http://{node}/nodes/getmyip', verify=False).json()
                    self.my_ip = f'{self.my_ip}:{self.port}'
                response = requests.post(f'http://{node}/nodes/register_node', json={"node_ip": self.my_ip}, verify=False)
                self.nodes.update(set(response.json()))
            except Exception:
                pass #Node not connect

    def update_blockchain(self):
        for node in self.nodes:
            try:
                len_chain = requests.get(f'http://{node}/nodes/get_len_chain', verify=False).json()
                if self.blockchain.len_chain < len_chain:
                    new_chain = requests.get(f'http://{node}/nodes/get_chain', verify=False).json()
                    if self.blockchain.valid_chain(new_chain):
                        self.blockchain.chain = new_chain
            except Exception:
                pass #Node not connect or incorrect data

    def start(self):
        # Instantiate the Node
        app = Flask(__name__)

        @app.route('/nodes/getnodes', methods=['GET'])
        def get_nodes():
            return jsonify(list(self.nodes)), 200

        @app.route('/nodes/getmyip', methods=['GET'])
        def get_myip():
            return jsonify(request.remote_addr), 200

        @app.route('/nodes/register_node', methods=['POST'])
        def register_node():
            self.nodes.add(request.json["node_ip"])
            return jsonify([]), 200

        @app.route('/transactions/new', methods=['POST'])
        def new_transaction():
            values = request.get_json()

            # Check that the required fields are in the POST'ed data
            required = ['sender', 'recipient', 'amount']
            if not all(k in values for k in required):
                return 'Missing values', 400

            # Create a new Transaction
            self.blockchain.new_transaction(values['sender'], values['recipient'], values['amount'])
            if self.blockchain.chain:
                index = self.blockchain.chain['index']
            else:
                index = 0
            response = {'message': f'Transaction will be added to Block {index}'}
            return jsonify(response), 201

        @app.route('/nodes/get_len_chain', methods=['GET'])
        def get_len_chain():
            return jsonify(self.blockchain.len_chain), 200

        @app.route('/nodes/get_chain', methods=['GET'])
        def get_chain():
            return jsonify(self.blockchain.chain), 200

        @app.route('/nodes/get_new_job', methods=['POST'])
        def get_new_job():
            return jsonify(self.blockchain.new_block()), 200

        @app.route('/nodes/set_proof_block', methods=['POST'])
        def set_proof_block():
            self.blockchain.chain.append(request.get_json())
            return jsonify([]), 200


        def job_node():
            update_node_time = 0
            while True:
                # read from main process command
                if self.pipe_node.poll():
                    command = self.pipe_node.recv()
                    if command == 'exit':
                        self.pipe_node.send('exit_ok')
                        sys.exit(0)

                nowtime = time.time()

                # load all nodes and update ip in all nodes
                if nowtime - update_node_time > 60:
                    self.load_all_nodes()
                    self.register_node()
                    update_node_time = nowtime + 60

                # sinc chain with all nodes
                self.update_blockchain()

                time.sleep(15)




        # Запускаем ноду
        job_node1 = Thread(target=job_node)
        job_node1.start()



        app.run(host='127.0.0.1', port=self.port)

    """
    while True:
        # Принимаем от майнера новый блок
        if self.pipe_node_to_miner.poll():
            block = self.pipe_node_to_miner.recv()
            # Проверяем что новый блок валидный для текущей цепочки
            if not self.blockchain.chain or \
                    (block['previous_hash'] == self.blockchain.hash(self.blockchain.chain[-1]) and
                     block['index'] == self.blockchain.chain[-1]['index'] + 1):
                self.blockchain.chain.append(block)
            else:
                print("Блок не подходит. Отпраляем майнеру обновленную цепочку блоков для работы")

                #while True:
                #    index = self.blockchain.chain[-1]['index']
                #    self.pipe_node_to_miner.send(self.blockchain.chain[index])
                   #if self.pipe_node_to_miner.recv()

        time.sleep(1)
    """


