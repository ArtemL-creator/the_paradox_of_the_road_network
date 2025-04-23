from sim_queue import Queue

class Lane:
    def __init__(self, *, lane_id: int, car_queue_size: int):
        self.lane_id = lane_id
        self.queue = Queue(car_queue_size) # Очередь для автомобилей на этой полосе
        self.is_blocked = False # Признак блокировки полосы

    def block(self):
        self.is_blocked = True

    def unblock(self):
        self.is_blocked = False

    def __str__(self):
        status = 'blocked' if self.is_blocked else 'open'
        return f'Lane {self.lane_id} ({status})'