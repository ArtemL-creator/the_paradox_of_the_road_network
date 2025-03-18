# Файл queue.py:

"""
Реализация очереди в виде кольцевого буфера. Примечание: проверка
на переполнение и недополнение не выполняется. Здесь этого никогда не должно происходить.

Я выбрал кольцевой буфер вместо встроенных в Javascript
методов 'unshift' и 'pop' по соображениям эффективности: Таким образом,
я получаю постоянное время для постановки в очередь и извлечения из очереди,
в то время как 'unshift' является линейным по длине очереди.
"""

class Queue:
    def __init__(self, max_items):
        """
        Конструктор очереди.

        Args:
            max_items (int): Максимальное количество элементов в очереди.
        """
        self.n = max_items
        self.q = [None] * self.n # Инициализация списка фиксированного размера
        self.head = 0
        self.len = 0

    def length(self):
        """
        Возвращает текущую длину очереди.

        Returns:
            int: Длина очереди.
        """
        return self.len

    def enqueue(self, item):
        """
        Добавляет элемент в конец очереди.

        Args:
            item: Элемент для добавления.
        """
        self.q[(self.head + self.len) % self.n] = item
        self.len += 1

    def dequeue(self):
        """
        Извлекает и возвращает элемент из начала очереди.

        Returns:
            Элемент, извлеченный из начала очереди.
        """
        item = self.q[self.head]
        self.len -= 1
        self.head = (self.head + 1) % self.n
        return item

    def first(self):
        """
        Возвращает первый элемент в очереди, не удаляя его.

        Returns:
            Первый элемент в очереди.
        """
        return self.q[self.head]

    def last(self):
        """
        Возвращает последний элемент в очереди, не удаляя его.

        Returns:
            Последний элемент в очереди.
        """
        return self.q[(self.head + self.len - 1) % self.n]

    def peek(self, idx):
        """
        Возвращает элемент по указанному индексу от начала очереди, не удаляя его.

        Args:
            idx (int): Индекс элемента для просмотра (от 0 до length() - 1).

        Returns:
            Элемент по указанному индексу.
        """
        return self.q[(self.head + idx) % self.n]

# Файл traffic.py:

import random
import math

xmlns = "http://www.w3.org/2000/svg"
# frame = document.getElementById("the-coordinate-frame") # DOM element

# event handlers and pointers to DOM elements
# sn_bridge = document.getElementById("sn-bridge") # DOM element
# sn_bridge.addEventListener("click", toggle_bridge, False) # DOM event listener

# ns_bridge = document.getElementById("ns-bridge") # DOM element
# ns_bridge.addEventListener("click", toggle_bridge, False) # DOM event listener

# the_barricade = document.getElementById("barricade") # DOM element
# the_barricade.addEventListener("click", toggle_bridge, False) # DOM event listener

# go_button = document.getElementById("the-run-button") # DOM element
# go_button.addEventListener("click", go_stop_button, False) # DOM event listener

# reset_button = document.getElementById("the-reset-button") # DOM element
# reset_button.addEventListener("click", reset_model, False) # DOM event listener

# max_cars_input = document.getElementById("max-cars-input") # DOM element
# max_cars_input.addEventListener("input", set_max_cars, False) # DOM event listener

# launch_rate_slider = document.getElementById("launch-rate-slider") # DOM element
# launch_rate_slider.addEventListener("input", get_launch_rate, False) # DOM event listener

# launch_rate_output = document.getElementById("launch-rate-output") # DOM element

# congestion_slider = document.getElementById("congestion-slider") # DOM element
# congestion_slider.addEventListener("input", get_congestion_coef, False) # DOM event listener

# congestion_output = document.getElementById("congestion-output") # DOM element

# launch_timing_menu = document.getElementById("launch-timing-menu") # DOM element
# launch_timing_menu.addEventListener("change", get_launch_timing, False) # DOM event listener

# routing_mode_menu = document.getElementById("routing-mode-menu") # DOM element
# routing_mode_menu.addEventListener("change", get_routing_mode, False) # DOM event listener

# speed_menu = document.getElementById("speed-menu") # DOM element
# speed_menu.addEventListener("change", get_speed_mode, False) # DOM event listener

# selection_method_menu = document.getElementById("selection-method-menu") # DOM element
# selection_method_menu.addEventListener("change", get_selection_method, False) # DOM event listener

# geek_toggle = document.getElementById("geek-out") # DOM element
# geek_toggle.addEventListener("click", toggle_geek_mode, False) # DOM event listener

# hint_toggle = document.getElementById("hint-toggle") # DOM element
# hint_toggle.addEventListener("click", toggle_hints, False) # DOM event listener

# hint_stylesheet = document.getElementById("hint-stylesheet") # DOM element


# globals
model_state = "stopped" # другие состояния: "running" (выполняется) и "stopping" (останавливается)
bridge_blocked = True
routing_mode = "selfish" # другой режим: "random" (случайный)
speed_mode = "theoretical" # альтернативы: "actual" (фактический), "historical" (исторический)
selection_method = "minimum" # другой выбор: "weighted-probability" (взвешенная вероятность)
launch_timing = "poisson" # другие: "uniform" (равномерный), "periodic" (периодический)
launch_timer = None # указатель на функцию, будет присвоено позже в init
global_clock = 0 # целочисленный счетчик шагов симуляции, для измерения времени в пути
next_departure = 0 # следующее показание часов, когда автомобиль должен отправиться
max_cars = float('inf') # указано элементом max_cars_input; если пусто, нет лимита
animation_timer = None # для setInterval/clearInterval (не используется в Python напрямую)
car_radius = 3
car_length = 2 * car_radius
total_path_length = 1620
car_queue_size = (total_path_length / car_length) + 10 # убедимся, что у нас никогда не закончатся автомобили
# car_array = [None] * car_queue_size # сохраняем указатели на все автомобили, чтобы мы могли перебирать их
speed_limit = 3 # расстояние за шаг времени в свободном потоке
launch_rate = 0.55 # скорость, с которой автомобили пытаются въехать в сеть в Origin; точное значение зависит от launch_timing
congestion_coef = 0.55 # 0 означает отсутствие замедления из-за пробок; 1 означает максимальную плотность, трафик замедляется почти до остановки
quickest_trip = 582 / speed_limit # Минимальное количество шагов времени для прохождения кратчайшего маршрута без пробок
geek_mode = False # показывать ли дополнительные "geeky" элементы управления; изначально нет
hint_mode = True # показывать ли всплывающие подсказки; изначально да

# my globals
num_of_steps = 0

# probability distributions and related stuff

def coin_flip():
    """Возвращает случайное True или False с вероятностью 50%."""
    return random.random() < 0.5 # note: returns boolean

