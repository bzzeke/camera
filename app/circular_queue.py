import queue

class CircularQueue:

    max_size = 0
    queue = None
    drop = True

    def __init__(self, max_size):
        self.queue = queue.Queue()
        self.max_size = max_size

    def put(self,data):
        while self.queue.qsize() > self.max_size and self.drop:
            self.queue.get()

        self.queue.put(data)
        return True

    def size(self):
        return self.queue.qsize()

    def get(self):
        data = None
        try:
            data = self.queue.get(block=False)
        except queue.Empty:
            pass

        return data
