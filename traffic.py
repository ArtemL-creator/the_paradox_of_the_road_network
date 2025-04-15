import math
import random
import types
import sys
from random import choice

from lane import Lane
from queue import Queue
from traffic_light import TrafficLight
from multi_phase_traffic_light import MultiPhaseTrafficLight
# from traffic_node import TrafficNode
from avatar import Avatar
from road_event import RoadEvent

# from PyQt5.QtWidgets import QApplication
# from index_pyqt5 import TrafficApp

# Глобальные переменные
model_state = "stopped"  # "stopped", "running", "stopping"
bridge_blocked = False
traffic_light_on = False
road_events_on = False
routing_mode = "selfish"  # или "random", "selfish"
speed_mode = "actual"  # альтернативы: "actual", "historical", "theoretical"
selection_method = "minimum"  # или "weighted-probability", "minimum"
launch_timing = "poisson"  # альтернативы: "uniform", "periodic"
global_clock = 0  # счётчик тактов симуляции
next_departure = 0  # следующий такт, когда можно отправить автомобиль
max_cars = 1500  # float("inf")         # если не задано – не ограничено

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


# Класс узла (Node). Для упрощения координаты передаются в конструкторе.
class Node:
    def __init__(self, id_str, x=0, y=0):
        self.node_name = id_str
        self.x = x
        self.y = y
        self.car = None
        self.arrived_from_link = None  # Новое поле

    def has_room(self):
        return self.car is None

    def accept(self, car, from_link):  # Принимаем доп. аргумент
        if self.has_room():  # Проверка не помешает
            self.car = car
            self.arrived_from_link = from_link  # Сохраняем, откуда приехала
        else:
            # Этого не должно происходить, если has_room() проверяется до вызова accept,
            # но на всякий случай.
            print(f"[ERROR] Node {self.node_name} не может принять машину, т.к. занят!")
            car.park()  # Куда-то деть машину

    def evacuate(self):
        if self.car:
            self.car.park()
            self.car = None

    def dispatch(self):
        if self.car:
            # Определяем следующий участок по маршруту (ключ – имя узла)
            # print(f"Узел {self.node_name} пытается отправить машину")

            next_link = self.car.route.directions.get(self.node_name)
            if next_link is not None:
                # print(f"Следующий участок: {next_link.id}")

                # Выбираем свободную полосу на следующем участке
                free_lane = next_link.choose_free_lane()
                # Если участок пуст или последний автомобиль уже отъехал на car_length
                if free_lane is not None:
                    # Если полоса пуста или последний автомобиль отъехал на достаточное расстояние
                    if free_lane.queue.len == 0 or free_lane.queue.items[-1].progress >= car_length:
                        # print("Условие выполнено, машина отправлена")

                        self.car.progress = 0
                        self.car.avatar.set_position(self.x, self.y)
                        free_lane.queue.enqueue(self.car)
                        next_link.update_speed()
                        self.car = None
                    else:
                        # !!! ЛОГИРУЕМ ПРИЧИНУ НЕВОЗМОЖНОСТИ ВЪЕЗДА !!!
                        blocker_progress = free_lane.queue.items[-1].progress if free_lane.queue.len > 0 else -1
                        print(
                            f"[GRIDLOCK_DEBUG] Узел {self.node_name}: Машина {self.car.serial_number} НЕ МОЖЕТ въехать на {next_link.id} (ЗЕЛЕНЫЙ).")
                        print(
                            f"[GRIDLOCK_DEBUG]   Причина: Полоса {free_lane.lane_id} занята. Очередь={free_lane.queue.len}, Прогресс последней машины={blocker_progress:.2f} (нужно >= {car_length})")
                else:
                    print("Нет свободных полос на участке", next_link.id)
            else:
                print("Нет свободных полос на следующем участке!")


# Специальный узел для конечной точки, где происходит фиксация статистики
class DestinationNode(Node):
    def dispatch(self):
        if self.car:
            dashboard.record_arrival(self.car)
            print(f"Машина {self.car.serial_number} достигла конечной точки")
            self.car.park()
            self.car = None


