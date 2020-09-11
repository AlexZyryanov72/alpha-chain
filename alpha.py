import sys
from multiprocessing import Process, Pipe
from node import FullNode

from miner import *
from blockchain import Blockchain


def start_node(port):
    node = FullNode(port)
    node.start()


def start_mine(pipe_miner_to_node, blockchain):
    miner = Miner(pipe_miner_to_node, blockchain)
    miner.start()


if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    # parser.add_argument('command', help='commands', choices=['main', 'dev', 'scissors'], nargs='?', default="main")
    parser.add_argument('-p', '--port', default=7777, type=int, help='port to listen on')
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
    process_node = Process(target=start_node, args=(port,))
    process_node.start()

    # Запускаем майнинг
    if args.miner:
        current_address = wallets.current_address
        process_miner = Process(target=start_mine, args=(pipe_miner_to_node, blockchain,))
        process_miner.start()

    if args.console:
        while True:
            command = input('> ').lower().split(" ")
            if "exit" in command:
                if args.miner:
                    process_miner.terminate()
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
