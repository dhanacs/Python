import threading
from collections import deque

class Queue1:
    q:deque
    lock:threading.Lock

    def __init__(self):
        self.q = deque()
        self.lock = threading.Lock()

    def publish(self, message) -> None:
        with self.lock:
            self.q.append(message)

    def consume(self) -> str | None:
        with self.lock:
            if len(self.q) == 0:
                return None
            else:
                return self.q.popleft()

if __name__ == "__main__":
    q = Queue1()
    q.publish("a"); q.publish("b"); q.publish("c")
    print("message =", q.consume())  # → "a"
    print("message =", q.consume())  # → "b"
    print("message =", q.consume())  # → "c"
    print("message =", q.consume())  # → None