class TrafficNode(Node):
    def __init__(self, *, id_str, x=0, y=0, traffic_light: MultiPhaseTrafficLight, phase_map: dict):
        """
        phase_map – словарь, где ключ – номер фазы (например, 1 или 2),
        а значение – множество идентификаторов участков, для которых сигнал считается зелёным.
        Например: {1: {"sn-bridge"}, 2: {"other-link"}}
        """
        super().__init__(id_str, x, y)
        self.traffic_light = traffic_light
        self.phase_map = phase_map

    def dispatch(self):
        if self.car and self.arrived_from_link:  # Проверяем, что машина и информация о прибытии есть
            current_phase_index = self.traffic_light.get_phase()
            # print(f"[LOG DISPATCH] Узел {self.node_name} пытается отправить машину {self.car.serial_number}")
            print(f"[LOG DISPATCH] Узел {self.node_name}: текущая фаза = {current_phase_index}")

            # Получаем ID линка, С КОТОРОГО прибыла машина
            incoming_link_id = self.arrived_from_link.id

            # Смотрим в phase_map, разрешен ли ВЪЕЗД С этого линка в текущей фазе
            allowed_incoming_links = self.phase_map.get(current_phase_index, set())

            if incoming_link_id in allowed_incoming_links:
                # ДА, въезд с этого направления разрешен (зеленый для приехавших с incoming_link_id)
                print(
                    f"[LOG DISPATCH] Узел {self.node_name}: Фаза {current_phase_index}. Въезд с {incoming_link_id} РАЗРЕШЕН.")

                # Теперь определяем, КУДА машина хочет ехать дальше по своему маршруту
                next_link_outgoing = self.car.route.directions.get(self.node_name)

                if next_link_outgoing is not None:
                    print(f"[LOG DISPATCH]   Машина {self.car.serial_number} хочет на -> {next_link_outgoing.id}")
                    # Пытаемся отправить на ЛЮБОЙ разрешенный маршрутом выходной линк,
                    # проверяя только наличие места на нем.
                    free_lane = next_link_outgoing.choose_free_lane()
                    if free_lane is not None:
                        can_enter_next = free_lane.queue.len == 0 or free_lane.queue.items[-1].progress >= car_length
                        if can_enter_next:
                            print(f"[LOG DISPATCH]   Отправлена на {next_link_outgoing.id}, полоса {free_lane.lane_id}")
                            self.car.progress = 0
                            self.car.avatar.set_position(self.x, self.y)
                            free_lane.queue.enqueue(self.car)
                            next_link_outgoing.update_speed()
                            self.car = None  # Освобождаем узел
                            self.arrived_from_link = None  # Сбрасываем инфо о прибытии
                        else:
                            print(f"[LOG DISPATCH]   НЕ отправлена. Участок {next_link_outgoing.id} занят у въезда.")
                            # Машина остается на узле ждать следующей попытки dispatch
                    else:
                        print(f"[LOG DISPATCH]   НЕ отправлена. Нет свободных полос на {next_link_outgoing.id}.")
                else:
                    print(f"[LOG DISPATCH]   НЕ отправлена. Нет следующего участка в маршруте?")

            else:
                # НЕТ, въезд с этого направления запрещен (красный для приехавших с incoming_link_id)
                self.car.waiting_time += 1
                print(
                    f"[LOG DISPATCH] Узел {self.node_name}: Фаза {current_phase_index}. Въезд с {incoming_link_id} ЗАПРЕЩЕН (красный). Машина {self.car.serial_number} ждёт ({self.car.waiting_time}).")
                # Ничего не делаем, машина ждет на узле
                return  # Явно выходим, т.к. отправка невозможна

        elif self.car and not self.arrived_from_link:
            print(f"[WARNING] Узел {self.node_name}: Машина есть, но неизвестно, откуда она прибыла!")


# Вспомогательная функция для создания точки
def create_point(x, y):
    return {"x": x, "y": y}