# Return a random interval drawn from exponential distribution
# with rate parameter lambda
# Why 1 - Math.random() rather than just plain Math.random()?
# So that we get (0,1] instead of [0, 1), thereby avoiding the
# risk of taking log(0).
# The parameter lambda, which determines the intensity of the
# Poisson process, will be given a value of launchRate/speedLimit,
# which ranges from 0 to 1/3.
def poisson(lambda_val):
    """
    Возвращает случайный интервал, взятый из экспоненциального распределения
    с параметром скорости lambda.
    """
    return -math.log(1 - random.random()) / lambda_val

# Return a real chosen uniformly at random from a finite interval [0, d),
# where d = 2 / lambda. Thus the mean of the distribution is 1 / lambda.
def uniform(lambda_val):
    """
    Возвращает случайное вещественное число, равномерно распределенное
    в конечном интервале [0, d), где d = 2 / lambda.
    """
    return random.random() * 2 / lambda_val

# Generates a simple periodic sequence, without randomness, with period
# 1 / lambda. But note that cars are launched only at integer instants,
# so the observed stream of cars may not be as regular as this function
# would suggest.
def periodic(lambda_val):
    """
    Генерирует простую периодическую последовательность без случайности, с периодом
    1 / lambda.
    """
    return 1 / lambda_val

# The road network is built from two kinds of components: nodes, where
# roads begin or end of intersect, and links, which are directed paths running
# from one node to the next.

# Most of the logic in the model is implemented by the nodes, which
# act as routers for the cars. Visually, a node is an SVG circle. Algorithmically,
# it's a buffer with a capacity of one car.

# constructor for Nodes
class Node:
    def __init__(self, id_str):
        """
        Конструктор узла дорожной сети.

        Args:
            id_str (str): Идентификатор узла.
        """
        self.node_name = id_str
        # self.svg_circle = document.getElementById(id_str)  # visible representation # DOM element
        # self.x = self.svg_circle.cx.baseVal.value         # get coords from the HTML # DOM property
        # self.y = self.svg_circle.cy.baseVal.value         # "baseVal.value" because animatable # DOM property
        # Placeholder for coordinates, as DOM is not available
        self.x = 0
        self.y = 0
        self.car = None

    def has_room(self):
        """
        Проверяет, есть ли место в узле для принятия автомобиля.
        Нужно вызывать перед попыткой передать автомобиль дальше.

        Returns:
            bool: True, если в узле есть место, False в противном случае.
        """
        return not self.car

    def accept(self, car):
        """
        Принимает автомобиль в узел.

        Args:
            car: Объект автомобиля.
        """
        self.car = car

    # clean up if somebody presses the reset button
    def evacuate(self):
        """
        Очищает узел от автомобиля, если кто-то нажимает кнопку сброса.
        """
        if self.car:
            self.car.park() # обратно на парковку
            self.car = None

    # The dispatch function is the main duty of a node -- deciding where
    # each car goes next and moving it along. Actually, there's not much
    # deciding to be done. Each car carries its own itinerary, so the node
    # merely has to consult this record and place the car on the appropriate
    # link. The itinerary takes the form of a dictionary with the structure
    # {"orig": link, "south": link, "north": link, "dest": link}, where the
    # keys are the names of nodes, and the values are links.
    def dispatch(self):
        """
        Основная функция узла - диспетчеризация автомобилей.
        Определяет, куда автомобиль поедет дальше, и перемещает его.
        """
        if self.car:
            next_link = self.car.route.directions[self.node_name] # find the link where this car wants to go
            if self.next_link.car_q.length() == 0 or self.next_link.car_q.last().progress >= car_length: # can the link accept a car?
                self.car.progress = 0 # recording position along the link
                # self.car.avatar.setAttribute("cx", self.x) # avatar is the visual representation of the car in SVGland # DOM manipulation
                # self.car.avatar.setAttribute("cy", self.y)
                # Placeholder for avatar attribute setting, DOM manipulation is not available
                self.car.avatar_x = self.x # Assuming car avatar now represented by attributes in Python
                self.car.avatar_y = self.y
                self.next_link.car_q.enqueue(self.car) # send the car on its way
                self.next_link.update_speed() # recalculate speed based on occupancy of link
                self.car = None # empty buffer, ready for next

# the four nodes of the Braess road network
orig = Node("orig")
dest = Node("dest")
south = Node("south")
north = Node("north")

# The final destination node has some special duties, so we override
# the dispatch method.
class DestNode(Node): # Inherit from Node class
    def dispatch(self):
        """
        Переопределенный метод dispatch для конечного узла назначения.
        Регистрирует прибытие автомобиля и отправляет его на парковку.
        """
        if self.car:
            Dashboard.record_arrival(self.car) # Dashboard is where we record stats
            self.car.park()
            self.car = None

dest = DestNode("dest") # Re-assign dest to be an instance of DestNode

# Now we move on to the links, the roadways of the model. Again there's a
# visible manifestation as an SVG element and a behind-the-scenes data
# structure, which takes the form a queue. (See queue.js for details on
# the latter.)
# Note that much of the basic data about the link comes from the SVG
# (which is defined in index.html): the length of the path, start and end
# coordinates, which class of road it is (congestible or not).

