import sys
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtGui import QPainter, QColor
from PyQt6.QtCore import QTimer

class MovingCircleWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.circle_x = 0  # начальная позиция по X
        self.circle_y = 50  # фиксированная позиция по Y
        self.circle_radius = 20
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.move_circle)
        self.timer.start(30)  # обновление каждые 30 мс

    def move_circle(self):
        # Изменяем позицию круга
        self.circle_x += 2  # скорость перемещения
        if self.circle_x > self.width():
            self.circle_x = -self.circle_radius * 2  # зациклить движение
        self.update()  # вызвать перерисовку

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setBrush(QColor("blue"))
        painter.drawEllipse(self.circle_x, self.circle_y,
                            self.circle_radius * 2, self.circle_radius * 2)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MovingCircleWidget()
    window.resize(400, 200)
    window.show()
    sys.exit(app.exec())