# Класс участка дороги (Link)
class Link:
    def __init__(self, *, id_str: str, o_node, d_node, num_lanes=1, path_length=100, congestive=True):
        self.id = id_str
        # Определяем начальную и конечную точку по координатам узлов
        self.origin_xy = create_point(o_node.x, o_node.y)
        self.destination_xy = create_point(d_node.x, d_node.y)
        self.path_length = round(path_length)
        self.origin_node = o_node
        self.destination_node = d_node
        self.open_to_traffic = True

        self.lanes = [Lane(lane_id=i, car_queue_size=car_queue_size) for i in range(num_lanes)]

        self.congestive = congestive
        # Вычисляем занятость как сумму машин во всех полосах
        self.occupancy = self.get_average_occupancy()
        self.speed = speed_limit
        self.travel_time = self.path_length / self.speed

    def get_total_occupancy(self):
        """Возвращает общее число машин во всех полосах."""
        return sum(lane.queue.len for lane in self.lanes)

    def get_average_occupancy(self):
        """Возвращает среднее число машин на одной полосе."""
        total = sum(lane.queue.len for lane in self.lanes)
        return total / len(self.lanes) if self.lanes else 0

    def update_speed(self):
        self.speed = speed_limit
        self.travel_time = self.path_length / self.speed

    def get_car_xy(self, progress):
        # Линейная интерполяция между началом и концом участка
        t = progress / self.path_length
        x = self.origin_xy["x"] + t * (self.destination_xy["x"] - self.origin_xy["x"])
        y = self.origin_xy["y"] + t * (self.destination_xy["y"] - self.origin_xy["y"])
        return {"x": x, "y": y}

    def choose_free_lane(self) -> Lane | None:
        """Выбирает свободную полосу с наименьшей очередью, при равенстве выбирается случайно."""
        free_lanes = [lane for lane in self.lanes if not lane.is_blocked]
        if not free_lanes:
            print(f"[LOG LANE CHOICE] Дорога {self.id}: все полосы заблокированы!")
            return None  # Все полосы заблокированы

        # Определяем минимальную длину очереди среди свободных полос
        min_length = min(lane.queue.len for lane in free_lanes)
        # Фильтруем полосы с минимальной очередью
        candidate_lanes = [lane for lane in free_lanes if lane.queue.len == min_length]

        # Выводим информацию о кандидативах
        candidate_info = ", ".join(
            [f"Полоса {lane.lane_id} (очередь: {lane.queue.len})" for lane in candidate_lanes]
        )
        # print(f"[DEBUG] Дорога {self.id}: свободные полосы с минимальной очередью (длина очереди = {min_length}): {candidate_info}")

        # Если больше одной полосы, выбираем случайным образом
        selected_lane = random.choice(candidate_lanes)
        # print(f"[DEBUG] Дорога {self.id}: выбрана полоса {selected_lane.lane_id} (очередь: {selected_lane.queue.len})")
        return selected_lane

    def try_reassign_blocked_lane(self, blocked_lane: Lane):
        """
        Переносит автомобили из заблокированной полосы blocked_lane
        только на непосредственно соседние полосы (разница в lane_id равна 1).
        """
        # Если участок однополосный, lane change бессмысленен.
        if len(self.lanes) == 1:
            return False

        # Выбираем только те полосы, у которых разница в lane_id равна 1
        candidate_lanes = [lane for lane in self.lanes if lane is not blocked_lane and not lane.is_blocked and abs(
            lane.lane_id - blocked_lane.lane_id) == 1]
        if not candidate_lanes:
            print(
                f"[LANE CHANGE] Нет соседних незаблокированных полос для участка {self.id} от полосы {blocked_lane.lane_id}")
            return False

        # Если несколько кандидатов, выбираем случайно
        target_lane = random.choice(candidate_lanes)

        # Если выбранная полоса подходит для перевода
        if target_lane.queue.len == 0 or target_lane.queue.items[-1].progress >= car_length:
            # Переносим все автомобили из заблокированной полосы (или хотя бы одного)
            while blocked_lane.queue.len > 0:
                car = blocked_lane.queue.dequeue()
                target_lane.queue.enqueue(car)
                print(
                    f"[LANE CHANGE] Машина {car.serial_number} переехала с полосы {blocked_lane.lane_id} на соседнюю полосу {target_lane.lane_id} участка {self.id}")
            return True
        else:
            print(f"[LANE CHANGE] Соседняя полоса {target_lane.lane_id} участка {self.id} не готова принять автомобили")
            return False

    def drive(self):
        for lane in self.lanes:
            # Если полоса заблокирована, пытаемся перевести автомобили на соседние полосы
            if lane.is_blocked:
                self.try_reassign_blocked_lane(lane)
                continue

            if lane.queue.len > 0:
                first_car = lane.queue.peek(0)
                first_car.past_progress = first_car.progress
                first_car.progress = min(self.path_length, first_car.progress + self.speed)
                first_car.odometer += first_car.progress - first_car.past_progress
                car_xy = self.get_car_xy(first_car.progress)
                first_car.avatar.set_position(car_xy["x"], car_xy["y"])

                # Обновляем положение последующих автомобилей

                for i in range(1, lane.queue.len):
                    leader = lane.queue.peek(i - 1)
                    follower = lane.queue.peek(i)
                    follower.past_progress = follower.progress
                    follower.progress = min(follower.progress + self.speed, leader.progress - car_length)
                    follower.odometer += follower.progress - follower.past_progress
                    car_xy = self.get_car_xy(follower.progress)
                    follower.avatar.set_position(car_xy["x"], car_xy["y"])

                if first_car.progress >= self.path_length and self.destination_node.has_room():
                    dequeued_car = lane.queue.dequeue()
                    # Передаем и машину, и сам линк (self)
                    self.destination_node.accept(car=dequeued_car, from_link=self)
                self.update_speed()

    def evacuate(self):
        """Очищает дорогу от машин"""
        for lane in self.lanes:
            while lane.queue.len > 0:
                c = lane.queue.dequeue()
                c.park()
        self.update_speed()


