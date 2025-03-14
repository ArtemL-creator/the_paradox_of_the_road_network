import math
import random
import time
import types

# Глобальные переменные
model_state = "stopped"  # "stopped", "running", "stopping"
bridgeBlocked = False
routingMode = "selfish"  # или "random"
speedMode = "theoretical"  # альтернативы: "actual", "historical"
selectionMethod = "minimum"  # или "weighted-probability", "minimum"
launchTiming = "poisson"  # альтернативы: "uniform", "periodic"
globalClock = 0  # счётчик тактов симуляции
nextDeparture = 0  # следующий такт, когда можно отправить автомобиль
maxCars = 500  # float("inf")         # если не задано – не ограничено

carRadius = 3
carLength = 2 * carRadius
totalPathLength = 1620
carQueueSize = int(totalPathLength / carLength) + 10
speedLimit = 3
launchRate = 0.55
congestionCoef = 0.55
quickestTrip = 582 / speedLimit
geekMode = False
hintMode = True

# my global
numOfSteps = 0


# Функции распределения
def coinFlip():
    return random.random() < 0.5


def poisson(lambda_val):
    return -math.log(1 - random.random()) / lambda_val


def uniform_func(lambda_val):
    return random.random() * 2 / lambda_val


def periodic(lambda_val):
    return 1 / lambda_val


# Функция выбора времени запуска
launchTimer = poisson  # т.к. launchTiming === "poisson"


# Простейшая реализация очереди
class Queue:
    def __init__(self, maxsize):
        self.items = []
        self.maxsize = maxsize

    def enqueue(self, item):
        if len(self.items) < self.maxsize:
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
    def __init__(self, x=0, y=0, r=carRadius, fill="#000", display="none"):
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
        self.nodeName = id_str
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
            print(f"Узел {self.nodeName} пытается отправить машину")
            nextLink = self.car.route.directions.get(self.nodeName)
            if nextLink is not None:
                print(f"Следующий участок: {nextLink.id}")
                # Если участок пуст или последний автомобиль уже отъехал на carLength
                if nextLink.carQ.len == 0 or nextLink.carQ.items[-1].progress >= carLength:
                    print("Условие выполнено, машина отправлена")
                    self.car.progress = 0
                    self.car.avatar.set_position(self.x, self.y)
                    nextLink.carQ.enqueue(self.car)
                    nextLink.update_speed()
                    self.car = None


# Специальный узел для конечной точки, где происходит фиксация статистики
class DestinationNode(Node):
    def dispatch(self):
        if self.car:
            Dashboard.recordArrival(self.car)
            print(f"Машина {self.car.serialNumber} достигла конечной точки")
            self.car.park()
            self.car = None


# Вспомогательная функция для создания точки
def create_point(x, y):
    return {"x": x, "y": y}


# Класс участка дороги (Link)
class Link:
    def __init__(self, id_str, oNode, dNode, pathLength=100, congestible=False):
        self.id = id_str
        # Определяем начальную и конечную точку по координатам узлов
        self.originXY = create_point(oNode.x, oNode.y)
        self.destinationXY = create_point(dNode.x, dNode.y)
        self.pathLength = round(pathLength)
        self.originNode = oNode
        self.destinationNode = dNode
        self.openToTraffic = True
        self.carQ = Queue(carQueueSize)
        self.congestible = congestible
        self.occupancy = self.carQ.len
        self.speed = speedLimit
        self.travelTime = self.pathLength / self.speed

    def update_speed(self):
        self.speed = speedLimit
        self.travelTime = self.pathLength / self.speed

    def getCarXY(self, progress):
        # Линейная интерполяция между началом и концом участка
        t = progress / self.pathLength
        x = self.originXY["x"] + t * (self.destinationXY["x"] - self.originXY["x"])
        y = self.originXY["y"] + t * (self.destinationXY["y"] - self.originXY["y"])
        return {"x": x, "y": y}

    def drive(self):
        if self.carQ.len > 0:
            firstCar = self.carQ.peek(0)
            firstCar.pastProgress = firstCar.progress
            firstCar.progress = min(self.pathLength, firstCar.progress + self.speed)
            firstCar.odometer += firstCar.progress - firstCar.pastProgress
            carXY = self.getCarXY(firstCar.progress)
            firstCar.avatar.set_position(carXY["x"], carXY["y"])

            # Обновляем положение последующих автомобилей
            for i in range(1, self.carQ.len):
                leader = self.carQ.peek(i - 1)
                follower = self.carQ.peek(i)
                follower.pastProgress = follower.progress
                follower.progress = min(follower.progress + self.speed, leader.progress - carLength)
                follower.odometer += follower.progress - follower.pastProgress
                carXY = self.getCarXY(follower.progress)
                follower.avatar.set_position(carXY["x"], carXY["y"])

            if firstCar.progress >= self.pathLength and self.destinationNode.has_room():
                self.destinationNode.accept(self.carQ.dequeue())
                # self.update_speed()
            self.update_speed()

     # ===============================================================================================

    def evacuate(self):
        while self.carQ.len > 0:
            c = self.carQ.dequeue()
            c.park()
        self.update_speed()