# constructor for links; oNode and dNode are the origin and destination nodes
class Link:
    def __init__(self, id_str, o_node, d_node):
        """
        Конструктор звена дорожной сети.

        Args:
            id_str (str): Идентификатор звена.
            o_node (Node): Узел отправления.
            d_node (Node): Узел назначения.
        """
        self.id = id_str
        # self.svg_path = document.getElementById(id_str) # DOM element
        # self.path_length = math.round(self.svg_path.getTotalLength()) # DOM method
        # Placeholder for path_length, as DOM methods are not available
        self.path_length = 100 # Example length
        # console.log('Length', self.path_length)  # rounding to ensure lengths A=B and a=b
        # self.origin_xy = self.svg_path.getPointAtLength(0) # DOM method
        # self.destination_xy = self.svg_path.getPointAtLength(self.path_length) # DOM method
        # Placeholders for origin and destination XY, as DOM methods not available
        self.origin_xy = {"x": 0, "y": 0} # Example origin XY
        self.destination_xy = {"x": 10, "y": 10} # Example destination XY
        self.origin_node = o_node
        self.destination_node = d_node
        self.open_to_traffic = True # always true except for bridge links
        from queue import Queue # Import locally to avoid circular dependency if queue.py is in the same directory
        self.car_q = Queue(car_queue_size) # vehicles currently driving on this link
        # self.congestible = self.svg_path.classList.contains("thin-road") # DOM property
        # Placeholder for congestible, assuming it's always True for now
        self.congestible = True # true for a and b only
        self.occupancy = self.car_q.length()
        self.speed = speed_limit
        self.travel_time = self.path_length / speed_limit # default value, will be overridden

    def update_speed(self):
        """
        Обновляет скорость движения по звену.
        Стандартная реализация для широких дорог; будет переопределена для a и b.
        """
        self.speed = speed_limit
        self.travel_time = self.path_length / self.speed

    # def get_car_xy(self, progress): # DOM method
    #     """
    #     Возвращает координаты автомобиля на звене в зависимости от прогресса.
    #     0 <= progress <= path.length
    #     """
    #     return self.svg_path.getPointAtLength(progress) # DOM method
    def get_car_xy(self, progress):
        """
        Возвращает координаты автомобиля на звене в зависимости от прогресса.
        0 <= progress <= path.length
        Placeholder implementation as DOM method not available
        """
        return {"x": self.origin_xy["x"] + progress, "y": self.origin_xy["y"] + progress}


    # This is where the rubber meets the road, the procedure that actually
    # moves the cars along a link. It's also where most of the CPU cycles
    # get spent.
    #    The basic idea is to take a car's current speed, determine how far it
    # will move along the path at that speed in one time step, and update
    # its xy coordinates. But there's a complication: The car may not be able
    # to move that far if there's another car in front of it.
    #    The first car in the queue needs special treatment. We know there's
    # no one in front of it, but it may be near the end of the path.
    def drive(self):
        """
        Перемещает автомобили по звену. Основная логика движения автомобилей.
        """
        if self.car_q.length() > 0:
            first_car = self.car_q.peek(0)
            first_car.past_progress = first_car.progress
            first_car.progress = min(self.path_length, first_car.progress + self.speed) # don't go off the end
            first_car.odometer += first_car.progress - first_car.past_progress # cumulative distance over whole route
            car_xy = self.get_car_xy(first_car.progress)
            # first_car.avatar.setAttribute("cx", car_xy.x) # setting SVG coords # DOM manipulation
            # first_car.avatar.setAttribute("cy", car_xy.y)
            # Placeholder for avatar attribute setting, DOM manipulation is not available
            first_car.avatar_x = car_xy["x"]
            first_car.avatar_y = car_xy["y"]

            for i in range(1, self.car_q.length()): # now for all the cars after the first one
                leader = self.car_q.peek(i - 1)
                follower = self.car_q.peek(i)
                follower.past_progress = follower.progress
                follower.progress = min(follower.progress + self.speed, leader.progress - car_length) # don't rear-end the leader
                follower.odometer += follower.progress - follower.past_progress
                car_xy = self.get_car_xy(follower.progress)
                # follower.avatar.setAttribute("cx", car_xy.x) # DOM manipulation
                # follower.avatar.setAttribute("cy", car_xy.y)
                # Placeholder for avatar attribute setting, DOM manipulation is not available
                follower.avatar_x = car_xy["x"]
                follower.avatar_y = car_xy["y"]

            if first_car.progress >= self.path_length and self.destination_node.has_room(): # hand off car to destination node
                self.destination_node.accept(self.car_q.dequeue())
                self.update_speed() # occupancy has decreased by 1

    # when Reset pressed, dump all the cars back to the parking lot
    def evacuate(self):
        """
        Эвакуирует все автомобили со звена обратно на парковку при нажатии Reset.
        """
        while self.car_q.length() > 0:
            c = self.car_q.dequeue()
            c.park()
        self.update_speed()

# here we create the six links of the road network
a_link = Link("a", orig, south)
a_link_upper = Link("A", orig, north) # Renamed to avoid shadowing built-in function
b_link = Link("b", north, dest)
b_link_upper = Link("B", south, dest) # Renamed to avoid shadowing built-in function
sn_link = Link("sn-bridge", south, north)
ns_link = Link("ns-bridge", north, south)

# default state, bridge closed in both directions
sn_link.open_to_traffic = False
ns_link.open_to_traffic = False

# We need to override the updateSpeed method for the narrow links a and b,
# where traffic slows as a function of density. Under the formula given here,
# if occupancy === 0 (i.e., no cars on the road), speed === speedLimit. At
# maximum occupancy and congestionCoef === 1, speed falls to 0 and travelTime
# diverges. The if stmt makes sure speed is always strictly positive.
class CongestibleLink(Link): # Inherit from Link class
    def update_speed(self):
        """
        Переопределенный метод update_speed для узких звеньев a и b,
        где трафик замедляется в зависимости от плотности.
        """
        epsilon = 1e-10
        self.occupancy = self.car_q.length()
        self.speed = speed_limit - (self.occupancy * car_length * speed_limit * congestion_coef) / self.path_length
        if self.speed <= 0:
            self.speed = epsilon
        self.travel_time = self.path_length / self.speed

a_link = CongestibleLink("a", orig, south) # Re-assign a_link to be an instance of CongestibleLink
b_link = CongestibleLink("b", north, dest) # Re-assign b_link to be an instance of CongestibleLink

# borrow the aLink method for bLink - Not needed in Python inheritance is used

# The following four method overrides are for efficiency only. They
# can be eliminated without changing functionality.
#    The default getCarXY uses the SVG path method getPointAtLength.
# Profiling suggests that the program spends most of its cpu cycles
# executing this function. Four of the links are axis-parallel straight
# lines, for which we can easily calculate position without going into
# the SVG path.
class StraightLink(Link): # Inherit from Link class
    def get_car_xy(self, progress):
        """
        Переопределенный метод get_car_xy для прямых звеньев a и b,
        для оптимизации расчета координат без использования SVG.
        """
        y = self.origin_xy["y"]
        x = self.origin_xy["x"] + progress
        return {"x": x, "y": y} # return a point object in same format as getPointAtLength

a_link = StraightLink("a", orig, south) # Re-assign a_link to be an instance of StraightLink
b_link = StraightLink("b", north, dest) # Re-assign b_link to be an instance of StraightLink

class StraightVerticalLink(Link): # Inherit from Link class
    def get_car_xy(self, progress):
        """
        Переопределенный метод get_car_xy для вертикальных прямых звеньев sn и ns.
        """
        x = self.origin_xy["x"]
        y = self.origin_xy["y"] + progress
        return {"x": x, "y": y}

sn_link = StraightVerticalLink("sn-bridge", south, north) # Re-assign sn_link to be an instance of StraightVerticalLink

class StraightVerticalReverseLink(Link): # Inherit from Link class
    def get_car_xy(self, progress):
        """
        Переопределенный метод get_car_xy для вертикальных прямых звеньев ns (обратное направление).
        """
        x = self.origin_xy["x"]
        y = self.origin_xy["y"] - progress
        return {"x": x, "y": y}