# Подкласс для “узких” (congestible) участков, скорость которых зависит от плотности трафика
class CongestibleLink(Link):
    def update_speed(self):
        epsilon = 1e-10
        self.occupancy = self.get_average_occupancy()  # Средняя загруженность на полосу
        density_factor = self.occupancy / car_queue_size  # Плотность загруженности (0 - 1)
        dynamic_congestion_coef = congestion_coef * (1 - (len(self.lanes) - 1) * 0.1)
        dynamic_congestion_coef = max(dynamic_congestion_coef, 0.1)  # Ограничение снизу
        self.speed = speed_limit - (
                self.occupancy * car_length * speed_limit * dynamic_congestion_coef) / self.path_length
        if self.speed <= 0:
            self.speed = epsilon
        self.travel_time = self.path_length / self.speed

        # Отладка: печатаем текущие параметры
        # print(f"[DEBUG] Дорога {self.id}:")
        # print(f" - Полос: {len(self.lanes)}")
        # print(f" - Заполненность: {self.occupancy:.2f}/{car_queue_size} (среднее)")
        # print(f" - Коэффициент сопротивления: {dynamic_congestion_coef:.3f}")
        # print(f" - Скорость: {self.speed:.2f} (ограничение: {speed_limit})")
        # print(f" - Время проезда: {self.travel_time:.2f} сек\n")


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
            if traffic_light_on:
                self.calc_travel_time_theoretical_with_lights()
            else:
                self.calc_travel_time_theoretical()
        elif speed_mode == "actual":
            if traffic_light_on:
                self.calc_travel_time_actual()
        else:
            self.calc_travel_time_historical()

    def calc_travel_time_theoretical(self):
        tt = 0
        print(f"[LOG ROUTE TIME CALC] Маршрут {self.label}:")
        for link in self.itinerary:
            tt += link.travel_time
            print(
                f"[LOG ROUTE TIME CALC]   Участок {link.id}: длина={link.path_length}, скорость={link.speed}, время={link.travel_time}")
        self.travel_time = tt

    def calc_travel_time_theoretical_with_lights(self):
        """
        Рассчитывает теоретическое время в пути, С УЧЕТОМ
        оценки задержек на светофорах (TrafficNode), управляемых
        MultiPhaseTrafficLight, где фазы разрешают ВЪЕЗД С определенных линков.
        """
        tt = 0  # Общее расчётное время
        traffic_light_node_count = 0  # Счётчик узлов со светофорами
        print(f"[LOG ROUTE TIME W/ LIGHTS v2] Расчет для маршрута {self.label}:")

        # Итерируем по участкам маршрута с использованием индекса
        for i, current_link in enumerate(self.itinerary):
            # 1. Добавляем время движения по самому участку
            link_time = current_link.travel_time
            tt += link_time
            print(
                f"[LOG ROUTE TIME W/ LIGHTS v2]   Участок {current_link.id} (Длина: {current_link.path_length:.0f}, Скорость: {current_link.speed:.2f}): Время движения = {link_time:.2f}")

            # 2. Проверяем узел НАЗНАЧЕНИЯ текущего участка - ЗДЕСЬ БУДЕТ СВЕТОФОР
            destination_node = current_link.destination_node

            # 3. Проверяем, является ли этот узел светофором
            #    И не является ли он последним узлом маршрута (не считаем ожидание в самом конце)
            is_last_link = (i == len(self.itinerary) - 1)

            if isinstance(destination_node, TrafficNode) and \
                    hasattr(destination_node, 'traffic_light') and \
                    hasattr(destination_node.traffic_light, 'phase_durations') and \
                    not is_last_link:

                traffic_light_node_count += 1
                print(
                    f"[LOG ROUTE TIME W/ LIGHTS v2]     -> Узел {destination_node.node_name}: Светофор #{traffic_light_node_count}")

                # Определяем линк, ПО КОТОРОМУ машина прибыла к этому узлу
                # current_link - это и есть тот линк, с которого машина въезжает на destination_node
                incoming_link_id = current_link.id

                # Получаем объект светофора и карту фаз узла
                light = destination_node.traffic_light
                phase_map = destination_node.phase_map

                # --- Оценка ожидания на основе разрешения для ВХОДЯЩЕГО линка ---
                estimated_wait = 0
                green_phase_index = -1
                red_duration = 0
                total_cycle_time = sum(light.phase_durations) if light.phase_durations else 0

                if total_cycle_time <= 0:
                    print(f"[WARNING] Маршрут {self.label}: Что-то не так у узла {destination_node.node_name}")
                else:
                    # Ищем ИНДЕКС фазы, которая разрешает ВЪЕЗД С нашего incoming_link_id
                    for idx, allowed_incoming_links in phase_map.items():
                        if not isinstance(idx, int) or idx < 0 or idx >= light.num_phases:
                            print(
                                f"[WARNING] Маршрут {self.label}: Неверный индекс фазы '{idx}' в phase_map узла {destination_node.node_name}.")
                            continue
                        if incoming_link_id in allowed_incoming_links:
                            green_phase_index = idx
                            break  # Нашли

                    if green_phase_index != -1:
                        # Нашли зеленую фазу для въезда с нашего направления
                        green_duration = light.phase_durations[green_phase_index]
                        if green_duration >= total_cycle_time:
                            red_duration = 0
                        else:
                            red_duration = total_cycle_time - green_duration

                        estimated_wait = red_duration / 2.0
                        print(
                            f"[LOG ROUTE TIME W/ LIGHTS v2]       Въезд с -> {incoming_link_id}: Зеленая фаза (индекс)={green_phase_index}, Длит. красного={red_duration}, Цикл={total_cycle_time}, Ожидание ~{estimated_wait:.2f}")
                    else:
                        # Въезд с нашего направления не разрешен ни в одной фазе!
                        print(
                            f"[WARNING] Маршрут {self.label}: Въезд с '{incoming_link_id}' на узел '{destination_node.node_name}' не найден ни в одной фазе phase_map!")
                        estimated_wait = 0
                        print(
                            f"[LOG ROUTE TIME W/ LIGHTS v2]       Въезд с -> {incoming_link_id}: НАПРАВЛЕНИЕ НЕ НАЙДЕНО В PHASE_MAP! Ожидание = 0")

                tt += estimated_wait

        print(
            f"[LOG ROUTE TIME W/ LIGHTS v2] Маршрут {self.label}: Найдено светофоров = {traffic_light_node_count}, Итоговое теор. время ~ {tt:.2f}")
        self.travel_time = tt

    def calc_travel_time_actual(self):
        """
        Рассчитывает ВРЕМЯ в пути на основе СРЕДНЕЙ СКОРОСТИ
        машин, ФАКТИЧЕСКИ находящихся на данном маршруте.
        Задержки (из-за заторов И светофоров) УЧИТЫВАЮТСЯ НЕЯВНО
        через снижение средней скорости наблюдавшихся машин.
        """
        n = 0  # Количество машин, по которым усредняем
        total_tt = 0  # Сумма расчетных времен для усреднения
        # print(f"[DEBUG] Calculating ACTUAL time for route {self.label} at clock {global_clock}")

        for car in car_array:
            # Ищем машины, которые СЕЙЧАС на ЭТОМ маршруте, УЖЕ ПРОЕХАЛИ что-то (>0),
            # и находятся в пути ненулевое время (>0)
            if (car and car.route == self and
                    car.odometer > 0):  # Проверяем, что машина вообще двигалась

                elapsed_time = global_clock - car.depart_time
                if elapsed_time > 0:  # Проверяем, что прошло время с момента старта

                    # Рассчитываем СРЕДНЮЮ скорость этой машины за все время ее пути
                    # УБИРАЕМ некорректное умножение на speed_limit
                    average_speed = car.odometer / elapsed_time
                    # print(f"[DEBUG]   Car {car.serial_number}: odometer={car.odometer:.1f}, time={elapsed_time:.1f}, avg_speed={average_speed:.2f}")

                    # Оцениваем ПОЛНОЕ время пути для этой машины,
                    # экстраполируя ее прошлую среднюю скорость на всю длину маршрута.
                    # Если средняя скорость была > 0, время будет конечным.
                    # Случай average_speed == 0 отсекается условием car.odometer > 0
                    estimated_total_time_for_car = self.route_length / average_speed
                    # print(f"[DEBUG]     Estimated TT for car: {estimated_total_time_for_car:.2f}")

                    total_tt += estimated_total_time_for_car
                    n += 1
                # else: # Debugging: Car hasn't been running for any time yet or departed in the future?
                #    print(f"[DEBUG]   Car {car.serial_number}: elapsed_time <= 0")
            # else: # Debugging: Car not on this route or odometer is 0
            # if car and car.route == self:
            #    print(f"[DEBUG]   Car {car.serial_number}: odometer=0")

        if n == 0:
            # Если нет машин на маршруте для оценки (или они еще не двигались),
            # используем теоретическое время без загрузки или оценку из theoretical_with_lights?
            # Пока оставим простое теоретическое.
            # print(f"[WARN] calc_travel_time_actual для {self.label}: Нет данных по движущимся машинам, используем теор. скорость.")
            # Альтернатива: вызвать теоретический расчет с учетом светофоров, если они включены
            if traffic_light_on:
                # Вычисляем теоретическое с ожиданием, чтобы иметь хоть какую-то оценку
                # Это рекурсивный вызов, если calc_travel_time вызывает его же.
                # Лучше просто скопировать логику или сделать отдельную функцию
                # Проще всего - использовать базовое теоретическое время.
                self.travel_time = self.route_length / speed_limit  # Самый простой fallback
            else:
                self.travel_time = self.route_length / speed_limit

        else:
            # Усредняем оцененное время по всем наблюдавшимся машинам
            self.travel_time = total_tt / n
            # print(f"[DEBUG] calc_travel_time_actual для {self.label}: n={n}, total_tt={total_tt:.2f}, final avg_tt={self.travel_time:.2f}")

    def calc_travel_time_historical(self):
        if dashboard.counts.get(self.label, 0) == 0:
            self.travel_time = self.route_length / speed_limit
        else:
            self.travel_time = dashboard.times[self.label] / dashboard.counts[self.label]


