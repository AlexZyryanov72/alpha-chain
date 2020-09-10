import sys
from multiprocessing import Process, Pipe
from node import FullNode
from flask import Flask, jsonify, request
from miner import *
from blockchain import Blockchain


def web(blockchain, port):
    # Instantiate the Node
    app = Flask(__name__)

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

    @app.route('/get_len_chain', methods=['GET'])
    def get_len_chain():
        return blockchain.chain[-1]['index'] + 1

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

    app.run(host='127.0.0.1', port=port)

def start_node(pipe_node_to_miner, blockchain, port):
    node = FullNode(pipe_node_to_miner, blockchain, port)
    node.start()

def start_mine(pipe_miner_to_node, blockchain):
    miner = Miner(pipe_miner_to_node, blockchain)
    miner.start()

if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    # parser.add_argument('command', help='commands', choices=['main', 'dev', 'scissors'], nargs='?', default="main")
    parser.add_argument('-p', '--port', default=7003, type=int, help='port to listen on')
    parser.add_argument('-m', '--miner', help='start miner', action='store_const', const=True, default=False)
    parser.add_argument('-nc', '--console', help='input commands in command line', action='store_const',
                        const=True, default=False)

    args = parser.parse_args()
    port = args.port

    wallets = Wallets()
    if not wallets.get_addresses():
        print("Список кошельков пуст. Создается новый кошелек")
        wallets.add_wallet()

    pipe_miner_to_node, pipe_node_to_miner = Pipe()

    # Instantiate the Blockchain
    blockchain = Blockchain()

    # Запускаем ноду
    process_node = Process(target=start_node, args=(pipe_node_to_miner, blockchain, port))
    process_node.start()

    # Запускаем майнинг
    if args.miner:
        current_address = wallets.current_address
        process_miner = Process(target=start_mine, args=(pipe_miner_to_node, blockchain, ))
        process_miner.start()


    # Запускаем сервер для приема транзакций
    process_web = Process(target=web,  args=(blockchain, port,))
    process_web.start()

    if args.console:
        while True:
            command = input('> ').lower().split(" ")
            if "exit" in command:
                if args.miner:
                    process_miner.terminate()
                process_web.terminate()
                sys.exit(0)
            elif "new_wallet" in command:
                wallets.add_wallet()
            elif "list_wallet" in command:
                print(wallets.get_addresses())
            elif "current_wallet" in command:
                print(wallets.current_address)
            elif "change_current_wallet" in command:
                addr = input('Input address wallet: ')
                if wallets.get_wallet(addr):
                    wallets.current_address = addr
                    current_address = addr
                    print('OK')
                else:
                    print("Кошелек с таким адресом не зарегестрирован")
            elif "len" in command:
                print(len(blockchain.chain))
            else:
                print("Unknown command")

