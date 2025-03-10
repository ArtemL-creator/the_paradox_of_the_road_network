import math
import random
import time
import types

# Глобальные переменные
model_state = "stopped"  # "stopped", "running", "stopping"
bridge_blocked = True
routing_mode = "selfish"  # или "random"
speed_mode = "theoretical"  # альтернативы: "actual", "historical"
selection_method = "minimum"  # или "weighted-probability", "minimum"
launch_timing = "poisson"  # альтернативы: "uniform", "periodic"
global_clock = 0  # счётчик тактов симуляции
next_departure = 0  # следующий такт, когда можно отправить автомобиль
max_cars = 500  # float("inf")         # если не задано – не ограничено

car_radius = 3
car_length = 2 * car_radius
total_path_length = 1620
car_queue_size = int(total_path_length / car_length) + 10
speed_limit = 3
launch_rate = 0.55
congestion_coef = 0.55
quickest_trip = 582 / speed_limit
geek_mode = False
hint_mode = True

# my global
num_of_steps = 0


# Функции распределения
def coin_flip():
    return random.random() < 0.5


def poisson(lambda_val):
    return -math.log(1 - random.random()) / lambda_val


def uniform_func(lambda_val):
    return random.random() * 2 / lambda_val


def periodic(lambda_val):
    return 1 / lambda_val


# Функция выбора времени запуска
launch_timer = poisson  # т.к. launch_timing === "poisson"


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


# Класс для симуляции “аватара” (визуальное представление автомобиля)
class Avatar:
    def __init__(self, x=0, y=0, r=car_radius, fill="#000", display="none"):
        self.x = x
        self.y = y
        self.r = r
        self.fill = fill
        self.display = display

    def set_position(self, x, y):
        self.x = x
        self.y = y

    def set_fill(self, fill):
        self.fill = fill

    def set_display(self, display):
        self.display = display


# Класс узла (Node). Для упрощения координаты передаются в конструкторе.
class Node:
    def __init__(self, id_str, x=0, y=0):
        self.node_name = id_str
        self.x = x
        self.y = y
        self.car = None

    def has_room(self):
        return self.car is None

    def accept(self, car):
        self.car = car

    def evacuate(self):
        if self.car:
            self.car.park()
            self.car = None

    def dispatch(self):
        if self.car:
            # Определяем следующий участок по маршруту (ключ – имя узла)
            print(f"Узел {self.node_name} пытается отправить машину")
            next_link = self.car.route.directions.get(self.node_name)
            if next_link is not None:
                print(f"Следующий участок: {next_link.id}")
                # Если участок пуст или последний автомобиль уже отъехал на car_length
                if next_link.car_q.len == 0 or next_link.car_q.items[-1].progress >= car_length:
                    print("Условие выполнено, машина отправлена")
                    self.car.progress = 0
                    self.car.avatar.set_position(self.x, self.y)
                    next_link.car_q.enqueue(self.car)
                    next_link.update_speed()
                    self.car = None


# Специальный узел для конечной точки, где происходит фиксация статистики
class DestinationNode(Node):
    def dispatch(self):
        if self.car:
            dashboard.record_arrival(self.car)
            print(f"Машина {self.car.serial_number} достигла конечной точки")
            self.car.park()
            self.car = None


# Вспомогательная функция для создания точки
def create_point(x, y):
    return {"x": x, "y": y}


# Класс участка дороги (Link)
class Link:
    def __init__(self, id_str, o_node, d_node, path_length=100, congestible=False):
        self.id = id_str
        # Определяем начальную и конечную точку по координатам узлов
        self.origin_xy = create_point(o_node.x, o_node.y)
        self.destination_xy = create_point(d_node.x, d_node.y)
        self.path_length = round(path_length)
        self.origin_node = o_node
        self.destination_node = d_node
        self.open_to_traffic = True
        self.car_q = Queue(car_queue_size)
        self.congestible = congestible
        self.occupancy = self.car_q.len
        self.speed = speed_limit
        self.travel_time = self.path_length / self.speed

    def update_speed(self):
        self.speed = speed_limit
        self.travel_time = self.path_length / self.speed

    def get_car_xy(self, progress):
        # Линейная интерполяция между началом и концом участка
        t = progress / self.path_length
        x = self.origin_xy["x"] + t * (self.destination_xy["x"] - self.origin_xy["x"])
        y = self.origin_xy["y"] + t * (self.destination_xy["y"] - self.origin_xy["y"])
        return {"x": x, "y": y}

    def drive(self):
        if self.car_q.len > 0:
            first_car = self.car_q.peek(0)
            first_car.past_progress = first_car.progress
            first_car.progress = min(self.path_length, first_car.progress + self.speed)
            first_car.odometer += first_car.progress - first_car.past_progress
            car_xy = self.get_car_xy(first_car.progress)
            first_car.avatar.set_position(car_xy["x"], car_xy["y"])

            # Обновляем положение последующих автомобилей
            for i in range(1, self.car_q.len):
                leader = self.car_q.peek(i - 1)
                follower = self.car_q.peek(i)
                follower.past_progress = follower.progress
                follower.progress = min(follower.progress + self.speed, leader.progress - car_length)
                follower.odometer += follower.progress - follower.past_progress
                car_xy = self.get_car_xy(follower.progress)
                follower.avatar.set_position(car_xy["x"], car_xy["y"])

            if first_car.progress >= self.path_length and self.destination_node.has_room():
                self.destination_node.accept(self.car_q.dequeue())
            self.update_speed()

    def evacuate(self):
        while self.car_q.len > 0:
            c = self.car_q.dequeue()
            c.park()
        self.update_speed()