# Подкласс для “узких” (congestible) участков, скорость которых зависит от плотности трафика
class CongestibleLink(Link):
    def update_speed(self):
        epsilon = 1e-10
        self.occupancy = self.carQ.len
        self.speed = speedLimit - (self.occupancy * carLength * speedLimit * congestionCoef) / self.pathLength
        if self.speed <= 0:
            self.speed = epsilon
        self.travelTime = self.pathLength / self.speed


# Методы для расчёта координат автомобиля на участке
def horizontal_getCarXY(self, progress):
    return {"x": self.originXY["x"] + progress, "y": self.originXY["y"]}


def vertical_down_getCarXY(self, progress):
    return {"x": self.originXY["x"], "y": self.originXY["y"] + progress}


def vertical_up_getCarXY(self, progress):
    return {"x": self.originXY["x"], "y": self.originXY["y"] - progress}


# Парковка – очередь для простаивающих автомобилей
parkingLot = Queue(carQueueSize)


# Класс маршрута (Route)
class Route:
    def __init__(self):
        self.label = ""
        self.paintColor = None
        self.directions = {"orig": None, "south": None, "north": None, "dest": None}
        self.itinerary = []
        self.routeLength = 0
        self.travelTime = 0

    def calcRouteLength(self):
        rtl = 0
        for link in self.itinerary:
            rtl += link.pathLength
        self.routeLength = rtl

    def calcTravelTime(self):
        if speedMode == "theoretical":
            self.calcTravelTimeTheoretical()
        elif speedMode == "actual":
            self.calcTravelTimeActual()
        else:
            self.calcTravelTimeHistorical()

    def calcTravelTimeTheoretical(self):
        tt = 0
        for link in self.itinerary:
            tt += link.travelTime
        self.travelTime = tt

    def calcTravelTimeActual(self):
        n = 0
        total_tt = 0
        for c in carArray:
            if c and c.route == self and c.odometer > 0 and (globalClock - c.departTime) != 0:
                v = (c.odometer / (globalClock - c.departTime)) * speedLimit
                tt = self.routeLength / v if v != 0 else float('inf')
                total_tt += tt
                n += 1
        if n == 0:
            self.travelTime = self.routeLength / speedLimit
        else:
            self.travelTime = total_tt / n

    def calcTravelTimeHistorical(self):
        if Dashboard.counts.get(self.label, 0) == 0:
            self.travelTime = self.routeLength / speedLimit
        else:
            self.travelTime = Dashboard.times[self.label] / Dashboard.counts[self.label]


# Создаём узлы (с произвольными координатами)
orig = Node("orig", x=0, y=0)
dest = DestinationNode("dest", x=100, y=0)
south = Node("south", x=50, y=50)
north = Node("north", x=50, y=-50)

# Создаём участки дороги
aLink = CongestibleLink("a", orig, south, pathLength=270, congestible=True)
ALink = Link("A", orig, north, pathLength=500)
bLink = CongestibleLink("b", north, dest, pathLength=270, congestible=True)
BLink = Link("B", south, dest, pathLength=500)
snLink = Link("sn-bridge", south, north, pathLength=40)
nsLink = Link("ns-bridge", north, south, pathLength=40)

snLink.openToTraffic = False
nsLink.openToTraffic = False

# Подменяем метод getCarXY для некоторых участков
aLink.getCarXY = types.MethodType(horizontal_getCarXY, aLink)
bLink.getCarXY = types.MethodType(horizontal_getCarXY, bLink)
snLink.getCarXY = types.MethodType(vertical_down_getCarXY, snLink)
nsLink.getCarXY = types.MethodType(vertical_up_getCarXY, nsLink)