# Фаза 0: Зеленый для подходов A и a (въезд на мосты)
# Фаза 1: Все красные (пауза)
# Фаза 2: Зеленый для подходов sn-bridge и ns-bridge (выезд с мостов)
# Фаза 3: Все красные (пауза)
phase_times = [15, 5, 15, 5]  # Примерные длительности
traffic_signal = MultiPhaseTrafficLight(phase_times)

# Карты фаз теперь указывают РАЗРЕШЕННЫЕ ВХОДЯЩИЕ линки
south_phase_map = {
    0: {"a"},  # В фазе 0 можно въехать С 'a'
    1: set(),  # В фазе 1 въезд запрещен всем
    2: {"ns-bridge"},  # В фазе 2 можно въехать С 'ns-bridge'
    3: set()  # В фазе 3 въезд запрещен всем
}

north_phase_map = {
    0: {"A"},  # В фазе 0 можно въехать С 'A'
    1: set(),  # В фазе 1 въезд запрещен всем
    2: {"sn-bridge"},  # В фазе 2 можно въехать С 'sn-bridge'
    3: set()  # В фазе 3 въезд запрещен всем
}

# Создаём узлы (с произвольными координатами)
orig = Node("orig", x=0, y=0)
dest = DestinationNode("dest", x=100, y=0)
if traffic_light_on:
    south = TrafficNode(id_str="south", x=50, y=50, traffic_light=traffic_signal, phase_map=south_phase_map)
    north = TrafficNode(id_str="north", x=50, y=-50, traffic_light=traffic_signal, phase_map=north_phase_map)