# Подкласс для “узких” (congestible) участков, скорость которых зависит от плотности трафика
class CongestibleLink(Link):
    def update_speed(self):
        epsilon = 1e-10
        self.occupancy = self.car_q.len
        self.speed = speed_limit - (self.occupancy * car_length * speed_limit * congestion_coef) / self.path_length
        if self.speed <= 0:
            self.speed = epsilon
        self.travel_time = self.path_length / self.speed


# Методы для расчёта координат автомобиля на участке
def horizontal_get_car_xy(self, progress):
    return {"x": self.origin_xy["x"] + progress, "y": self.origin_xy["y"]}


def vertical_down_get_car_xy(self, progress):
    return {"x": self.origin_xy["x"], "y": self.origin_xy["y"] + progress}


def vertical_up_get_car_xy(self, progress):
    return {"x": self.origin_xy["x"], "y": self.origin_xy["y"] - progress}


# Парковка – очередь для простаивающих автомобилей
parking_lot = Queue(car_queue_size)


# Класс маршрута (Route)
class Route:
    def __init__(self):
        self.label = ""
        self.paint_color = None
        self.directions = {"orig": None, "south": None, "north": None, "dest": None}
        self.itinerary = []
        self.route_length = 0
        self.travel_time = 0

    def calc_route_length(self):
        rtl = 0
        for link in self.itinerary:
            rtl += link.path_length
        self.route_length = rtl

    def calc_travel_time(self):
        if speed_mode == "theoretical":
            self.calc_travel_time_theoretical()
        elif speed_mode == "actual":
            self.calc_travel_time_actual()
        else:
            self.calc_travel_time_historical()

    def calc_travel_time_theoretical(self):
        tt = 0
        for link in self.itinerary:
            tt += link.travel_time
        self.travel_time = tt

    def calc_travel_time_actual(self):
        n = 0
        total_tt = 0
        for c in car_array:
            if c and c.route == self and c.odometer > 0 and (global_clock - c.depart_time) != 0:
                v = (c.odometer / (global_clock - c.depart_time)) * speed_limit
                tt = self.route_length / v if v != 0 else float('inf')
                total_tt += tt
                n += 1
        if n == 0:
            self.travel_time = self.route_length / speed_limit
        else:
            self.travel_time = total_tt / n

    def calc_travel_time_historical(self):
        if dashboard.counts.get(self.label, 0) == 0:
            self.travel_time = self.route_length / speed_limit
        else:
            self.travel_time = dashboard.times[self.label] / dashboard.counts[self.label]


# Создаём узлы (с произвольными координатами)
orig = Node("orig", x=0, y=0)
dest = DestinationNode("dest", x=100, y=0)
south = Node("south", x=50, y=50)
north = Node("north", x=50, y=-50)

# Создаём участки дороги
a_link = CongestibleLink("a", orig, south, path_length=270, congestible=True)
a_link_noncongestible = Link("A", orig, north, path_length=500)
b_link = CongestibleLink("b", north, dest, path_length=270, congestible=True)
b_link_noncongestible = Link("B", south, dest, path_length=500)
sn_link = Link("sn-bridge", south, north, path_length=40)
ns_link = Link("ns-bridge", north, south, path_length=40)

sn_link.open_to_traffic = False
ns_link.open_to_traffic = False