# Создаём маршруты
Ab = Route()
Ab.label = "Ab"
Ab.paintColor = "#cb0130"
Ab.directions = {"orig": ALink, "south": None, "north": bLink, "dest": parkingLot}
Ab.itinerary = [ALink, bLink]
Ab.calcRouteLength()

aB = Route()
aB.label = "aB"
aB.paintColor = "#1010a5"
aB.directions = {"orig": aLink, "south": BLink, "north": None, "dest": parkingLot}
aB.itinerary = [aLink, BLink]
aB.calcRouteLength()

AB = Route()
AB.label = "AB"
AB.paintColor = "#ffc526"
AB.directions = {"orig": ALink, "south": BLink, "north": nsLink, "dest": parkingLot}
AB.itinerary = [ALink, nsLink, BLink]
AB.calcRouteLength()

ab = Route()
ab.label = "ab"
ab.paintColor = "#4b9b55"
ab.directions = {"orig": aLink, "south": snLink, "north": bLink, "dest": parkingLot}
ab.itinerary = [aLink, snLink, bLink]
ab.calcRouteLength()


# Класс с методами выбора маршрута
class Chooser:
    @staticmethod
    def random(routeList):
        return random.choice(routeList)

    @staticmethod
    def min(routeList):
        minVal = float('inf')
        minRoutes = []
        for route in routeList:
            if route.travelTime < minVal:
                minVal = route.travelTime
                minRoutes = [route]
            elif route.travelTime == minVal:
                minRoutes.append(route)
        return random.choice(minRoutes) if len(minRoutes) > 1 else minRoutes[0]

    @staticmethod
    def probabilistic(routeList):
        valSum = 0
        for route in routeList:
            route.travelTime = 1 / route.travelTime if route.travelTime != 0 else 0
            valSum += route.travelTime
        for route in routeList:
            route.travelTime /= valSum
        r = random.random()
        accum = 0
        for route in routeList:
            accum += route.travelTime
            if accum > r:
                return route
        return routeList[-1]


def chooseRoute():
    if bridgeBlocked:
        availableRoutes = [Ab, aB]
    else:
        availableRoutes = [Ab, aB, AB, ab]

    # Принудительно обновить время для всех маршрутов
    for route in availableRoutes:
        route.calcTravelTime()  # Добавить эту строку

    if routingMode == "random":
        return Chooser.random(availableRoutes)
    else:
        for route in availableRoutes:
            route.calcTravelTime()
        if selectionMethod == "minimum":
            return Chooser.min(availableRoutes)
        else:
            return Chooser.probabilistic(availableRoutes)


# Класс автомобиля
class Car:
    def __init__(self):
        self.serialNumber = None
        self.progress = 0
        self.pastProgress = 0
        self.departTime = 0
        self.arriveTime = 0
        self.route = None
        self.odometer = 0
        self.avatar = Avatar()
        parkingLot.enqueue(self)

    def park(self):
        if self.route:
            print(f"Машина {self.serialNumber} возвращена в парковку")
        self.avatar.set_display("none")
        self.avatar.set_fill("#000")
        self.avatar.set_position(0, 0)
        self.route = None
        self.progress = 0
        self.pastProgress = 0
        self.odometer = 0
        parkingLot.enqueue(self)


# Массив для хранения ссылок на все автомобили (для перебора)
carArray = [None] * carQueueSize


def makeCars(n):
    for i in range(n):
        c = Car()
        c.serialNumber = i
        carArray[i] = c


# Функция синхронизации контролов – в Python эта функция лишь-заглушка
def syncControls():
    pass


# Объект для сбора статистики
class DashboardClass:
    def __init__(self):
        self.departureCount = 0
        self.arrivalCount = 0
        self.counts = {"Ab": 0, "aB": 0, "AB": 0, "ab": 0, "total": 0}
        self.times = {"Ab": 0, "aB": 0, "AB": 0, "ab": 0, "total": 0}

    def colorize(self):
        print("Цвета маршрутов:")
        print("Ab:", Ab.paintColor)
        print("aB:", aB.paintColor)
        print("AB:", AB.paintColor)
        print("ab:", ab.paintColor)
        print("Total: #000")

    def recordDeparture(self):
        self.departureCount += 1

    def recordArrival(self, car):
        self.arrivalCount += 1
        elapsed = (globalClock - car.departTime) / speedLimit
        routeCode = car.route.label if car.route else ""
        if routeCode in self.counts:
            self.counts[routeCode] += 1
            self.times[routeCode] += elapsed
            self.counts["total"] += 1
            self.times["total"] += elapsed
        self.updateReadouts()

    def updateReadouts(self):
        print("Статистика:")
        print("Вых.:", self.departureCount)
        print("Прих.:", self.arrivalCount)
        for key in self.counts:
            avg = "--" if self.counts[key] == 0 else round((self.times[key] / self.counts[key]) / quickestTrip, 3)
            print(f"{key}: кол-во={self.counts[key]}, ср. время={avg}")

    def reset(self):
        self.departureCount = 0
        self.arrivalCount = 0
        for key in self.counts:
            self.counts[key] = 0
        for key in self.times:
            self.times[key] = 0
        self.updateReadouts()

    def activeCars(self):
        # Считаем, сколько автомобилей не находится в парковке
        res = sum(1 for car in carArray if car not in parkingLot.items)
        return res


