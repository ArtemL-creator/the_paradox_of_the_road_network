import random
import math
from typing import List, Optional

from my_queue import Queue

step_counter = 0
animation_timer = None
model_state = "running"
bridge_blocked = False
routing_mode = "selfish"
speed_mode = "theoretical"
selection_method = "minimum"
launch_timing = "poisson"
launch_timer = lambda rate: poisson(rate)
launch_rate = 0.55
global_clock = 0
next_departure = 0
max_cars = 1000
car_radius = 3
car_length = 2 * car_radius
total_path_length = 1620
car_queue_size = (total_path_length // car_length) + 10
car_array: List[Optional["Car"]] = [None] * car_queue_size
speed_limit = 3
congestion_coef = 0.1
quickest_trip = 582 / speed_limit

route_stats = {
    "Ab": {"total_time": 0, "car_count": 0},
    "aB": {"total_time": 0, "car_count": 0},
    "AB": {"total_time": 0, "car_count": 0},
    "ab": {"total_time": 0, "car_count": 0},
}


class Car:
    def __init__(self, serial_number):
        self.serial_number = serial_number
        self.progress = 0
        self.past_progress = 0
        self.depart_time = 0
        self.arrive_time = 0
        self.route = None
        self.odometer = 0
        self.radius = car_radius
        # Добавляем машину в очередь парковки
        parking_lot.car_queue.enqueue(self)


class Dashboard:
    def __init__(self):
        self.departure_count = 0
        self.arrival_count = 0
        self.counts = {"Ab": 0, "aB": 0, "AB": 0, "ab": 0, "total": 0}
        self.times = {"Ab": 0, "aB": 0, "AB": 0, "ab": 0, "total": 0}

    def record_departure(self):
        self.departure_count += 1

    def record_arrival(self, car):
        elapsed = (global_clock - car.depart_time) / speed_limit
        route_code = car.route.label
        self.counts[route_code] += 1
        self.counts["total"] += 1
        self.times[route_code] += elapsed
        self.times["total"] += elapsed
        self.update_readouts()

    def update_readouts(self):
        for ct in self.counts:
            # Пока просто выводим значения для проверки.
            print(f"Route {ct}: Count={self.counts[ct]}")

        for tm in self.times:
            if self.counts[tm] == 0:
                print(f"Route {tm}: Time=--")
            else:
                avg_time = (self.times[tm] / self.counts[tm]) / quickest_trip
                print(f"Route {tm}: Avg Time={avg_time:.3f}")

    def reset(self):
        self.departure_count = 0
        self.arrival_count = 0
        for ct in self.counts:
            self.counts[ct] = 0
        for tm in self.times:
            self.times[tm] = 0
        self.update_readouts()


class Route:
    def __init__(self, label):
        self.label = label
        self.paint_color = None
        self.directions = {"orig": None, "south": None, "north": None, "dest": None}
        self.itinerary = []
        self.route_length = 0
        self.travel_time = 0
        self.current_travel_time = 0
        self.chooser_val = 0

    def calc_route_length(self):
        self.route_length = sum(link.path_length for link in self.itinerary)

    def calc_travel_time(self):
        if speed_mode == "theoretical":
            self.calc_travel_time_theoretical()
        elif speed_mode == "actual":
            self.calc_travel_time_actual()
        else:
            self.calc_travel_time_historical()

    def calc_travel_time_theoretical(self):
        self.travel_time = sum(link.travel_time for link in self.itinerary)

    def calc_travel_time_actual(self):
        total_time = 0
        car_count = 0

        for car in car_array:
            if car and car.route == self and car.odometer > 0:
                velocity = (car.odometer / (global_clock - car.depart_time)) * speed_limit
                travel_time = self.route_length / velocity
                total_time += travel_time
                car_count += 1

        if car_count == 0:
            self.travel_time = self.route_length / speed_limit
        else:
            self.travel_time = total_time / car_count

    def calc_travel_time_historical(self):
        if Dashboard().counts[self.label] == 0:
            self.travel_time = self.route_length / speed_limit
        else:
            self.travel_time = Dashboard().times[self.label] / Dashboard().counts[self.label]


class Node:
    def __init__(self, id_str):
        self.node_name = id_str
        self.car = None

    def has_room(self):
        """Проверяет, есть ли место для новой машины."""
        return self.car is None

    def accept(self, car):
        """Принимает машину в узел."""
        self.car = car

    def evacuate(self):
        """Очищает узел, если нажата кнопка сброса."""
        if self.car:
            self.car.reset()
            parking_lot.car_queue.enqueue(self.car)
            self.car = None

    def dispatch(self):
        """Отправляет машину на следующий участок пути."""
        if self.car:
            if self.node_name == "dest":
                try:
                    print(
                        f"Attempting to park car {self.car.serial_number}. Current parking lot length: {parking_lot.car_queue.length()}")
                except AttributeError:
                    print(
                        f"Car object {self.car} does not have an 'id' attribute. Debugging information: {vars(self.car)}")
                park_car(self.car)
                self.car = None
                return
            # Попытка получить следующий линк
            next_link = self.car.route.directions.get(self.node_name)
            if not next_link:
                print(f"Node name: {self.node_name}")
                print(f"Car: {self.car}")
                print(f"Directions: {self.car.route.directions}")
                raise ValueError(f"No link found for node {self.node_name} in directions.")

            if not hasattr(next_link, 'car_queue'):
                raise AttributeError(f"Next link {next_link} has no attribute 'car_queue'.")
            if not isinstance(next_link.car_queue, Queue):
                raise TypeError(f"Expected car_queue to be of type Queue, got {type(next_link.car_queue)} instead.")
            # Проверяем, может ли машина двигаться дальше

            if next_link.car_queue.length() == 0:
                print("Queue is empty, enqueuing car.")
                self.car.progress = 0
                next_link.car_queue.enqueue(self.car)
                next_link.update_speed()
                self.car = None
            else:
                last_car = next_link.car_queue.last()
                print(f"Last car in queue progress: {last_car.progress}")
                if last_car.progress >= car_length:
                    print("Enough space in the queue, enqueuing car.")
                    self.car.progress = 0
                    next_link.car_queue.enqueue(self.car)
                    next_link.update_speed()
                    self.car = None
                else:
                    print("Not enough space in the queue.")


class Link:
    def __init__(self, id_str, origin, destination, path_length):
        self.id = id_str
        self.origin_node = origin
        self.destination_node = destination
        self.open_to_traffic = True
        self.path_length = path_length
        self.speed = speed_limit
        self.travel_time = self.path_length / self.speed
        self.car_queue = Queue(car_queue_size)
        self.occupancy = self.car_queue.length()
        self.total_travel_time = 0
        self.car_count = 0

    def update_speed(self):
        self.speed = speed_limit
        self.travel_time = self.path_length / self.speed

    def drive(self):
        """Перемещает машины по пути."""
        if self.car_queue.length() <= 0:
            return

        first_car = self.car_queue.first()
        first_car.past_progress = first_car.progress
        first_car.progress = min(self.path_length, first_car.progress + self.speed)
        first_car.odometer += first_car.progress - first_car.past_progress

        # Обработка последующих машин
        for i in range(1, self.car_queue.length()):
            leader = self.car_queue.peek(i - 1)
            follower = self.car_queue.peek(i)
            follower.past_progress = follower.progress
            follower.progress = min(follower.progress + self.speed, leader.progress - car_length)
            follower.odometer += follower.progress - follower.past_progress

        # Если первая машина достигла конца пути
        if first_car.progress >= self.path_length and self.destination_node.has_room():
            self.destination_node.accept(self.car_queue.dequeue())
            self.update_speed()

    def evacuate(self):
        """Очищает путь, если нажата кнопка сброса."""
        while not self.car_queue.length() > 0:
            car = self.car_queue.dequeue()
            car.reset()
            parking_lot.car_queue.enqueue(car)
        self.update_speed()


def coin_flip():
    """Возвращает True или False с равной вероятностью."""
    return random.random() < 0.5


def poisson(lambda_):
    """Генерирует случайное значение из распределения Пуассона с параметром lambda."""
    return -math.log(1 - random.random()) / lambda_


def uniform(lambda_):
    """Генерирует случайное значение из равномерного распределения в диапазоне [0, 2/lambda]."""
    return random.random() * 2 / lambda_


def periodic(lambda_):
    """Возвращает периодическое значение на основе параметра lambda."""
    return 1 / lambda_


def choose_route():
    """Выбирает маршрут в зависимости от состояния моста и режима маршрутизации."""
    if bridge_blocked:
        available_routes = [Ab, aB]
    else:
        available_routes = [Ab, aB, AB, ab]

    if routing_mode == "random":
        return chooser_random(available_routes)
    else:  # routing_mode == "selfish"
        for route in available_routes:
            route.calc_travel_time()

        if selection_method == "minimum":
            return chooser_min(available_routes)
        else:  # selection_method == "probabilistic"
            return chooser_probabilistic(available_routes)


# Пример функций chooser, которые ранее были написаны
def chooser_random(route_list):
    """Возвращает случайный маршрут из списка."""
    return random.choice(route_list)


def chooser_min(route_list):
    """Выбирает маршрут с минимальным временем путешествия."""
    min_val = min(route_list, key=lambda route: route.travel_time).travel_time
    min_routes = [route for route in route_list if route.travel_time == min_val]
    return random.choice(min_routes) if len(min_routes) > 1 else min_routes[0]


def chooser_probabilistic(route_list):
    """Выбирает маршрут пропорционально времени путешествия."""
    total_weight = sum(1 / route.travel_time for route in route_list)
    probabilities = [(1 / route.travel_time) / total_weight for route in route_list]
    r = random.random()
    cumulative = 0
    for route, prob in zip(route_list, probabilities):
        cumulative += prob
        if r <= cumulative:
            return route


def make_cars(n):
    """Создает автомобили и добавляет их в массив."""
    for i in range(n):
        car = Car(i)
        car.arrive_time = global_clock
        car_array[i] = car


def init():
    """Инициализация модели."""
    make_cars(car_queue_size)
    global global_clock
    global_clock = 0
    A_link.update_speed()
    a_link.update_speed()
    B_link.update_speed()
    b_link.update_speed()
    ns_link.update_speed()
    sn_link.update_speed()


def save_stats():
    """Выводит статистику маршрутов."""
    print("\nRoute Statistics:")
    for route, stats in route_stats.items():
        if stats['car_count'] > 0:
            average_time = stats['total_time'] / stats['car_count']
            print(f"Route {route}: Average time = {average_time:.2f}")
        else:
            print(f"Route {route}: No cars traveled.")


def launch_car():
    """Запускает машину из парковки, если условия позволяют."""
    global next_departure
    if (
            orig.has_room()
            and global_clock >= next_departure
            and model_state == "running"
            and parking_lot.car_queue.length() > 0
    ):
        next_car = parking_lot.car_queue.dequeue()
        next_car.depart_time = global_clock
        next_car.route = choose_route()
        orig.accept(next_car)
        dashboard.record_departure()
        next_departure = global_clock + launch_timer(launch_rate / speed_limit)


def park_car(car):
    """Обрабатывает парковку машины."""
    global global_clock
    car.arrive_time = global_clock
    travel_time = car.arrive_time - car.depart_time
    route_name = car.route.label

    # Обновляем статистику маршрута
    if route_name not in route_stats:
        route_stats[route_name] = {"total_time": 0, "car_count": 0}
    route_stats[route_name]["total_time"] += travel_time
    route_stats[route_name]["car_count"] += 1

    # Проверяем место в парковке
    if parking_lot.car_queue.length() < car_queue_size:
        parking_lot.car_queue.enqueue(car)
        print(f"Car {car.serial_number} parked. Route: {route_name}, Travel time: {travel_time}")
    else:
        print(f"Parking lot is full. Car {car.serial_number} cannot be parked.")


def steps():
    for _ in range(car_queue_size):
        global global_clock, step_counter
        print(f"Running step {step_counter + 1}/{car_queue_size}")

        if coin_flip():
            dest.dispatch()
            b_link.drive()
            dest.dispatch()
            b_link.drive()
        else:
            dest.dispatch()
            b_link.drive()
            dest.dispatch()
            b_link.drive()

        if coin_flip():
            north.dispatch()
            a_link.drive()
            north.dispatch()
            sn_link.drive()
        else:
            north.dispatch()
            sn_link.drive()
            north.dispatch()
            a_link.drive()

        if coin_flip():
            south.dispatch()
            ns_link.drive()
            south.dispatch()
            a_link.drive()
        else:
            south.dispatch()
            a_link.drive()
            south.dispatch()
            ns_link.drive()
        launch_car()
        orig.dispatch()
        orig.dispatch()
        global_clock += speed_limit
        step_counter += 1
        check_simulation_conditions()
        # time.sleep(launch_timer(launch_rate))

def check_simulation_conditions():
    """
    Проверяет условия остановки или завершения симуляции.
    """
    global model_state, animation_timer

    if step_counter < car_queue_size:
        delay = launch_timer(launch_rate)  # Определяем задержку для следующего шага
        print(f"Next step in {delay:.2f} seconds.")
    else:
        print("Simulation completed.")


class ParkingLot(Node):
    def __init__(self, name, capacity):
        super().__init__(name)
        self.car_queue = Queue(capacity)


parking_lot = ParkingLot("parking_lot", car_queue_size)

if __name__ == '__main__':
    # Example Nodes and Links
    orig = Node("orig")
    dest = Node("dest")
    south = Node("south")
    north = Node("north")

    a_link = Link("a", orig, south, 20)
    A_link = Link("A", orig, north, 100)
    b_link = Link("b", north, dest, 20)
    B_link = Link("B", south, dest, 100)
    sn_link = Link("sn", south, north, 10)
    ns_link = Link("ns", north, south, 10)
    sn_link.open_to_traffic = True
    ns_link.open_to_traffic = True

    Ab = Route("Ab")
    Ab.directions = {
        "orig": A_link,
        "south": None,
        "north": b_link,
        "dest": parking_lot
    }
    Ab.itinerary = [A_link, b_link]
    Ab.calc_route_length()

    aB = Route("aB")
    aB.directions = {
        "orig": a_link,
        "south": B_link,
        "north": None,
        "dest": parking_lot
    }
    aB.itinerary = [a_link, B_link]
    aB.calc_route_length()

    AB = Route("AB")
    AB.directions = {
        "orig": A_link,
        "south": B_link,
        "north": ns_link,
        "dest": parking_lot
    }
    AB.itinerary = [A_link, ns_link, B_link]
    AB.calc_route_length()

    ab = Route("ab")
    ab.directions = {
        "orig": a_link,
        "south": sn_link,
        "north": b_link,
        "dest": parking_lot
    }
    ab.itinerary = [a_link, ns_link, b_link]
    ab.calc_route_length()

    dashboard = Dashboard()
    init()
    step_counter = 0
    steps()
