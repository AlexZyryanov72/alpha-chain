import time
import requests


class FullNode:
    DEFAULT_NODES = ("127.0.0.1:5000", "127.0.0.1:5001",)
    def __init__(self, pipe_node_miner, blockchain, port):
        self.pipe_node_to_miner = pipe_node_miner
        self.blockchain = blockchain
        self.port = port
        self.nodes = set()
        self.my_ip = ""
        self.run_node()

    def start(self):
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
                if not self.my_ip:
                    self.my_ip = requests.get(f'http://{node}/nodes/getmyip', verify=False).json()
                    self.my_ip = f'{self.my_ip}:{self.port}'
                response = requests.post(f'http://{node}/nodes/setmyip', json={"my_ip": self.my_ip} , verify=False)
                self.nodes.update(set(response.json()))
            except:
                pass

    def run_node(self):
        self.load_all_nodes()
        self.register_node()
        print(self.nodes)