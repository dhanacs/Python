import uuid
import time
import threading

from collections import deque
from dataclasses import dataclass, field

# dataclass reduces code
@dataclass
class Message:
    payload:str
    id:str = field(default_factory=lambda: uuid.uuid4().hex)
    enqueued_at:float = field(default_factory=time.monotonic)

class Queue5:
    locks:dict
    lock:threading.Lock
    queues:dict

    def __init__(self):
        self.queues = {}
        self.locks = {}
        self.lock = threading.Lock()

    def publish(self, topic, payload) -> None:
        # lock queue creation
        with self.lock:
            if topic not in self.queues:
                self.queues[topic] = deque()
                self.locks[topic] = threading.Lock()

        with self.locks[topic]:
            message = Message(payload)
            self.queues[topic].append(message)
            return message.id

    def consume(self, topic) -> Message | None:
        if topic not in self.queues:
            return None

        with self.locks[topic]:
            if len(self.queues[topic]) > 0:
                return self.queues[topic].popleft()
            return None

if __name__ == "__main__":
    q = Queue5()
    msg_id = q.publish("t", "hello")   # → "3f8a…c1"
    m = q.consume("t")                 # → Message(id="3f8a…c1", payload="hello", …)
    assert m.id == msg_id and m.payload == "hello"