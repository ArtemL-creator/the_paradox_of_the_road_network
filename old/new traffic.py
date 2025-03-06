import random

from my_queue import Queue

# Simulation Initialization
global_clock = 0
speed_limit = 3
bridge_blocked = False
model_state = "running"
launch_rate = 0.55
congestion_coef = 0.1
next_departure = 0
max_cars = 10000
car_radius = 3
car_length = 2 * car_radius
total_path_length = 1620
car_queue_size = (total_path_length // car_length) + 10
car_array = [None] * car_queue_size
parking_lot = Queue(car_queue_size)
quickest_trip = 582 / speed_limit


class Car:
    def __init__(self, serial_number):
        self.serial_number = serial_number
        self.progress = 0
        self.past_progress = 0
        self.depart_time = 0
        self.arrive_time = 0
        self.route = None
        self.odometer = 0


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
        self.arrival_count += 1  # Увеличиваем счетчик прибытия
        self.update_readouts()

    def update_readouts(self):
        print("Departures:", self.departure_count)
        print("Arrivals:", self.arrival_count)
        for route, count in self.counts.items():
            avg_time = self.times[route] / count if count > 0 else 0
            print(f"{route}: {count} cars, Avg time: {avg_time:.3f}s")

    def reset(self):
        self.departure_count = 0
        self.arrival_count = 0
        for key in self.counts:
            self.counts[key] = 0
        for key in self.times:
            self.times[key] = 0
        self.update_readouts()


class Route:
    def __init__(self, label):
        self.label = label
        self.itinerary = []
        self.route_length = 0
        self.travel_time = 0

    def calc_route_length(self):
        self.route_length = sum(link.path_length for link in self.itinerary)

    def calc_travel_time(self):
        self.travel_time = sum(link.travel_time for link in self.itinerary)


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
        self.occupancy = self.car_queue.length

    def update_speed(self):
        self.speed = speed_limit - (self.occupancy * car_length * speed_limit * congestion_coef) / self.path_length
        self.travel_time = self.path_length / self.speed

    def drive(self):
        if self.car_queue.length() > 0:  # Проверяем, есть ли машины в очереди
            car = self.car_queue.first()  # Получаем первую машину в очереди
            car.past_progress = car.progress
            car.progress = min(self.path_length, car.progress + self.speed)
            car.odometer += car.progress - car.past_progress

            if car.progress >= self.path_length:  # Если машина достигла конца пути
                self.car_queue.dequeue()  # Убираем машину из очереди
                self.destination_node.accept(car)  # Отправляем машину в пункт назначения
                self.update_speed()


class Node:
    def __init__(self, id_str):
        self.id = id_str
        self.car = None

    def has_room(self):
        return self.car is None

    def accept(self, car):
        self.car = car

    def dispatch(self):
        if self.car:
            next_link = self.car.route.itinerary[0]
            if not next_link.car_queue or next_link.car_queue[-1].progress >= car_length:
                self.car.progress = 0
                next_link.car_queue.append(self.car)
                next_link.update_speed()
                self.car = None


# Create Cars
def make_cars(n):
    for i in range(n):
        car = Car(i)  # Создаем новый объект Car
        car.serial_number = i  # Присваиваем серийный номер
        parking_lot.enqueue(car)  # Добавляем машину в очередь parking_lot


# Initialize System
def init():
    make_cars(car_queue_size)
    global global_clock
    global_clock = 0


# Choose Route
def choose_route():
    available_routes = [Ab, aB, AB, ab]
    if bridge_blocked:
        available_routes = [Ab, aB]
    return random.choice(available_routes)


# Main Simulation Step
def step():
    global global_clock
    for link in [a_link, b_link, sn_link, ns_link]:
        link.drive()
    global_clock += 1


# Launch Car
def launch_car():
    global next_departure
    if global_clock >= next_departure and model_state == "running" and parking_lot.length() > 0:
        next_car = parking_lot.dequeue()  # Извлекаем первую машину из очереди
        next_car.depart_time = global_clock
        next_car.route = choose_route()  # Выбираем маршрут для машины
        dashboard.record_departure()  # Записываем факт отправления
        next_departure = global_clock + launch_rate  # Устанавливаем время следующего отправления


# Run Simulation
def simulate():
    global model_state
    while model_state == "running":
        step()  # Выполняем шаг симуляции (движение машин по дороге)
        launch_car()  # Запускаем новые машины
        if parking_lot.length() == 0 and all(
                link.car_queue.length() == 0 for link in [a_link, b_link, sn_link, ns_link]):
            model_state = "completed"  # Завершаем симуляцию, когда все машины покинули парковку и все очереди пусты
            print("Simulation complete.")


if __name__ == '__main__':
    # Example Nodes and Links
    orig = Node("orig")
    dest = Node("dest")
    south = Node("south")
    north = Node("north")

    a_link = Link("a", orig, south, 100)
    A_link = Link("A", orig, north, 100)
    b_link = Link("b", north, dest, 100)
    B_link = Link("B", south, dest, 100)
    sn_link = Link("sn", south, north, 50)
    ns_link = Link("ns", north, south, 50)
    sn_link.open_to_traffic = False
    ns_link.open_to_traffic = False

    Ab = Route("Ab")
    Ab.itinerary = [a_link, b_link]
    Ab.calc_route_length()

    aB = Route("aB")
    aB.itinerary = [a_link, ns_link]
    aB.calc_route_length()

    AB = Route("AB")
    AB.itinerary = [a_link, sn_link, b_link]
    AB.calc_route_length()

    ab = Route("ab")
    ab.itinerary = [a_link, ns_link, b_link]
    ab.calc_route_length()

    dashboard = Dashboard()
    init()
    simulate()
