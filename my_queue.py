class Queue:
    def __init__(self, max_items):
        super().__init__()
        self.n = max_items
        self.q = [None] * self.n  # Инициализация массива фиксированной длины
        self.head = 0
        self.len = 0

    def length(self):
        return self.len

    def q_is_empty(self):
        return self.len == 0
    def enqueue(self, item):
        if self.len < self.n:  # Проверка, не превышает ли длина очереди максимальный размер
            self.q[(self.head + self.len) % self.n] = item
            self.len += 1
        else:
            raise Exception("Queue is full")

    def dequeue(self):
        if self.len == 0:  # Проверка, не пуста ли очередь
            raise Exception("Queue is empty")
        item = self.q[self.head]
        self.len -= 1
        self.head = (self.head + 1) % self.n
        return item

    def first(self):
        if self.len == 0:  # Проверка, не пуста ли очередь
            raise Exception("Queue is empty")
        return self.q[self.head]

    def last(self):
        if self.len == 0:  # Проверка, не пуста ли очередь
            raise Exception("Queue is empty")
        return self.q[(self.head + self.len - 1) % self.n]

    def peek(self, idx):
        if idx < 0 or idx >= self.len:  # Проверка корректности индекса
            raise IndexError("Index out of range")
        return self.q[(self.head + idx) % self.n]
