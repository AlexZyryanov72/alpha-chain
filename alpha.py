from multiprocessing import Process, Pipe
from node import FullNode
from argparse import ArgumentParser
from miner import *
from blockchain import Blockchain
import signal
from wallets import Wallets
import psutil


def start_node(pipe_node, port):
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    node = FullNode(pipe_node, port)
    node.start()


def start_mine(miner_node, miner_address, affinity):
    signal.signal(signal.SIGINT, signal.SIG_IGN)

    proc = psutil.Process()
    proc.cpu_affinity([affinity])

    miner = Miner(miner_node, miner_address)
    miner.start()

def exit_program(signum=None, frame=None):
    import sys
    # terminate miner processes
    for miner in process_miners:
        miner.terminate()

    # send exit and wait while node end job
    pipe_node[0].send('exit')
    if pipe_node[0].recv() == 'exit_ok':
        process_node.terminate()
    sys.exit(0)

if __name__ == '__main__':
    signal.signal(signal.SIGINT, exit_program)

    wallets = Wallets()
    if not wallets.get_addresses():
        print("Список кошельков пуст. Создается новый кошелек")
        wallets.add_wallet()

    parser = ArgumentParser()
    # parser.add_argument('command', help='commands', choices=['main', 'dev', 'scissors'], nargs='?', default="main")
    parser.add_argument('-p', '--port', default=7777, type=int, help='port to listen on')
    parser.add_argument('-pl', '--pool', help='start pool for mine', action='store_const', const=True, default=False)
    parser.add_argument('-m', '--miner', help='start miner', action='store_const', const=True, default=False)
    parser.add_argument('-mn', '--miner_node', default="127.0.0.1", type=str, help='link miner with node')
    parser.add_argument('-ma', '--miner_address', default=wallets.current_address, type=str, help='address miner payment')
    parser.add_argument('-mc', '--miner_cpu', default='', type=str, help='select numbers cpu for workers')
    parser.add_argument('-c', '--console', help='input commands in command line', action='store_const',
                        const=True, default=False)

    args = parser.parse_args()
    port = args.port

    # checking parameters for correct input args
    try:
        if args.miner_cpu == '':
            miner_cpu = list(range(0, psutil.cpu_count(), 2))
        else:
            miner_cpu = list(map(int, args.miner_cpu.split(',')))
    except Exception as e:
        print(f'error: {e}')

    # for send data in process
    pipe_node = Pipe()

    # Instantiate the Blockchain
    blockchain = Blockchain()

    # Запускаем ноду
    process_node = Process(target=start_node, args=(pipe_node[1], port,))
    process_node.start()

    # Запускаем майнинг
    if args.miner:
        process_miners = []
        for i in range(len(miner_cpu)):
            process_miners.append(Process(target=start_mine, args=(f'{args.miner_node}:{args.port}',
                                                                   args.miner_address,
                                                                   miner_cpu[i])))
            process_miners[i].start()
            time.sleep(1)
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

    while True:
        time.sleep(1)
