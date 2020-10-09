import pickle
import zlib
import time
from os import makedirs
from os.path import exists
import requests
import json

rpc_id = 0


def exist_file(file):
    return exists(file)

def save_to_file(file, data):
    while True:
        try:
            with open(file, 'wb') as f:
                f.write(zlib.compress(pickle.dumps(data, pickle.HIGHEST_PROTOCOL), 9))
                break
        except Exception as e:
            if 'No such file or directory' in e.args:
                makedirs('/'.join(file.split('/')[:-1]))
            else:
                print(e, "save_to_file")

            time.sleep(0.1)

def load_from_file(file):
    while True:
        try:
            with open(file, 'rb') as f:
                return pickle.loads(zlib.decompress(f.read()))
        except Exception as e:
            print(e, file, "load_from_file")
            if 'Error -3 while decompressing data: incorrect header check' in e.args:
                return {"error": 'Error -3 while decompressing data: incorrect header check'}
            time.sleep(0.1)

def send_request(url, method, data=[]):
    global rpc_id
    rpc_id += 1
    responce = requests.post(url=url,
                             data=json.dumps({
                                 "jsonrpc": "2.0",
                                 "id": rpc_id,
                                 "method": method,
                                 "params": data}),
                             headers={'content-type': 'application/json'}).json()
    if 'result' in responce:
        return responce["result"]
    else:
        return responce

def send_request_and_wait_responce(url, method, data=[]):
    id_task = send_request(url=url, method=method, data=data)
    while True:
        data = send_request(url=url, method="nodes.wait_task", data=[id_task])
        if 'error' in data:
            time.sleep(0.5)
        else:
            return data['result']