ns_link = StraightVerticalReverseLink("ns-bridge", north, south) # Re-assign ns_link to be an instance of StraightVerticalReverseLink


# this one is not a link, just a bare queue, but
# it has a closely analogous function. This is the holding
# pen for cars after they reach the destination and before
# they get recycled to the origin.
parking_lot = Queue(car_queue_size) # holds idle cars

# A Route object encodes a sequence of links leading from Origin
# to Destination. For the road network in this model, there are
# just two possible routes when the bridge is closed, four when
# it is open. Each of these routes has an associated color; the
# cars following the route display the color. And the route
# also includes a directions object that instructs each node
# on how to handle a car following the route.

# constructor
class Route:
    def __init__(self):
        """
        Конструктор маршрута.
        Маршрут представляет собой последовательность звеньев, ведущих от Origin к Destination.
        """
        self.label = ""
        self.paint_color = None
        self.directions = {"orig": None, "south": None, "north": None, "dest": None}
        self.itinerary = []
        self.route_length = 0
        self.travel_time = 0

    # total length is just sum of constituent link lengths
    def calc_route_length(self):
        """
        Вычисляет общую длину маршрута как сумму длин составляющих звеньев.
        """
        rtl = 0
        for link in self.itinerary:
            rtl += link.path_length
        self.route_length = rtl

    # For calculating the expected travel time over a route, we have a
    # choice of three procedures. (The choice is determined by the
    # Speed Measurement selector.)

    def calc_travel_time(self):
        """
        Вычисляет ожидаемое время в пути по маршруту, используя выбранный метод измерения скорости.
        """
        if speed_mode == "theoretical":
            self.calc_travel_time_theoretical()
        elif speed_mode == "actual":
            self.calc_travel_time_actual()
        else:
            self.calc_travel_time_historical()

    # The theoretical travel time comes straight out of the definition
    # of the model. For links a and b travel time is a function of
    # occupancy -- the number of cars traversing the link. All other
    # links have travel time proportional to their length, regardless
    # of traffic density. Thus we can just add up these numbers for
    # the links composing a route.
    #   Why is this value "theoretical"? It assumes that cars always
    # travel at the speed limit on all non-congestible links. But in
    # there may be delays getting onto and off of those links, causing
    # "queue spillback" and increasing the travel time. Calculations
    # based on theretical values may therefore underestimate the true
    # travel time.
    def calc_travel_time_theoretical(self):
        """
        Вычисляет теоретическое время в пути, основанное на параметрах модели.
        """
        tt = 0
        for link in self.itinerary:
            tt += link.travel_time
        self.travel_time = tt

    # An alternative to the theoretical approach is to actually measure
    # the speed of cars currently traversing the route, and take an
    # average.
    #    TODO: I had a reason for looping through all cars, rather than
    # just those on the route (using queue.prototype.peek(i)) but I've
    # forgotten what it was. Now looks like a blunder.
    def calc_travel_time_actual(self):
        """
        Вычисляет фактическое время в пути, измеряя скорость автомобилей на маршруте.
        """
        n = 0
        sum_times = 0
        for c in car_array: # loop through all cars
            if c and c.route == self and c.odometer > 0: # select only cars on our route that have begun moving
                v = (c.odometer / (global_clock - c.depart_time)) * speed_limit # speed
                tt = self.route_length / v # travel time
                sum_times += tt # sum of travel times for all cars on the route
                n += 1
        if n == 0:
            self.travel_time = self.route_length / speed_limit # if no cars on this route, use default travel time
        else:
            self.travel_time = sum_times / n # average travel time for all cars on the route

    # A third approach: Use the cumulative statistics on travel times experienced
    # by all cars that have completed the route.
    def calc_travel_time_historical(self):
        """
        Вычисляет историческое время в пути, используя статистику по завершенным маршрутам.
        """
        if Dashboard.counts[self.label] == 0:
            self.travel_time = self.route_length / speed_limit # if no data, use the default value
        else:
            self.travel_time = Dashboard.times[self.label] / Dashboard.counts[self.label] # average travel time

# Define the four possible routes as instances of Route().

ab_route = Route()
ab_route.label = "Ab"
ab_route.paint_color = "#cb0130"
ab_route.directions = {"orig": a_link_upper, "south": None, "north": b_link, "dest": parking_lot}
ab_route.itinerary = [a_link_upper, b_link]
ab_route.calc_route_length()

ab_lower_route = Route() # Renamed to avoid shadowing existing variable
ab_lower_route.label = "aB"
ab_lower_route.paint_color = "#1010a5"
ab_lower_route.directions = {"orig": a_link, "south": b_link_upper, "north": None, "dest": parking_lot}
ab_lower_route.itinerary = [a_link, b_link_upper]
ab_lower_route.calc_route_length()

ab_upper_route = Route() # Renamed to avoid shadowing existing variable
ab_upper_route.label = "AB"
ab_upper_route.paint_color = "#ffc526"
ab_upper_route.directions = {"orig": a_link_upper, "south": b_link_upper, "north": ns_link, "dest": parking_lot}
ab_upper_route.itinerary = [a_link_upper, ns_link, b_link_upper]
ab_upper_route.calc_route_length()

ab_lower_upper_route = Route() # Renamed to avoid shadowing existing variable
ab_lower_upper_route.label = "ab"
ab_lower_upper_route.paint_color = "#4b9b55"
ab_lower_upper_route.directions = {"orig": a_link, "south": sn_link, "north": b_link, "dest": parking_lot}
ab_lower_upper_route.itinerary = [a_link, sn_link, b_link]
ab_lower_upper_route.calc_route_length()

# When a car is about to be launched upon a trip through the road
# network, we have to choose which route it will follow. In general,
# the choice is based on the expected travel time, as determined by
# one of the three methods above. But there are many ways to put the
# timing information to use.
#    Each of the functions below takes one argument, a list of all
# available routes. This will be a list of either two or four elements,
# depending on whether the bridge is closed or open.

chooser = {} # holder object for the three methods below

# The random chooser just ignores the route timings and chooses
# one of the available routes uniformly at random.
def random_chooser(route_list):
    """
    Выбирает случайный маршрут из списка доступных маршрутов.
    Игнорирует время в пути и выбирает маршрут случайным образом.
    """
    return route_list[math.floor(random.random() * len(route_list))]

chooser["random"] = random_chooser # Assigning to dictionary

