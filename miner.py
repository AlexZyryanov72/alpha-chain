import time
from blockchain import Blockchain
from utils import send_request_and_wait_responce



class Miner:
    def __init__(self, connect_address_node, address_payment, ):
        self.address_payment = address_payment
        self.connect_address_node = connect_address_node
        self.blockchain = Blockchain()
        self.rpc_id = 0
        self.headers = {'content-type': 'application/json'}

    def payload(self, method, params):
        self.rpc_id += 1
        return {
            "jsonrpc": "2.0",
            "id": self.rpc_id,
            "method": method,
            "params": params}

    def start(self):
        while True:
            # send request for new job
            while True:
                try:
                    block = send_request_and_wait_responce(url=f'http://{self.connect_address_node}/api',
                                                           method='nodes.get_new_job')
                    break
                except Exception:
                    print('Not connect node mining for new job')
                time.sleep(2)

            block['transactions'].append(self.blockchain.new_transaction(sender="0", recipient=self.address_payment,
                                                                         amount=self.blockchain.miner_amount_payment(block)))
            self.proof_of_work(block)
            response = {
                'message': "New Block Forged",
                'time': time.ctime(block['timestamp']),
                'index': block['index'],
                'difficulty': block['difficulty'],
                'proof': block['proof'],
                'previous_hash': block['previous_hash'],
                'transactions': block['transactions']
            }
            print(response)
            # send request proof block
            while True:
                try:
                    send_request_and_wait_responce(url=f'http://{self.connect_address_node}/api',
                                                   method='nodes.set_proof_block',
                                                   data={'block': block})
                    break
                except Exception:
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
            block['proof'] = proof





