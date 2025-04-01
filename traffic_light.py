class TrafficLight:
    def __init__(self, phase1_duration: int, phase2_duration: int):
        self.phase1_duration = phase1_duration
        self.phase2_duration = phase2_duration
        self.timer = 0
        self.phase = 1  # Фаза 1: для определённых направлений зелёный; Фаза 2: для остальных – зелёный

    def update(self):
        self.timer += 1
        if self.phase == 1 and self.timer >= self.phase1_duration:
            self.phase = 2
            self.timer = 0
        elif self.phase == 2 and self.timer >= self.phase2_duration:
            self.phase = 1
            self.timer = 0

    def get_phase(self) -> int:
        return self.phase