# The min chooser always takes the route with the shortest expected
# travel time, no matter how small the advantage might be. If multiple
# routes have exactly the same time, the choice is random
def min_chooser(route_list):
    """
    Выбирает маршрут с наименьшим ожидаемым временем в пути.
    Если несколько маршрутов имеют одинаковое время, выбор случаен.
    """
    min_val = float('inf')
    min_routes = []
    for route in route_list:
        if route.travel_time < min_val:
            min_val = route.travel_time
            min_routes = [route] # best yet, make sole element of min_routes
        elif route.travel_time == min_val:
            min_routes.append(route) # equal times, append to min_routes list
    if len(min_routes) == 1:
        return min_routes[0] # the one fastest route
    else:
        return min_routes[math.floor(random.random() * len(min_routes))] # random choice among all best

chooser["min"] = min_chooser # Assigning to dictionary

# Rather than the winner-take-all strategy of the min chooser, here we
# make a random choice with probabilities weighted according to the
# travel times. Thus a small difference between two routes yields only
# a slightly greater likelihood.
def probabilistic_chooser(route_list):
    """
    Выбирает маршрут вероятностно, взвешивая вероятности обратно пропорционально времени в пути.
    Маршруты с меньшим временем в пути имеют большую вероятность выбора.
    """
    val_sum = 0
    for route in route_list:
        route.travel_time = 1 / route.travel_time # inverse of travel time
        val_sum += route.travel_time # sum of the reciprocals
    for route in route_list:
        route.travel_time /= val_sum # normalize so probabilities sum to 1
    r = random.random()
    accum = 0
    for route in route_list: # step through routes until cumulative
        accum += route.travel_time # weighted probability > random r
        if accum > r:
            return route

chooser["probabilistic"] = probabilistic_chooser # Assigning to dictionary


# The ugly nest of if-else clauses, based on two state variables,
# routingMode and selectionMethod.
def choose_route():
    """
    Выбирает маршрут для автомобиля на основе текущего режима маршрутизации и метода выбора.
    """
    available_routes = []
    if bridge_blocked:
        available_routes = [ab_route, ab_lower_route]
    else:
        available_routes = [ab_route, ab_lower_route, ab_upper_route, ab_lower_upper_route]
    if routing_mode == "random":
        return chooser["random"](available_routes)
    else: # routing_mode === "selfish"
        for route in available_routes:
            route.calc_travel_time()
        if selection_method == "minimum":
            return chooser["min"](available_routes)
        else: # selection_method === "probabilistic"
            return chooser["probabilistic"](available_routes)

# The cars are Javascript objects, with a "abatar" property that holds info
# about the visual representation in SVG. We put the avatars into the DOM
# at init time and then leave them there, to avoid the cost of repeated DOM
# insertions and removals. Cars that aren't currently on the road are still
# in the DOM but are hidden with display: none.

# constructor for cars
class Car:
    def __init__(self):
        """
        Конструктор автомобиля.
        Инициализирует автомобиль и добавляет его на парковку.
        """
        self.serial_number = None # invariant assigned at creation, mostly for debugging use
        self.progress = 0 # records distance traveled along a link (reset after leaving link)
        self.past_progress = 0 # at t-1, so we can calculate distance traveled at step t
        self.depart_time = 0 # globalClock reading at orig node
        self.arrive_time = 0 # globalClock reading at dest node
        self.route = None # route chosen for the car at time of launch
        self.odometer = 0 # cumulative distance traveled throughout route (not just link)
        # self.avatar = document.createElementNS(xmlns, "circle") # the SVG element # DOM method
        # self.avatar.setAttribute("class", "car") # DOM method
        # self.avatar.setAttribute("cx", 0) # DOM method
        # self.avatar.setAttribute("cy", 0) # DOM method
        # self.avatar.setAttribute("r", car_radius) # DOM method
        # self.avatar.setAttribute("fill", "#000") # will be changed at launch to route color # DOM method
        # self.avatar.setAttribute("display", "none") # hidden until launched # DOM method
        # frame.appendChild(self.avatar) # add avatar to the DOM # DOM method
        # Placeholders for avatar attributes, as DOM methods not available
        self.avatar_x = 0 # Example initial x coordinate
        self.avatar_y = 0 # Example initial y coordinate
        self.avatar_radius = car_radius
        self.avatar_fill = "#000"
        self.avatar_display = "none"

        parking_lot.enqueue(self) # add object to the holding pen

    # Reset a car to default "parked" state, and add it to the
    # parking lot queue. Used when a car reaches the destination node
    # or when the model is reset via UI button.
    def park(self):
        """
        Возвращает автомобиль в состояние "парковка" и добавляет его в очередь парковки.
        Используется, когда автомобиль достигает конечного узла или при сбросе модели.
        """
        # self.avatar.setAttribute("display", "none") # DOM method
        # self.avatar.setAttribute("fill", "#000") # DOM method
        # self.avatar.setAttribute("cx", 0) # DOM method
        # self.avatar.setAttribute("cy", 0) # DOM method
        # Placeholder for avatar attribute setting, DOM manipulation is not available
        self.avatar_display = "none"
        self.avatar_fill = "#000"
        self.avatar_x = 0
        self.avatar_y = 0
        self.route = None
        self.progress = 0
        self.past_progress = 0
        self.odometer = 0
        parking_lot.enqueue(self)

# Here's where we make all the cars. Note that new Car() enqueues them in
# parkingLot.
def make_cars(n):
    """
    Создает указанное количество автомобилей и помещает их на парковку.

    Args:
        n (int): Количество автомобилей для создания.
    """
    for i in range(n):
        c = Car()
        c.serial_number = i
        car_array[i] = c

# runs on load
def init():
    """
    Инициализирует модель при загрузке.
    Создает автомобили, синхронизирует элементы управления и обновляет скорости звеньев.
    """
    make_cars(car_queue_size)
    global_clock = 0
    # sync_controls() # UI control sync, not relevant in pure Python context
    a_link_upper.update_speed()
    a_link.update_speed()
    b_link_upper.update_speed()
    b_link.update_speed()
    ns_link.update_speed()
    sn_link.update_speed()
    # Dashboard.colorize() # UI color, not relevant in pure Python context
    # setup_for_touch() # Touch setup, not relevant in pure Python context
    global launch_timer # Need to declare global if modifying global var in function scope
    timings = {"poisson": poisson, "uniform": uniform, "periodic": periodic} # Use local timings var to init global launch_timer
    launch_timer = timings[launch_timing]