else:
    south = Node("south", x=50, y=50)
    north = Node("north", x=50, y=-50)

# Создаём участки дороги
a_link = CongestibleLink(id_str="a", o_node=orig, d_node=south, path_length=270, congestive=True, num_lanes=1)
# A_link = Link(id_str="A", o_node=orig, d_node=north, path_length=500, num_lanes=3)
A_link = CongestibleLink(id_str="A", o_node=orig, d_node=north, path_length=500, num_lanes=3)
b_link = CongestibleLink(id_str="b", o_node=north, d_node=dest, path_length=270, congestive=True, num_lanes=1)
# B_link = Link(id_str="B", o_node=south, d_node=dest, path_length=500, num_lanes=3)
B_link = CongestibleLink(id_str="B", o_node=south, d_node=dest, path_length=500, num_lanes=3)
# sn_link = Link(id_str="sn-bridge", o_node=south, d_node=north, path_length=40, num_lanes=1)
sn_link = CongestibleLink(id_str="sn-bridge", o_node=south, d_node=north, path_length=40, num_lanes=3)
# ns_link = Link(id_str="ns-bridge", o_node=north, d_node=south, path_length=40, num_lanes=1)
ns_link = CongestibleLink(id_str="ns-bridge", o_node=north, d_node=south, path_length=40, num_lanes=3)

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
route_Ab.directions = {"orig": A_link, "south": None, "north": b_link, "dest": parking_lot}
route_Ab.itinerary = [A_link, b_link]
route_Ab.calc_route_length()