# Подменяем метод get_car_xy для некоторых участков
a_link.get_car_xy = types.MethodType(horizontal_get_car_xy, a_link)
b_link.get_car_xy = types.MethodType(horizontal_get_car_xy, b_link)
sn_link.get_car_xy = types.MethodType(vertical_down_get_car_xy, sn_link)
ns_link.get_car_xy = types.MethodType(vertical_up_get_car_xy, ns_link)

# Создаём маршруты
route_Ab = Route()
route_Ab.label = "Ab"
route_Ab.paint_color = "#cb0130"
route_Ab.directions = {"orig": a_link_noncongestible, "south": None, "north": b_link, "dest": parking_lot}
route_Ab.itinerary = [a_link_noncongestible, b_link]
route_Ab.calc_route_length()

route_aB = Route()
route_aB.label = "aB"
route_aB.paint_color = "#1010a5"
route_aB.directions = {"orig": a_link, "south": b_link_noncongestible, "north": None, "dest": parking_lot}
route_aB.itinerary = [a_link, b_link_noncongestible]
route_aB.calc_route_length()

route_AB = Route()
route_AB.label = "AB"
route_AB.paint_color = "#ffc526"
route_AB.directions = {"orig": a_link_noncongestible, "south": b_link_noncongestible, "north": ns_link, "dest": parking_lot}
route_AB.itinerary = [a_link_noncongestible, ns_link, b_link_noncongestible]
route_AB.calc_route_length()

route_ab = Route()
route_ab.label = "ab"
route_ab.paint_color = "#4b9b55"
route_ab.directions = {"orig": a_link, "south": sn_link, "north": b_link, "dest": parking_lot}
route_ab.itinerary = [a_link, sn_link, b_link]
route_ab.calc_route_length()


# Класс с методами выбора маршрута
class Chooser:
    @staticmethod
    def random_choice(route_list):
        return random.choice(route_list)

    @staticmethod
    def min_choice(route_list):
        min_val = float('inf')
        min_routes = []
        for route in route_list:
            if route.travel_time < min_val:
                min_val = route.travel_time
                min_routes = [route]
            elif route.travel_time == min_val:
                min_routes.append(route)
        return random.choice(min_routes) if len(min_routes) > 1 else min_routes[0]

    @staticmethod
    def probabilistic(route_list):
        val_sum = 0
        for route in route_list:
            route.travel_time = 1 / route.travel_time if route.travel_time != 0 else 0
            val_sum += route.travel_time
        for route in route_list:
            route.travel_time /= val_sum
        r = random.random()
        accum = 0
        for route in route_list:
            accum += route.travel_time
            if accum > r:
                return route
        return route_list[-1]


def choose_route():
    if bridge_blocked:
        available_routes = [route_Ab, route_aB]
    else:
        available_routes = [route_Ab, route_aB, route_AB, route_ab]

    # Принудительно обновить время для всех маршрутов
    for route in available_routes:
        route.calc_travel_time()

    if routing_mode == "random":
        return Chooser.random_choice(available_routes)
    else:
        for route in available_routes:
            route.calc_travel_time()
        if selection_method == "minimum":
            return Chooser.min_choice(available_routes)
        else:
            return Chooser.probabilistic(available_routes)


# Класс автомобиля
class Car:
    def __init__(self):
        self.serial_number = None
        self.progress = 0
        self.past_progress = 0
        self.depart_time = 0
        self.arrive_time = 0
        self.route = None
        self.odometer = 0
        self.avatar = Avatar()
        parking_lot.enqueue(self)

    def park(self):
        if self.route:
            print(f"Машина {self.serial_number} возвращена в парковку")
        self.avatar.set_display("none")
        self.avatar.set_fill("#000")
        self.avatar.set_position(0, 0)
        self.route = None
        self.progress = 0
        self.past_progress = 0
        self.odometer = 0
        parking_lot.enqueue(self)


# Массив для хранения ссылок на все автомобили (для перебора)
car_array = [None] * car_queue_size


def make_cars(n):
    for i in range(n):
        c = Car()
        c.serial_number = i
        car_array[i] = c


def sync_controls():
    pass


