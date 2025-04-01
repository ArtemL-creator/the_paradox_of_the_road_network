# Класс для симуляции “аватара” (визуальное представление автомобиля)
class Avatar:
    def __init__(self, x=0, y=0, r=1, fill="#000", display="none"):
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