# Make sure the on-screen input elements correctly reflect the values
# of corresponding js variables. (This is needed mainly for Firefox,
# which does not reset inputs on page reload.)
# def sync_controls(): # UI control sync, not relevant in pure Python context
#     """
#     Синхронизирует значения элементов управления на экране с js переменными.
#     """
#     congestion_slider.value = congestion_coef # DOM property
#     launch_rate_slider.value = launch_rate # DOM property
#     routing_mode_menu.value = routing_mode # DOM property
#     launch_timing_menu.value = launch_timing # DOM property
#     speed_menu.value = speed_mode # DOM property
#     selection_method_menu.value = selection_method # DOM property
#     max_cars_input.value = "" # DOM property
#     geeky_controls = document.querySelectorAll(".geeky") # DOM method
#     for i in range(len(geeky_controls)): # DOM style manipulation
#         geeky_controls[i].style.display = "none" # DOM style manipulation
#     geek_toggle.textContent = "More controls" # DOM property
#     geek_mode = False


# Dashboard for recording and displaying stats. The "counts" and "times"
# dictionaries keep track of how many cars have traversed each route and
# how long they took to do it. Each of these values is linked to a cell
# in an HTML table.
class Dashboard:
    departure_count = 0
    arrival_count = 0
    counts = {
        "Ab": 0, "aB": 0, "AB": 0, "ab": 0, "total": 0
    }
    times = {
        "Ab": 0, "aB": 0, "AB": 0, "ab": 0, "total": 0
    }
    # count_readouts = { # DOM elements, not relevant in pure Python context
    # Ab: document.getElementById("Ab-count"), # links to HTML table cells # DOM method
    # aB: document.getElementById("aB-count"),
    # AB: document.getElementById("AB-count"),
    # ab: document.getElementById("ab-count"),
    # total: document.getElementById("total-count")
    # }

    # time_readouts = { # DOM elements, not relevant in pure Python context
    # Ab: document.getElementById("Ab-time"),
    # aB: document.getElementById("aB-time"),
    # AB: document.getElementById("AB-time"),
    # ab: document.getElementById("ab-time"),
    # total: document.getElementById("total-time")
    # }

    @staticmethod
    def colorize():
        """
        Устанавливает цвет фона ячеек таблицы статистики в соответствии с цветами маршрутов.
        """
        # Ab_row = document.getElementById("Ab-row") # DOM element
        # Ab_row.style.backgroundColor = ab_route.paint_color # DOM style manipulation
        # aB_row = document.getElementById("aB-row") # DOM element
        # aB_row.style.backgroundColor = ab_lower_route.paint_color # DOM style manipulation
        # AB_row = document.getElementById("AB-row") # DOM element
        # AB_row.style.backgroundColor = ab_upper_route.paint_color # DOM style manipulation
        # ab_row = document.getElementById("ab-row") # DOM element
        # ab_row.style.backgroundColor = ab_lower_upper_route.paint_color # DOM style manipulation
        # total_row = document.getElementById("total-row") # DOM element
        # total_row.style.backgroundColor = "#000" # DOM style manipulation
        pass # Placeholder as DOM manipulation is not relevant in pure Python context

    @staticmethod
    def record_departure():
        """
        Увеличивает счетчик отправлений автомобилей.
        Вызывается функцией launch_car.
        """
        Dashboard.departure_count += 1

    @staticmethod
    def record_arrival(car):
        """
        Регистрирует прибытие автомобиля и обновляет статистику.
        Вызывается методом dest.dispatch.

        Args:
            car (Car): Прибывший автомобиль.
        """
        elapsed = (global_clock - car.depart_time) / speed_limit
        route_code = car.route.label
        Dashboard.counts[route_code] += 1
        Dashboard.counts["total"] += 1
        Dashboard.times[route_code] += elapsed # Note: we're storing total time for all cars; need to divide by n
        Dashboard.times["total"] += elapsed
        Dashboard.update_readouts()

    # For the time readout, we divide total elapsed time by number of
    # cars to get time per car; we then also divide by the duration of the
    # quickest conceivable trip from Origin to Destination. Thus all times
    # are reported in units of this fastest trip.
    @staticmethod
    def update_readouts():
        """
        Обновляет показания панели статистики.
        """
        # for ct in Dashboard.count_readouts: # DOM elements, not relevant in pure Python context
        #     Dashboard.count_readouts[ct].textContent = Dashboard.counts[ct] # DOM property
        # for tm in Dashboard.time_readouts: # DOM elements, not relevant in pure Python context
        #     if Dashboard.counts[tm] == 0:
        #         Dashboard.time_readouts[tm].textContent = "--" # DOM property
        #     else:
        #         Dashboard.time_readouts[tm].textContent = "{:.3f}".format((Dashboard.times[tm] / Dashboard.counts[tm]) / quickest_trip) # DOM property
        pass # Placeholder as DOM manipulation is not relevant in pure Python context

    @staticmethod
    def reset():
        """
        Сбрасывает панель статистики, обнуляя все счетчики и времена.
        Вызывается при нажатии кнопки Reset.
        """
        Dashboard.departure_count = 0
        Dashboard.arrival_count = 0
        for ct in Dashboard.counts:
            Dashboard.counts[ct] = 0
        for tm in Dashboard.times:
            Dashboard.times[tm] = 0
        Dashboard.update_readouts()

# Event handlers and other routines connected with controls and the user interface.

# The Go button starts the animation, but the Stop button doesn't stop it.
# Instead we just set a state variable, change the button text to "Wait",
# and let any cars still on the road find their way to the destination.
# The step function -- the procedure run on every time step -- will eventually
# stop the periodic updates.
# def go_stop_button(e): # DOM Event handler, not relevant in pure Python context
#     """
#     Обработчик кнопки Go/Stop. Запускает и останавливает анимацию модели.
#     """
#     if model_state == "stopped":
#         model_state = "running"
#         go_button.innerHTML = "Stop" # DOM property
#         animate()
#     elif model_state == "running":
#         model_state = "stopping"
#         go_button.innerHTML = "Wait" # DOM property
#         go_button.disabled = True # DOM property


# Handler for the Reset button. If the model is running, we need to
# stop the animation. Then we clear all cars from links and nodes,
# clear the dashboard, and reset a few globals.
def reset_model():
    """
    Обработчик кнопки Reset. Останавливает анимацию, очищает сеть и панель статистики.
    """
    links_and_nodes = [a_link_upper, a_link, b_link_upper, b_link, ns_link, sn_link, orig, dest, north, south]
    global model_state, animation_timer, global_clock, next_departure # Need to declare global if modifying global var in function scope
    # if model_state == "running": # Condition check on global var
    #     model_state = "stopped" # Modify global var
    #     go_button.innerHTML = "Go" # DOM property
    #     window.clearInterval(animation_timer) # DOM method
    model_state = "stopped" # Forcing model to stop regardless of previous state
    # if animation_timer: # Check if animation_timer is set before clearing
    #     clearInterval(animation_timer) # Clear animation timer if it's running
    # animation_timer = None # Reset animation_timer
    # go_button.innerHTML = "Go" # Update go button text after stopping
    # go_button.removeAttribute("disabled") # Enable go button after stopping

    for link_node in links_and_nodes:
        link_node.evacuate()
    global_clock = 0
    next_departure = 0
    Dashboard.reset()