route_aB = Route()
route_aB.label = "aB"
route_aB.paint_color = "#1010a5"
route_aB.directions = {"orig": a_link, "south": B_link, "north": None, "dest": parking_lot}
route_aB.itinerary = [a_link, B_link]
route_aB.calc_route_length()

route_AB = Route()
route_AB.label = "AB"
route_AB.paint_color = "#ffc526"
route_AB.directions = {"orig": A_link, "south": B_link, "north": ns_link, "dest": parking_lot}
route_AB.itinerary = [A_link, ns_link, B_link]
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
        print(f"[LOG ROUTE SELECTION] Маршрут {route.label}: теоретическое время = {route.travel_time}")

    if routing_mode == "random":
        chosen_route = Chooser.random_choice(available_routes)
        print(f"[LOG ROUTE SELECTION] Выбран случайный маршрут: {chosen_route.label}")
        return chosen_route
    else:
        for route in available_routes:
            route.calc_travel_time()
        if selection_method == "minimum":
            chosen_route = Chooser.min_choice(available_routes)
            print(
                f"[LOG ROUTE SELECTION] Выбран маршрут с минимальным временем: {chosen_route.label} (время = {chosen_route.travel_time})")
            return chosen_route
        else:
            chosen_route = Chooser.probabilistic(available_routes)
            print(f"[LOG ROUTE SELECTION] Выбран маршрут вероятностным методом: {chosen_route.label}")
            return chosen_route


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
        self.waiting_time = 0  # суммарное время ожидания на узлах
        self.avatar = Avatar(r=car_radius)
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
        print(global_clock / speed_limit, route_counts["Ab"], route_counts["aB"], route_counts["AB"],
              route_counts["ab"])


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
        orig.accept(car=next_car, from_link=None)
        dashboard.record_departure()
        next_departure = global_clock + launch_timer(launch_rate / speed_limit)


