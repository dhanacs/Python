# custom comparator examples
# can be used in sorting and priority queues

from queue import PriorityQueue
from dataclasses import dataclass

@dataclass
class Node:
    id:int
    cost:int

    # overload < operator
    def __lt__(self, other):
        return self.cost < other.cost

if __name__ == "__main__":
    nodes = [Node(2, 73), Node(12, 19), Node(22, 21), Node(3, 10), Node(4, 3), Node(10, 33), Node(6, 45)]

    # sorted nodes
    nodes.sort()
    print("array elements")
    for node in nodes:
        print("id =", node.id, "cost =", node.cost)

    # priority queue
    q = PriorityQueue()
    for node in nodes: q.put(node)

    print()
    print("queue elements")
    while not q.empty():
        node = q.get()
        print("id =", node.id, "cost =", node.cost)