# Handler for the numeric input that allows us to run a specified number
# of cars through the system.
# def set_max_cars(e): # DOM Event handler, not relevant in pure Python context
#     """
#     Обработчик числового ввода для установки максимального количества автомобилей.
#     """
#     limit = int(max_cars_input.value) # DOM property
#     if limit == 0:
#         max_cars = float('inf') # Modify global var
#     else:
#         max_cars = limit # Modify global var

# Handler for clicks on the bridge in the middle of the roadway network.
# Initial state is blocked; clicks toggle between open and closed. Visual
# indicators are handled by altering the classList.
# def toggle_bridge(): # DOM event handler, not relevant in pure Python context
#     """
#     Обработчик кликов по мосту. Переключает состояние моста между открытым и закрытым.
#     """
#     global bridge_blocked, sn_link, ns_link # Need to declare global if modifying global var in function scope
#     bridge_blocked = not bridge_blocked # Modify global var
#     sn_link.open_to_traffic = not sn_link.open_to_traffic # Modify global var
#     ns_link.open_to_traffic = not ns_link.open_to_traffic # Modify global var
#     sn_bridge.classList.toggle("closed") # DOM method
#     ns_bridge.classList.toggle("closed") # DOM method
#     the_barricade.classList.toggle("hidden") # DOM method

# Handler for the Vehicle Launch Rate input (which will be rendered as a
# slider by most modern browsers).
# def get_launch_rate(e): # DOM event handler, not relevant in pure Python context
#     """
#     Обработчик слайдера скорости запуска автомобилей.
#     """
#     global launch_rate, next_departure, launch_timer, speed_limit # Need to declare global if modifying global var in function scope
#     launch_rate = max(float(launch_rate_slider.value), 0.001) # DOM property
#     launch_rate_output.textContent = "{:.2f}".format(launch_rate) # DOM property
#     next_departure = global_clock + launch_timer(launch_rate / speed_limit) # Modify global var

# Handler for the Congestion Coefficient slider.
# def get_congestion_coef(e): # DOM event handler, not relevant in pure Python context
#     """
#     Обработчик слайдера коэффициента загруженности.
#     """
#     global congestion_coef # Need to declare global if modifying global var in function scope
#     congestion_coef = float(congestion_slider.value) # DOM property
#     congestion_output.textContent = "{:.2f}".format(congestion_coef) # DOM property

# Handler for Launch Timing select input.
# def get_launch_timing(e): # DOM event handler, not relevant in pure Python context
#     """
#     Обработчик выпадающего списка выбора времени запуска автомобилей.
#     """
#     global launch_timing, launch_timer, speed_limit # Need to declare global if modifying global var in function scope
#     timings = {"poisson": poisson, "uniform": uniform, "periodic": periodic}
#     selected_timing = launch_timing_menu.value # DOM property
#     launch_timing = selected_timing # Modify global var
#     launch_timer = timings[selected_timing] # Modify global var

# Handler for Routing Mode select input.
# def get_routing_mode(e): # DOM event handler, not relevant in pure Python context
#     """
#     Обработчик выпадающего списка выбора режима маршрутизации.
#     """
#     global routing_mode # Need to declare global if modifying global var in function scope
#     selected_mode = routing_mode_menu.value # DOM property
#     routing_mode = selected_mode # Modify global var

# Handler for Speed Measurement select input.
# def get_speed_mode(e): # DOM event handler, not relevant in pure Python context
#     """
#     Обработчик выпадающего списка выбора метода измерения скорости.
#     """
#     global speed_mode # Need to declare global if modifying global var in function scope
#     selected_mode = speed_menu.value # DOM property
#     speed_mode = selected_mode # Modify global var

# Handler for Route Selection Method select input.
# def get_selection_method(e): # DOM event handler, not relevant in pure Python context
#     """
#     Обработчик выпадающего списка выбора метода выбора маршрута.
#     """
#     global selection_method # Need to declare global if modifying global var in function scope
#     selected_mode = selection_method_menu.value # DOM property
#     selection_method = selected_mode # Modify global var

# With two sliders, four drop-down menus, a couple of buttons, and a numeric
# input control, the UI looks a bit intimidating. To avoid scaring people away
# on first acquaintance, we can hide all but the most basic controls, and
# display the rest only on request. This is a handler for clicks on a "More
# controls"/"Fewer controls" element at the bottom of the control panel.
# def toggle_geek_mode(e): # DOM event handler, not relevant in pure Python context
#     """
#     Обработчик переключения отображения дополнительных элементов управления ("geeky").
#     """
#     global geek_mode # Need to declare global if modifying global var in function scope
#     geeky_controls = document.querySelectorAll(".geeky") # DOM method
#     if geek_mode: # Condition check on global var
#         for i in range(len(geeky_controls)): # DOM style manipulation
#             geeky_controls[i].style.display = "none" # DOM style manipulation
#         geek_toggle.textContent = "More controls" # DOM property
#     else:
#         for i in range(len(geeky_controls)): # DOM style manipulation
#             geeky_controls[i].style.display = "block" # DOM style manipulation
#         geek_toggle.textContent = "Fewer controls" # DOM property
#     geek_mode = not geek_mode # Modify global var

# Tooltips, or "hover hints", explain what all the geeky controls are supposed
# to control. But the hints themselves are annoying after you've seen them the
# first few times, so we provide a ways to turn them off. This is the click
# handler for the "Show/Hide hover hints" element at the bottom of the control panel.
#    The hint implementation is a CSS-only solution by Kushagra Gour (see hint.css).
# The easy way to turn it off and on is by disabling the whole stylesheet.
# def toggle_hints(e): # DOM event handler, not relevant in pure Python context
#     """
#     Обработчик переключения отображения всплывающих подсказок.
#     """
#     global hint_mode # Need to declare global if modifying global var in function scope
#     # if hint_mode: # Condition check on global var
#     #     hint_stylesheet.disabled = True # DOM property
#     #     hint_toggle.textContent = "Show hover hints" # DOM property
#     # else:
#     #     hint_stylesheet.disabled = False # DOM property
#     #     hint_toggle.textContent = "Hide hover hints" # DOM property
#     hint_mode = not hint_mode # Modify global var