# Объект для сбора статистики
class DashboardClass:
    def __init__(self):
        self.departure_count = 0
        self.arrival_count = 0
        self.counts = {"Ab": 0, "aB": 0, "AB": 0, "ab": 0, "total": 0}
        self.times = {"Ab": 0, "aB": 0, "AB": 0, "ab": 0, "total": 0}

    def colorize(self):
        print("Цвета маршрутов:")
        print("Ab:", route_Ab.paint_color)
        print("aB:", route_aB.paint_color)
        print("AB:", route_AB.paint_color)
        print("ab:", route_ab.paint_color)
        print("Total: #000")

    def record_departure(self):
        self.departure_count += 1

    def record_arrival(self, car):
        self.arrival_count += 1
        elapsed = (global_clock - car.depart_time) / speed_limit
        route_code = car.route.label if car.route else ""
        if route_code in self.counts:
            self.counts[route_code] += 1
            self.times[route_code] += elapsed
            self.counts["total"] += 1
            self.times["total"] += elapsed
        self.update_readouts()

    def update_readouts(self):
        print("Статистика:")
        print("Вых.:", self.departure_count)
        print("Прих.:", self.arrival_count)
        for key in self.counts:
            avg = "--" if self.counts[key] == 0 else round((self.times[key] / self.counts[key]) / quickest_trip, 3)
            print(f"{key}: кол-во={self.counts[key]}, ср. время={avg}")

    def reset(self):
        self.departure_count = 0
        self.arrival_count = 0
        for key in self.counts:
            self.counts[key] = 0
        for key in self.times:
            self.times[key] = 0
        self.update_readouts()

    def active_cars(self):
        # Считаем, сколько автомобилей не находится в парковке
        res = sum(1 for car in car_array if car not in parking_lot.items)
        return res


dashboard = DashboardClass()


def save_stats():
    routes = ["Ab", "aB", "AB", "ab"]
    print("launch_rate:", launch_rate, "congestion_coef:", congestion_coef, "bridge_blocked:", bridge_blocked)
    for r in routes:
        print(r, dashboard.counts[r])
    print("total", dashboard.counts["total"])


def car_census(sample_interval):
    route_counts = {"Ab": 0, "aB": 0, "AB": 0, "ab": 0}
    if dashboard.departure_count > 10000 and global_clock % sample_interval == 0:
        for c in car_array:
            if c and c.route:
                route_counts[c.route.label] += 1
        print(global_clock / speed_limit, route_counts["Ab"], route_counts["aB"], route_counts["AB"], route_counts["ab"])


def launch_car():
    global next_departure, global_clock, model_state
    if orig.has_room() and global_clock >= next_departure and model_state == "running" and parking_lot.len > 0:
        next_car = parking_lot.dequeue()
        if next_car is None:
            return
        next_car.depart_time = global_clock
        next_car.route = choose_route()
        next_car.avatar.set_fill(next_car.route.paint_color)
        next_car.avatar.set_position(orig.x, orig.y)
        next_car.avatar.set_display("block")
        orig.accept(next_car)
        dashboard.record_departure()
        next_departure = global_clock + launch_timer(launch_rate / speed_limit)


def step():
    global global_clock, model_state, num_of_steps
    # Обновляем состояния узлов и участков в случайном порядке
    num_of_steps = num_of_steps + 1

    if num_of_steps == 69:
        pass

    if coin_flip():
        dest.dispatch()
        b_link.drive()
        dest.dispatch()
        b_link_noncongestible.drive()
    else:
        dest.dispatch()
        b_link_noncongestible.drive()
        dest.dispatch()
        b_link.drive()

    if coin_flip():
        north.dispatch()
        a_link_noncongestible.drive()
        north.dispatch()
        sn_link.drive()
    else:
        north.dispatch()
        sn_link.drive()
        north.dispatch()
        a_link_noncongestible.drive()

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

    orig.dispatch()
    launch_car()
    orig.dispatch()
    launch_car()
    # Для отладки можно раскомментировать:
    # car_census(9)
    global_clock += speed_limit

    if model_state == "stopping" and parking_lot.len == car_queue_size:
        # if model_state == "stopping" and dashboard.active_cars() == 0:
        print("Симуляция остановлена.")
        print(f"Количество шагов = {num_of_steps}")
        # save_stats()  # раскомментировать, если нужна сводка в консоли
        return False
    if model_state == "running" and dashboard.departure_count >= max_cars:
        model_state = "stopping"
        print("Достигнуто максимальное число автомобилей, остановка запуска.")
    return True


def animate():
    running = True
    while running:
        running = step()
        time.sleep(0.015)  # задержка ~15 мс (примерно 60 кадров/сек)


def init():
    global global_clock
    make_cars(car_queue_size)
    global_clock = 0
    sync_controls()
    a_link_noncongestible.update_speed()
    a_link.update_speed()
    b_link_noncongestible.update_speed()
    b_link.update_speed()
    ns_link.update_speed()
    sn_link.update_speed()
    dashboard.colorize()
    # setupForTouch() не требуется в версии для Python


if __name__ == "__main__":
    model_state = "running"
    init()
    animate()