Dashboard = DashboardClass()


def saveStats():
    routes = ["Ab", "aB", "AB", "ab"]
    print("launchRate:", launchRate, "congestionCoef:", congestionCoef, "bridgeBlocked:", bridgeBlocked)
    for r in routes:
        print(r, Dashboard.counts[r])
    print("total", Dashboard.counts["total"])


def carCensus(sampleInterval):
    routeCounts = {"Ab": 0, "aB": 0, "AB": 0, "ab": 0}
    if Dashboard.departureCount > 10000 and globalClock % sampleInterval == 0:
        for c in carArray:
            if c and c.route:
                routeCounts[c.route.label] += 1
        print(globalClock / speedLimit, routeCounts["Ab"], routeCounts["aB"], routeCounts["AB"], routeCounts["ab"])


def launchCar():
    global nextDeparture, globalClock, model_state
    if orig.has_room() and globalClock >= nextDeparture and modelState == "running" and parkingLot.len > 0:
        nextCar = parkingLot.dequeue()
        if nextCar is None:
            return
        nextCar.departTime = globalClock
        nextCar.route = chooseRoute()
        nextCar.avatar.set_fill(nextCar.route.paintColor)
        nextCar.avatar.set_position(orig.x, orig.y)
        nextCar.avatar.set_display("block")
        orig.accept(nextCar)
        Dashboard.recordDeparture()
        nextDeparture = globalClock + launchTimer(launchRate / speedLimit)


def step():
    global globalClock, model_state
    global numOfSteps
    # Обновляем состояния узлов и участков в случайном порядке
    numOfSteps = numOfSteps + 1

    if numOfSteps == 69:
        pass

    if coinFlip():
        dest.dispatch()
        bLink.drive()
        dest.dispatch()
        BLink.drive()
    else:
        dest.dispatch()
        BLink.drive()
        dest.dispatch()
        bLink.drive()

    if coinFlip():
        north.dispatch()
        ALink.drive()
        north.dispatch()
        snLink.drive()
    else:
        north.dispatch()
        snLink.drive()
        north.dispatch()
        ALink.drive()

    if coinFlip():
        south.dispatch()
        nsLink.drive()
        south.dispatch()
        aLink.drive()
    else:
        south.dispatch()
        aLink.drive()
        south.dispatch()
        nsLink.drive()

    orig.dispatch()
    launchCar()
    orig.dispatch()
    launchCar()
    # Для отладки можно раскомментировать:
    # carCensus(9)
    globalClock += speedLimit

    if modelState == "stopping" and parkingLot.len == carQueueSize:
        # if modelState == "stopping" and Dashboard.activeCars() == 0:
        print("Симуляция остановлена.")
        print(f"Количество шагов = {numOfSteps}")
        # saveStats()  # раскомментировать, если нужна сводка в консоли
        return False
    if modelState == "running" and Dashboard.departureCount >= maxCars:
        modelState = "stopping"
        print("Достигнуто максимальное число автомобилей, остановка запуска.")
    return True


def animate():
    running = True
    while running:
        running = step()
        time.sleep(0.015)  # задержка ~15 мс (примерно 60 кадров/сек)


def init():
    global globalClock
    makeCars(carQueueSize)
    globalClock = 0
    syncControls()
    ALink.update_speed()
    aLink.update_speed()
    BLink.update_speed()
    bLink.update_speed()
    nsLink.update_speed()
    snLink.update_speed()
    Dashboard.colorize()
    # setupForTouch() не требуется в версии для Python


if __name__ == "__main__":
    model_state = "running"
    init()
    animate()