# Список текущих дорожных событий (ремонтов)
road_events = []


def update_road_events(current_time):
    for event in road_events:
        event.update(current_time)


def schedule_random_repair(current_time):
    # Выбираем случайный участок из списка участков
    if bridge_blocked:
        link = random.choice([a_link, A_link, b_link, B_link])
    else:
        link = random.choice([a_link, A_link, b_link, B_link, sn_link, ns_link])
    # Выбираем случайную полосу, если таковая есть
    available_lanes = [lane for lane in link.lanes if not lane.is_blocked]
    if available_lanes:
        lane = random.choice(available_lanes)
        # Определяем время начала ремонта – например, через несколько тактов от текущего
        start_time = current_time + random.randint(5, 20)
        duration = random.randint(10, 50)
        event = RoadEvent(link=link, lane=lane, start_time=start_time, duration=duration)
        road_events.append(event)
        print(
            f"[ROAD EVENT] Запланирован ремонт на участке {link.id}, полоса {lane.lane_id} начиная с такта {start_time} на {duration} тактов")


def step():
    global global_clock, model_state, num_of_steps
    # Обновляем состояния узлов и участков в случайном порядке
    num_of_steps = num_of_steps + 1

    # Обновляем события ремонта
    if road_events_on:
        update_road_events(global_clock)
        # С вероятностью p планируем случайный ремонт
        if random.random() < 0.05:
            schedule_random_repair(global_clock)

    # Обновляем светофор(ы) для узлов с сигналами
    if traffic_light_on:
        # Передаем реальный шаг времени симуляции
        time_increment = speed_limit
        traffic_signal.update(time_step=time_increment)

    if num_of_steps == 69:
        pass

    if coin_flip():
        dest.dispatch()
        b_link.drive()
        dest.dispatch()
        B_link.drive()
    else:
        dest.dispatch()
        B_link.drive()
        dest.dispatch()
        b_link.drive()

    if coin_flip():
        north.dispatch()
        A_link.drive()
        north.dispatch()
        sn_link.drive()
    else:
        north.dispatch()
        sn_link.drive()
        north.dispatch()
        A_link.drive()

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
    # orig.dispatch()
    # launch_car()
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
        # time.sleep(0.015)  # задержка ~15 мс (примерно 60 кадров/сек)


# def go_stop_button():
#     global model_state
#     if model_state == "stopped":
#         model_state = "running"
#         main_window.go_button.setText("Stop")
#         animate()
#     elif model_state == "running":
#         model_state = "stopping"
#         main_window.go_button.setText("Wait")
#         main_window.go_button.setDisabled(True)


def init():
    global global_clock
    make_cars(car_queue_size)
    global_clock = 0
    sync_controls()
    A_link.update_speed()
    a_link.update_speed()
    B_link.update_speed()
    b_link.update_speed()
    ns_link.update_speed()
    sn_link.update_speed()
    dashboard.colorize()
    # setupForTouch() не требуется в версии для Python


if __name__ == "__main__":
    model_state = "running"
    # app = QApplication(sys.argv)
    # main_window = TrafficApp()
    init()
    # main_window.go_button.clicked.connect(go_stop_button)
    # main_window.show()
    # sys.exit(app.exec_())
    animate()
