from flask import Flask, jsonify, request
from flask_jsonrpc import JSONRPC
import json
from blockchain import Blockchain
import time
import sys
from os import urandom
import requests
from threading import Thread
import utils


chain_save_dir = 'data/chain/'
class Task(Thread):
    def __init__(self, node, task):
        super().__init__()
        self.node = node
        self.task = task

    def get_len_chain(self):
        while True:
            if self.node.sync_node:
                self.task['result'] = self.node.blockchain.len_chain
                return
            time.sleep(0.1)

    def get_new_job(self):
        while True:
            if self.node.sync_node:
                self.task['result'] = self.node.blockchain.new_block()
                return
            time.sleep(0.1)

    def set_proof_block(self):
        if self.node.sync_node:
            self.node.set_sync_node(False)
            self.node.blockchain.chain.append(self.task['data'])
            self.task['result'] = []
            self.node.save_blockchain()
            self.node.set_sync_node(True)

    def run(self):
        if self.task['method'] == "get_len_chain":
            self.get_len_chain()
        elif self.task['method'] == "get_new_job":
            self.get_new_job()
        elif self.task['method'] == "set_proof_block":
            self.set_proof_block()


class FullNode:
    def __init__(self, pipe_node, port):
        self.DEFAULT_NODES = ("127.0.0.1:7777", "127.0.0.1:7778",)
        self.pipe_node = pipe_node
        self.sync = False
        self.port = port
        self.blockchain = Blockchain()
        self.nodes = set()
        self.my_ip = 0
        self.rpc_id = 0
        self.task_queue = {}

    def set_sync_node(self, state):
        self.sync = state

    @property
    def sync_node(self):
        return self.sync


    def load_all_nodes(self):
        if not self.nodes:
            self.nodes = set(self.DEFAULT_NODES)

        for node in self.nodes.copy():
            try:
                nodes = utils.send_request(url=f'http://{node}/api', method="nodes.getnodes")
                self.nodes.update(set(nodes))
            except Exception:
                pass # Node not connect

    def register_node(self):
        for node in self.nodes:
            try:
                if self.my_ip == 0:
                    self.my_ip = utils.send_request(url=f'http://{node}/api', method="nodes.getmyip")
                    self.my_ip = f'{self.my_ip}:{self.port}'
                utils.send_request(url=f'http://{node}/api', method="nodes.register_node", data=[self.my_ip])
            except Exception:
                pass #Node not connect

    def load_blockchain(self):
        self.set_sync_node(False)
        chain = []
        index_file = 0
        while utils.exist_file(f'{chain_save_dir}{str(index_file)}.dat'):
            data = utils.load_from_file(f'{chain_save_dir}{str(index_file)}.dat')
            chain.extend(data)
            index_file += 1
        self.blockchain.chain = chain
        self.set_sync_node(True)

    def save_blockchain(self):
        for index_100 in range(self.blockchain.len_chain // 100 + 1):
            utils.save_to_file(f'{chain_save_dir}{str(index_100)}.dat',
                               self.blockchain.chain[index_100*100:index_100*100+100])

    def update_blockchain(self):
        for node in self.nodes:
            try:
                len_chain = utils.send_request_and_wait_responce(url=f'http://{node}/api',
                                                               method='nodes.get_len_chain')
                if self.blockchain.len_chain < len_chain:
                    new_chain = utils.send_request_and_wait_responce(url=f'http://{node}/api',
                                                                     method='nodes.get_chain')
                    if self.blockchain.valid_chain(new_chain):
                        self.blockchain.chain = new_chain
                        self.save_blockchain(self.blockchain)
            except Exception:
                pass #Node not connect or incorrect data

    def create_task(self, method, data=[]):
        while True:
            id = str(urandom(32).hex())
            if id not in self.task_queue.keys():
                break
        self.task_queue[id] = {"method": method,
                              "data": data}
        return id

    def start(self):
        # Instantiate the Node
        app = Flask(__name__)
        # Flask-JSONRPC
        jsonrpc = JSONRPC(app, '/api', enable_web_browsable_api=True)

        @jsonrpc.method('nodes.getnodes')
        def get_nodes() -> list:
            return list(self.nodes)

        @jsonrpc.method('nodes.getmyip')
        def get_myip() -> str:
            return request.remote_addr

        @jsonrpc.method('nodes.register_node')
        def register_node(node_ip: str):
            self.nodes.add(node_ip)

        @jsonrpc.method('nodes.transactions_new')
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

        @jsonrpc.method('nodes.get_len_chain')
        def get_len_chain() -> str:
            return self.create_task(method='get_len_chain')


        @jsonrpc.method('nodes.get_chain')
        def get_chain() -> str:
            return self.create_task(method='get_chain')
            #return self.blockchain.chain

        @jsonrpc.method('nodes.get_new_job')
        def get_new_job() -> str:
            return self.create_task(method='get_new_job')


        @jsonrpc.method('nodes.set_proof_block')
        def set_proof_block(block:dict) -> str:
            return self.create_task(method='set_proof_block', data=block)


        @jsonrpc.method('nodes.wait_task')
        def wait_task(id_task:str) -> dict:
            if 'result' in self.task_queue[id_task].keys():
                return {'result': self.task_queue[id_task]['result']}
            else:
                return {'error': 'data not ready yet'}

        def job_node():
            print(666666666666666666666666666666666666666666666666666666666666666666666666666666666)
            self.load_blockchain()
            print(len(self.blockchain.chain), self.blockchain.len_chain)
            print(6666666666666666666666666666666666777777777777777777777777777777777777777777777777)

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

        def worker_node():
            while True:
                for task in self.task_queue.copy().keys():
                    self.task_queue[task]['tread'] = Task(self, self.task_queue[task])
                    self.task_queue[task]['tread'].start()

                    # Запускаем ноду
        job_node = Thread(target=job_node)
        job_node.start()

        # run worker for tasks
        worker_node = Thread(target=worker_node)
        worker_node.start()



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


