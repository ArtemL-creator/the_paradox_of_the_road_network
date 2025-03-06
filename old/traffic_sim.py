import random
import math
import threading
import my_queue
from PyQt6 import QtWidgets, uic

Form, Window = uic.loadUiType("traffic.ui")

# Классы для моделирования
class Node:
    def __init__(self, id_str, simulation):
        self.node_name = id_str
        self.x = 0
        self.y = 0
        self.car = None
        self.simulation = simulation

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
            # parkingLot.enqueue(self.car)  # Здесь парковка не реализована
            self.car = None

    def dispatch(self):
        if self.car:
            next_link = self.car.route.directions.get(self.node_name)  # найти следующий путь
            if next_link.car_q_len == 0 or next_link.car_q_last().progress >= self.simulation.car_length:
                self.car.progress = 0
                self.car.avatar.setAttribute("cx", self.x)
                self.car.avatar.setAttribute("cy", self.y)
                next_link.car_q_enqueue(self.car)
                next_link.update_speed()
                self.car = None


class Link:
    def __init__(self, id_str, o_node, d_node, simulation):
        self.id = id_str
        self.origin_node = o_node
        self.destination_node = d_node
        self.simulation = simulation
        self.open_to_traffic = True
        self.car_queue = queue.Queue(simulation.car_queue_size)
        self.path_length = 0  # Пример
        self.speed = simulation.speed_limit
        self.travel_time = self.path_length / self.speed

    def update_speed(self):
        self.speed = self.simulation.speed_limit
        self.travel_time = self.path_length / self.speed

    def drive(self):
        if self.car_queue.length() > 0:
            first_car = self.car_queue.peek(0)  # Доступ к первому элементу в очереди
            first_car.past_progress = first_car.progress
            first_car.progress = min(self.path_length, first_car.progress + self.speed)
            first_car.odometer += first_car.progress - first_car.past_progress
            car_xy = self.get_car_xy(first_car.progress)
            first_car.avatar.setAttribute("cx", car_xy.x)
            first_car.avatar.setAttribute("cy", car_xy.y)

    def get_car_xy(self, progress):
        return self.simulation.svg_path.get_point_at_length(progress)


class Route:
    def __init__(self, simulation):
        self.simulation = simulation
        self.label = ""
        self.paint_color = None
        self.directions = {"orig": None, "south": None, "north": None, "dest": None}
        self.itinerary = []
        self.route_length = 0
        self.travel_time = 0

    def calc_route_length(self):
        """Вычисление длины маршрута."""
        self.route_length = sum(link.path_length for link in self.itinerary)

    def calc_travel_time(self):
        """Вычисление времени проезда по маршруту."""
        self.travel_time = sum(link.travel_time for link in self.itinerary)


class TrafficSimulation:
    def __init__(self):
        self.model_state = "stopped"
        self.global_clock = 0
        self.next_departure = 0
        self.launch_rate = 0.55
        self.max_cars = float('inf')
        self.bridge_blocked = False
        self.car_queue_size = 50
        self.speed_limit = 3
        self.launch_timing = "poisson"
        self.launch_timer = self.poisson
        self.routing_mode = "random"
        self.selection_method = "minimum"
        self.car_array = []
        self.parking_lot = queue.Queue(self.car_queue_size)

        self.orig = Node("orig", self)
        self.dest = Node("dest", self)
        self.south = Node("south", self)
        self.north = Node("north", self)
        self.a_link = Link("a", self.orig, self.south, self)
        self.b_link = Link("b", self.north, self.dest, self)

    def go_stop_button(self):
        if self.model_state == "stopped":
            self.model_state = "running"
            animate()
        elif self.model_state == "running":
            self.model_state = "stopping"
            self.model_state = "stopped"

    def reset_model(self):
        links_and_nodes = [self.a_link, self.b_link, self.north, self.south, self.orig, self.dest]
        for link_or_node in links_and_nodes:
            link_or_node.evacuate()

        self.global_clock = 0
        self.next_departure = 0

    def set_max_cars(self):
        self.max_cars = 100


    def launch_car(self):
        if self.orig.has_room() and self.global_clock >= self.next_departure:
            next_car = self.parking_lot.dequeue()  # Получаем машину из очереди parking_lot
            next_car.depart_time = self.global_clock
            next_car.route = self.choose_route()
            next_car.avatar.setAttribute("fill", next_car.route.paint_color)
            self.orig.accept(next_car)
            next_car.avatar.setAttribute("display", "block")
            self.next_departure = self.global_clock + self.launch_timer(self.launch_rate)

    def step(self):
        if self.model_state == "running":
            self.global_clock += self.speed_limit
            self.launch_car()

    def choose_route(self):
        available_routes = [self.a_link, self.b_link] if not self.bridge_blocked else [self.a_link]
        if self.routing_mode == "random":
            return random.choice(available_routes)
        elif self.routing_mode == "selfish":
            return min(available_routes, key=lambda route: route.travel_time)
        elif self.routing_mode == "probabilistic":
            return random.choices(available_routes, weights=[1/route.travel_time for route in available_routes])[0]

    def poisson(self, lambda_):
        return -math.log(1 - random.random()) / lambda_

    def update_simulation(self):
        if self.model_state == "running":
            self.step()


class Dashboard:
    def __init__(self, simulation):
        self.simulation = simulation
        self.counts = {"Ab": 0, "aB": 0, "AB": 0, "ab": 0, "total": 0}
        self.times = {"Ab": 0, "aB": 0, "AB": 0, "ab": 0, "total": 0}

    def record_departure(self):
        self.counts["total"] += 1

    def record_arrival(self, car):
        elapsed = (self.simulation.global_clock - car.depart_time) / self.simulation.speed_limit
        self.times["total"] += elapsed

    def update_readouts(self):
        print(f"Counts: {self.counts}")
        print(f"Times: {self.times}")


def animate():
    simulation.update_simulation()


# Инициализация и запуск
simulation = TrafficSimulation()
dashboard = Dashboard(simulation)
simulation.launch_car()
