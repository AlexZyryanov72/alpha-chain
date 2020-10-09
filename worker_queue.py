from threading import Thread
import time
from os import urandom

class Task(Thread):
    def __init__(self, node, task):
        super().__init__()
        self.node = node
        self.task = task

    def run(self):
        self.task['result'] = self.task['method'](self.task['data'])
        if self.task['result'] is None:
            self.task['result'] = []

class WorkerQueue(Thread):
    def __init__(self):
        super().__init__()
        self.task_queue = {}

    def run(self):
        while True:
            for task in self.task_queue.copy().keys():
                if 'tread' not in self.task_queue[task].keys():
                    self.task_queue[task]['tread'] = Task(self, self.task_queue[task])
                    self.task_queue[task]['tread'].start()
            time.sleep(0.1)

    def append(self, callback, data=[]):
        while True:
            id = str(urandom(32).hex())
            if id not in self.task_queue.keys():
                break
        self.task_queue[id] = {"method": callback,
                               "data": data}
        return id

    def pop(self, id):
        self.task_queue.pop(id)

    def fetch_job(self, id):
        if id not in self.task_queue:
            return {'error': f'data with id: {id} not found', 'is_finished': False}
        if 'result' in self.task_queue[id].keys():
            return {'result': self.task_queue.pop(id)['result'], 'is_finished': True}
        else:
            return {'error': 'data not ready', 'is_finished': False}