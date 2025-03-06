import sys
import random
import math
from PyQt6 import QtCore, QtWidgets, uic
from PyQt6.QtCore import QTimer

# Загрузка интерфейса из файла .ui
Form, Window = uic.loadUiType("traffic.ui")

class TrafficSimulation(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.initialize_simulation()

    def setup_ui(self):
        # Инициализация пользовательского интерфейса
        self.ui = Form()
        self.ui.setupUi(self)

        # Подключение кнопок и других виджетов к обработчикам
        self.ui.startButton.clicked.connect(self.start_simulation)
        self.ui.stopButton.clicked.connect(self.stop_simulation)
        self.ui.resetButton.clicked.connect(self.reset_simulation)

        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.update_simulation)

    def initialize_simulation(self):
        # Инициализация переменных симуляции
        self.model_state = "stopped"
        self.bridge_blocked = True
        self.routing_mode = "selfish"
        self.speed_mode = "theoretical"
        self.selection_method = "minimum"
        self.launch_timing = "poisson"
        self.launch_timer = self.poisson
        self.global_clock = 0
        self.next_departure = 0
        self.max_cars = float('inf')
        self.car_radius = 3
        self.car_length = 2 * self.car_radius
        self.total_path_length = 1620
        self.car_queue_size = (self.total_path_length / self.car_length) + 10
        self.car_array = [None] * int(self.car_queue_size)
        self.speed_limit = 3
        self.launch_rate = 0.55
        self.congestion_coef = 0.55
        self.quickest_trip = 582 / self.speed_limit

        # Создание узлов сети
        self.orig = Node("orig")
        self.dest = Node("dest")
        self.south = Node("south")
        self.north = Node("north")

    def coin_flip(self):
        return random.random() < 0.5

    def poisson(self, lambda_: float) -> float:
        return -math.log(1 - random.random()) / lambda_

    def uniform(self, lambda_: float) -> float:
        return random.random() * 2 / lambda_

    def periodic(self, lambda_: float) -> float:
        return 1 / lambda_

    def start_simulation(self):
        self.model_state = "running"
        self.animation_timer.start(100)  # обновление каждую 1/10 секунды

    def stop_simulation(self):
        self.model_state = "stopping"
        self.animation_timer.stop()

    def reset_simulation(self):
        self.model_state = "stopped"
        self.global_clock = 0
        self.next_departure = 0
        self.car_array = [None] * int(self.car_queue_size)
        self.orig.reset()
        self.dest.reset()
        self.south.reset()
        self.north.reset()

    def update_simulation(self):
        if self.model_state == "running":
            self.global_clock += 1
            self.orig.dispatch()
            self.dest.dispatch()
            self.south.dispatch()
            self.north.dispatch()

class Node:
    def __init__(self, id_str):
        self.node_name = id_str
        self.x = 0  # Например, координаты на экране
        self.y = 0
        self.car = None

    def has_room(self):
        return self.car is None

    def accept(self, car):
        self.car = car

    def evacuate(self):
        if self.car:
            # Очистить визуальное представление машины
            self.car.avatar.setAttribute("display", "none")
            self.car.avatar.setAttribute("cx", 0)
            self.car.avatar.setAttribute("cy", 0)
            self.car.route = None
            self.car.progress = 0
            self.car.odometer = 0
            # parkingLot.enqueue(self.car) # Здесь парковка не реализована
            self.car = None

    def dispatch(self):
        if self.car:
            next_link = self.car.route.directions.get(self.node_name)  # найти следующий путь
            if next_link.car_q_len == 0 or next_link.car_q_last().progress >= self.car_length:
                self.car.progress = 0
                self.car.avatar.setAttribute("cx", self.x)
                self.car.avatar.setAttribute("cy", self.y)
                next_link.car_q_enqueue(self.car)
                next_link.update_speed()
                self.car = None


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = TrafficSimulation()
    window.show()
    sys.exit(app.exec())
