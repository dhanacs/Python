# Random numbers and uuid

import uuid
import random

if __name__ == "__main__":
    id = uuid.uuid8()
    print("uuid =", id)

    n = random.randrange(1, 100 + 1)
    print("random in [1, 100] =", n)