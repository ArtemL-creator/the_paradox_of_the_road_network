import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtSvg import *
from PyQt5.QtGui import *


class TrafficSimulation(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.initLogic()

    def initUI(self):
        self.setWindowTitle('Traffic Simulation')
        self.setGeometry(100, 100, 1000, 600)

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QHBoxLayout(main_widget)

        # Левая панель со статистикой
        self.stats_table = QTableWidget()
        self.stats_table.setColumnCount(3)
        self.stats_table.setHorizontalHeaderLabels(['Route', 'Count', 'Time'])
        layout.addWidget(self.stats_table, stretch=1)

        # Графическая область
        self.graphics_view = QGraphicsView()
        self.scene = QGraphicsScene()
        self.graphics_view.setScene(self.scene)
        layout.addWidget(self.graphics_view, stretch=3)

        # Панель управления
        control_panel = QVBoxLayout()

        # Кнопки управления
        self.run_button = QPushButton('Go')
        self.reset_button = QPushButton('Reset')
        control_panel.addWidget(self.run_button)
        control_panel.addWidget(self.reset_button)

        # Слайдеры
        self.launch_slider = self.create_slider('Vehicle Launch Rate', 0.55)
        self.congestion_slider = self.create_slider('Congestion Coefficient', 0.55)

        # Выпадающие меню
        self.routing_mode = QComboBox()
        self.routing_mode.addItems(['selfish', 'random'])

        layout.addLayout(control_panel)

        # Инициализация графики
        self.initGraphics()

    def create_slider(self, label, value):
        container = QVBoxLayout()
        lbl = QLabel(label)
        slider = QSlider(Qt.Horizontal)
        slider.setRange(0, 100)
        slider.setValue(int(value * 100))
        output = QLabel(f'{value:.2f}')

        container.addWidget(lbl)
        container.addWidget(slider)
        container.addWidget(output)

        slider.valueChanged.connect(lambda v: output.setText(f'{v / 100:.2f}'))
        return slider

    def initGraphics(self):
        # Отрисовка дорог и элементов
        self.draw_roads()
        self.draw_junctions()
        self.draw_labels()

    def draw_roads(self):
        # Реализация отрисовки дорог с помощью QPainterPath
        path_a = QPainterPath()
        path_a.moveTo(50, 180)
        path_a.lineTo(320, 180)
        self.scene.addPath(path_a, QPen(Qt.black, 2))

        # Аналогично для других элементов (реки, мостов и т.д.)

    def draw_junctions(self):
        origin = QGraphicsEllipseItem(40, 170, 20, 20)
        origin.setBrush(Qt.red)
        self.scene.addItem(origin)

    def draw_labels(self):
        text = self.scene.addText("Origin")
        text.setPos(50, 200)

    def initLogic(self):
        # Инициализация логики симуляции
        self.run_button.clicked.connect(self.toggle_simulation)
        self.reset_button.clicked.connect(self.reset_simulation)

    def toggle_simulation(self):
        # Логика запуска/остановки
        pass

    def reset_simulation(self):
        # Сброс состояния
        pass


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = TrafficSimulation()
    ex.show()
    sys.exit(app.exec_())