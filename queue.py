# Простейшая реализация очереди
class Queue:
    def __init__(self, max_size):
        self.items = []
        self.max_size = max_size

    def enqueue(self, item):
        if len(self.items) < self.max_size:
            self.items.append(item)
        else:
            print("Очередь переполнена!")

    def dequeue(self):
        return self.items.pop(0) if self.items else None

    def peek(self, index):
        return self.items[index] if index < len(self.items) else None

    @property
    def len(self):
        return len(self.items)
