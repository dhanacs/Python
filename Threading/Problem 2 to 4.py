import threading
from collections import deque

class Queue2:
    locks:dict
    lock:threading.Lock
    queues:dict

    def __init__(self):
        self.queues = {}
        self.locks = {}
        self.lock = threading.Lock()

    def publish(self, topic, message) -> None:
        # lock queue creation
        with self.lock:
            if topic not in self.queues:
                self.queues[topic] = deque()
                self.locks[topic] = threading.Lock()

        with self.locks[topic]:
            self.queues[topic].append(message)

    def consume(self, topic) -> str | None:
        if topic not in self.queues:
            return None

        with self.locks[topic]:
            if len(self.queues[topic]) > 0:
                return self.queues[topic].popleft()
            return None

if __name__ == "__main__":
    q = Queue2()
    q.publish("a", "1"); q.publish("b", "2"); q.publish("a", "3")
    print("message =", q.consume("a"))  # → "1"
    print("message =", q.consume("a"))  # → "3"
    print("message =", q.consume("b"))  # → "2"
    print("message =", q.consume("c"))  # → None