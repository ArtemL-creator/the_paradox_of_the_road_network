class RoadEvent:
    def __init__(self, *, link, lane, start_time, duration):
        """
        link    – участок дороги, на котором происходит ремонт,
        lane    – конкретная полоса (объект класса Lane),
        start_time – такт симуляции, когда начинается ремонт,
        duration   – длительность ремонта (в тактах)
        """
        self.link = link
        self.lane = lane
        self.start_time = start_time
        self.duration = duration
        self.active = False

    def update(self, current_time):
        # Если наступило время ремонта и ремонт ещё не активирован – активируем
        if current_time >= self.start_time and current_time < self.start_time + self.duration:
            if not self.active:
                self.lane.block()
                self.active = True
                print(f"[ROAD EVENT] Ремонт начался на участке {self.link.id}, полоса {self.lane.lane_id} в такт {current_time}")
        # Если время ремонта закончилось и событие активно – снимаем блокировку
        elif self.active and current_time >= self.start_time + self.duration:
            self.lane.unblock()
            self.active = False
            print(f"[ROAD EVENT] Ремонт завершён на участке {self.link.id}, полоса {self.lane.lane_id} в такт {current_time}")