# Set up for Touch devices. Kill the hints and the geek mode. Uses class
# added to the html tag by modernizr.
# def setup_for_touch(): # DOM and Modernizr dependency, not relevant in pure Python context
#     """
#     Настройка для сенсорных устройств. Отключает подсказки и "geeky" режим.
#     """
#     if Modernizr.touch: # Modernizr dependency
#         if geek_mode: # Condition check on global var
#             toggle_geek_mode()
#         if hint_mode: # Condition check on global var
#             toggle_hints()
#         geek_toggle.style.display = "none" # DOM style manipulation
#         hint_toggle.style.display = "none" # DOM style manipulation

# Prints the contents of the Dashboard panel to the console at the end of the
# run. Disabled by default; to activate, uncomment the line toward the end of
# the step function, below.
def save_stats():
    """
    Выводит в консоль содержимое панели статистики по завершении запуска.
    """
    routes = ["Ab", "aB", "AB", "ab"]
    print("launchRate:", launch_rate, "congestionCoef:", congestion_coef, "bridgeBlocked:", bridge_blocked)
    for route in routes:
        # print(route, Dashboard.count_readouts[route].textContent, Dashboard.time_readouts[route].textContent) # DOM property
        print(route, Dashboard.counts[route], Dashboard.times[route]) # Print counts and times directly from Dashboard class
    # print("total", Dashboard.count_readouts["total"].textContent, Dashboard.time_readouts["total"].textContent) # DOM property
    print("total", Dashboard.counts["total"], Dashboard.times["total"]) # Print counts and times directly from Dashboard class

# Just for producing graphs of occupancy levels; in default configuration,
# the only call to this function is commented out. When activated, carCensus
# logs the number of cars on each route at each time step. The output is a sequence
# of five numbers: time, Ab, aB, AB, ab.
def car_census(sample_interval):
    """
    Выводит статистику заполненности маршрутов для построения графиков.
    """
    route_counts = {"Ab": 0, "aB": 0, "AB": 0, "ab": 0}
    # census = [global_clock, 0, 0, 0, 0] # census is not used
    if Dashboard.departure_count > 10000 and global_clock % sample_interval == 0: # Condition check on Dashboard and global_clock
        for c in car_array:
            if c and c.route:
                route_counts[c.route.label] += 1
        print(global_clock / speed_limit, route_counts["Ab"], route_counts["aB"], route_counts["AB"], route_counts["ab"])

# Here we're at the starting line -- the procedure that prepares a car to
# run the course and hands it off to the Origin node. But it's more complicated
# than it should be. Not every call to launchCar actually launches a car.
#    Abstractly, here's what happens. At intervals determined by our timer
# function, a departure time is put on the schedule (by setting the global
# variable nextDeparture). LaunchCar runs on each clock tick, and checks to
# see if globalClock >= nextDeparture. However, the car can actually be launched
# at that moment only if there is room for it in the orig node buffer. This
# has nontrivial consequences when cars are being launched at high frequency.
#
def launch_car():
    """
    Запускает автомобиль в сеть, если есть место в начальном узле и пришло время отправления.
    """
    global next_departure # Need to declare global if modifying global var in function scope
    if orig.has_room() and global_clock >= next_departure and model_state == "running" and parking_lot.length() > 0: # Condition check on orig, global_clock, model_state, parking_lot
        next_car = parking_lot.dequeue()
        next_car.depart_time = global_clock
        next_car.route = choose_route()
        next_car.avatar_fill = next_car.route.paint_color # Use avatar_fill instead of setAttribute for fill
        # next_car.avatar.setAttribute("fill", next_car.route.paint_color) # DOM method
        # next_car.avatar.setAttribute("cx", orig.x) # DOM method
        # next_car.avatar.setAttribute("cy", orig.y) # DOM method
        # next_car.avatar.setAttribute("display", "block") # DOM method
        # Placeholders for avatar attribute setting, DOM manipulation is not available
        next_car.avatar_x = orig.x
        next_car.avatar_y = orig.y
        next_car.avatar_display = "block"
        orig.accept(next_car)
        Dashboard.record_departure()
        next_departure = global_clock + launch_timer(launch_rate / speed_limit) # Modify global var

# The step function is the main driver of the simulation. The idea is
# to poll all the nodes and links, moving cars along their route. But
# in what sequence should we examine the nodes and links. It makes sense
# to work backwards through the network, clearing space in later nodes
# and links so that cars behind them can move up.
#    There's another, subtler issue of sequencing. Every node except orig
# has two links feeding into it. If we always attend to those links in the
# same order, the later one might never get a chance to advance, if the
# earlier one keeps the node always occupied. I thought I could avoid this
# problem by simply alternating the sequence, but a deadlock is still
# possible in heavy traffic. Randomizing the sequence seems to work well.
def step():
    """
    Выполняет один шаг симуляции, перемещая автомобили по сети.
    """
    global global_clock, model_state, animation_timer, num_of_steps # Need to declare global if modifying global var in function scope
    num_of_steps += 1
    if coin_flip():
        dest.dispatch()
        b_link.drive()
        dest.dispatch()
        b_link_upper.drive()
    else:
        dest.dispatch()
        b_link_upper.drive()
        dest.dispatch()
        b_link.drive()
    if coin_flip():
        north.dispatch()
        a_link_upper.drive()
        north.dispatch()
        sn_link.drive()
    else:
        north.dispatch()
        sn_link.drive()
        north.dispatch()
        a_link_upper.drive()
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
    # car_census(9) # uncomment to log route occupancy numbers on every time step
    global_clock += speed_limit # Modify global var
    if model_state == "stopping" and parking_lot.length() == car_queue_size: # Condition check on model_state and parking_lot
        # window.clearInterval(animation_timer) # DOM method
        # animation_timer = None # Reset animation_timer
        model_state = "stopped" # Modify global var
        # go_button.innerHTML = "Go" # DOM property
        # go_button.removeAttribute("disabled") # DOM method
        print(num_of_steps)
        # save_stats() # uncomment to output a summary of the run to the JS console
    if model_state == "running" and Dashboard.departure_count >= max_cars: # Condition check on model_state and Dashboard
        model_state = "stopping" # Modify global var
        # go_button.innerHTML = "Wait" # DOM property
        # go_button.setAttribute("disabled", True) # DOM method
        pass # print(num_of_steps);


def animate(): # No DOM animation in pure Python context
    """
    Запускает анимацию симуляции. В Python просто вызывает step в цикле.
    """
    global animation_timer # Need to declare global if modifying global var in function scope
    # animation_timer = window.setInterval(step, 15) # DOM method
    animation_timer = True # Dummy value to indicate animation is "running" in Python context
    while model_state == "running" or model_state == "stopping": # Run step in a loop instead of setInterval
        step()
        if model_state == "stopped": # Break loop when model is stopped
            break


init() # Инициализация модели



