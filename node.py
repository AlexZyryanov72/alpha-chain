from flask import Flask, jsonify, request
from blockchain import Blockchain
import time
import requests
from threading import Thread



class FullNode:
    def __init__(self, port):
        self.DEFAULT_NODES = ("127.0.0.1:7777", "127.0.0.1:7778",)
        self.port = port
        self.blockchain = Blockchain()
        self.nodes = set()
        self.my_ip = self.DEFAULT_NODES[0]

        self.load_all_nodes()
        self.register_node()
        print(self.nodes)

    def load_all_nodes(self):
        if not self.nodes:
            self.nodes = set(self.DEFAULT_NODES)

        for node in self.nodes.copy():
            try:
                response = requests.get(f'http://{node}/nodes/getnodes', verify=False)
                self.nodes.update(set(response.json()))
            except:
                pass

    def register_node(self):
        for node in self.nodes:
            try:
                if self.my_ip == self.DEFAULT_NODES[0]:
                    self.my_ip = requests.get(f'http://{node}/nodes/getmyip', verify=False).json()
                    self.my_ip = f'{self.my_ip}:{self.port}'
                response = requests.post(f'http://{node}/nodes/setmyip', json={"my_ip": self.my_ip}, verify=False)
                self.nodes.update(set(response.json()))
            except:
                pass




    def start(self):
        # Instantiate the Node
        app = Flask(__name__)

        @app.route('/nodes/getnodes', methods=['GET'])
        def get_nodes():
            return jsonify(list(self.nodes)), 200

        @app.route('/nodes/getmyip', methods=['GET'])
        def get_myip():
            return jsonify(request.remote_addr), 200

        @app.route('/nodes/setmyip', methods=['POST'])
        def set_myip():
            self.nodes.add(request.json["my_ip"])
            print(self.nodes)
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

        @app.route('/get_len_chain', methods=['GET'])
        def get_len_chain():
            return self.blockchain.chain[-1]['index'] + 1

        @app.route('/chain', methods=['GET'])
        def full_chain():
            response = {
                'chain': self.blockchain.chain,
                'length': len(self.blockchain.chain),
            }
            return jsonify(response), 200

        @app.route('/nodes/resolve', methods=['GET'])
        def consensus():
            replaced = self.blockchain.resolve_conflicts()

            if replaced:
                response = {
                    'message': 'Our chain was replaced',
                    'new_chain': self.blockchain.chain
                }
            else:
                response = {
                    'message': 'Our chain is authoritative',
                    'chain': self.blockchain.chain
                }

            return jsonify(response), 200

        def job_node():
            while True:
                print(44444444444)
                try:
                    requests.get(f'http://{self.my_ip}/nodes/getmyip', verify=False).json()
                    print(self.my_ip)
                except:
                    pass
                time.sleep(5)


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


