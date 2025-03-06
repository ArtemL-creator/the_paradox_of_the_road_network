import my_queue  # Для использования очереди

# Симуляция с глобальными параметрами
class TrafficSimulation:
    def __init__(self):
        # Инициализация глобальных переменных
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
        self.car_queue_size = int(self.total_path_length / self.car_length) + 10  # Размер очереди
        self.car_array = [None] * self.car_queue_size

    # Пример функции Poisson, которую вы можете использовать для запуска таймера
    def poisson(self):
        pass

# Класс Link, представляющий ссылку (дорогу) в симуляции
class Link:
    def __init__(self, id_str, o_node, d_node, simulation):
        self.id = id_str
        self.svg_path = None  # Этот атрибут будет связан с элементом SVG, например, с помощью библиотеки PyQt5 или Qt
        self.path_length = 0  # Длина пути, будет вычисляться на основе SVG
        self.origin_xy = None  # Начальная точка пути
        self.destination_xy = None  # Конечная точка пути
        self.origin_node = o_node
        self.destination_node = d_node
        self.open_to_traffic = True
        # Здесь передается car_queue_size из симуляции
        self.car_queue = queue.Queue(simulation.car_queue_size)
        self.congestible = False  # Допустим, здесь будет вычисляться на основе svg
        self.occupancy = self.car_queue.qsize()  # Текущая занятость очереди
        self.speed = 1  # Пример, может быть задано отдельно
        self.travel_time = self.path_length / self.speed  # Время в пути (например, скорость задана заранее)

# Пример использования:

# Инициализация симуляции

# Создание объекта Link, передача параметров из симуляции
link = Link(id_str="link1", o_node="origin", d_node="destination")

# Вывод значений для проверки
#print(f"Car queue size: {simulation.car_queue_size}")
print(f"Link car queue size: {link.car_queue.qsize()}")
