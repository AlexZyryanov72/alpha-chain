import sys
from multiprocessing import Process, Pipe
from node import FullNode
from argparse import ArgumentParser
from miner import *
from blockchain import Blockchain
import signal
from wallets import Wallets


def start_node(pipe_node, port):
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    node = FullNode(pipe_node, port)
    node.start()


def start_mine(pipe_miner, miner_node, miner_address):
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    miner = Miner(pipe_miner, miner_node, miner_address)
    miner.start()

def exit_program():
    if args.miner:
        pipe_miner[0].send('exit')

    # send exit and wait while node end job
    pipe_node[0].send('exit')
    if pipe_node[0].recv() == 'exit_ok':
        process_node.terminate()
    sys.exit(0)

def handler(signum, frame):
    exit_program()


if __name__ == '__main__':
    signal.signal(signal.SIGINT, handler)

    wallets = Wallets()
    if not wallets.get_addresses():
        print("Список кошельков пуст. Создается новый кошелек")
        wallets.add_wallet()

    parser = ArgumentParser()
    # parser.add_argument('command', help='commands', choices=['main', 'dev', 'scissors'], nargs='?', default="main")
    parser.add_argument('-p', '--port', default=7777, type=int, help='port to listen on')
    parser.add_argument('-m', '--miner', help='start miner', action='store_const', const=True, default=False)
    parser.add_argument('-mn', '--miner_node', default="127.0.0.1", type=str, help='link miner with node')
    parser.add_argument('-ma', '--miner_address', default=wallets.current_address, type=str, help='address miner payment')
    parser.add_argument('-c', '--console', help='input commands in command line', action='store_const',
                        const=True, default=False)

    args = parser.parse_args()
    port = args.port

    # for send data in process
    pipe_miner = Pipe()
    pipe_node = Pipe()

    # Instantiate the Blockchain
    blockchain = Blockchain()

    # Запускаем ноду
    process_node = Process(target=start_node, args=(pipe_node[1], port,))
    process_node.start()

    # Запускаем майнинг
    if args.miner:
        process_miner = Process(target=start_mine, args=(pipe_miner[1],
                                                         f'{args.miner_node}:{args.port}',
                                                         args.miner_address))
        process_miner.start()

    if args.console:
        while True:
            command = input('> ').lower().split(" ")
            if "exit" in command:
                exit_program()
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
                    print('OK')
                else:
                    print("Кошелек с таким адресом не зарегестрирован")
            elif "len" in command:
                print(len(blockchain.chain))
            else:
                print("Unknown command")
