class CircularQueue:

    max_size = 0

    def __init__(self, max_size):
        self.queue = list()
        self.max_size = max_size

    def put(self,data):
        if self.size() > self.max_size:
            self.get()

        self.queue.append(data)
        return True

    def size(self):
        return len(self.queue)

    def get(self):
        return self.queue.pop(0) if len(self.queue) > 0 else None
