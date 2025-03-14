import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QGridLayout, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QSlider, QLineEdit, QComboBox, QFrame
)
from PyQt5.QtCore import Qt
from PyQt5.QtSvg import QSvgWidget

class TrafficApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Traffic Simulation")

        # Центральный виджет и основной layout с отступами
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QGridLayout(central_widget)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(5)

        # --- Блок статистики ---
        stats_frame = QFrame()
        stats_frame.setFrameStyle(QFrame.Panel | QFrame.Raised)
        stats_frame.setLineWidth(2)
        stats_layout = QVBoxLayout(stats_frame)
        stats_layout.setContentsMargins(10, 10, 10, 10)
        stats_layout.setSpacing(5)

        playing_label = QLabel("Playing in traffic")
        font = playing_label.font()
        font.setFamily("Helvetica")
        font.setPointSize(12)
        font.setBold(True)
        playing_label.setFont(font)
        stats_layout.addWidget(playing_label)

        explanation_text = (
            "Roads A and B take a roundabout route but can carry unlimited traffic. "
            "Roads a and b are shorter but subject to congestion: The more cars, the slower they go. "
            "Initially, just two routes lead from Origin to Destination: Ab and aB. Clicking on the bridge in "
            "the middle of the map opens up two more pathways: AB and ab. Will these added routes improve the flow of traffic? "
            "For more information see bit-player.org; source code on Github."
        )
        explanation_label = QLabel(explanation_text)
        explanation_label.setWordWrap(True)
        explanation_label.setMaximumWidth(300)
        stats_layout.addWidget(explanation_label)

        # Таблица статистики
        stats_table_widget = QWidget()
        table_layout = QGridLayout(stats_table_widget)
        table_layout.setSpacing(5)

        header_font = playing_label.font()
        header_font.setPointSize(10)
        header_font.setBold(True)

        route_header = QLabel("Route")
        route_header.setFont(header_font)
        count_header = QLabel("Count")
        count_header.setFont(header_font)
        time_header = QLabel("Time")
        time_header.setFont(header_font)

        table_layout.addWidget(route_header, 0, 0)
        table_layout.addWidget(count_header, 0, 1)
        table_layout.addWidget(time_header, 0, 2)

        routes = ["Ab", "aB", "AB", "ab", "Total"]
        self.count_vars = {}
        self.time_vars = {}
        for i, route in enumerate(routes):
            # Метка маршрута
            route_label = QLabel(route)
            table_layout.addWidget(route_label, i + 1, 0)
            # Метки для количества и времени (их можно обновлять)
            count_label = QLabel("0")
            time_label = QLabel("--")
            table_layout.addWidget(count_label, i + 1, 1)
            table_layout.addWidget(time_label, i + 1, 2)
            self.count_vars[route] = count_label
            self.time_vars[route] = time_label

        stats_layout.addWidget(stats_table_widget)
        main_layout.addWidget(stats_frame, 0, 0)

        # --- Блок визуализации (заглушка) ---
        viz_frame = QFrame()
        viz_frame.setFrameStyle(QFrame.Panel | QFrame.Raised)
        viz_frame.setLineWidth(2)
        viz_layout = QVBoxLayout(viz_frame)
        viz_layout.setContentsMargins(10, 10, 10, 10)
        viz_layout.setSpacing(5)
        # Создаем QSvgWidget для отображения SVG
        self.svg_widget = QSvgWidget()
        svg_content = """
        <svg id="the-svg" 
         xmlns="http://www.w3.org/2000/svg" 
         xmlns:xlink="http://www.w3.org/1999/xlink"
         width="640px" height="400px" viewBox="0 0 640 400">
         <style type="text/css"><![CDATA[body {
              font-family: sans-serif;
              font-size: 1em;
            }
            
            h2, h3, h4, h5 {
              font-family: sans-serif;
              color: #a0a0a0;
            }
            
            h3 {
              text-align: left;
              font-weight: 400;
              font-size: 2em;
              margin: 0.25em;
            }
            
            
            p, li {
              font-size: 1em;
              text-align: left;
              font-family: serif;
              line-height: 1.2em;
              color: #808080;
            }
            
            a {
              text-decoration: none;
              color: #5888e2;
              cursor: default;
            }
            
            a:hover {
              color: #ff8000;
            }
            
            div#content {
              position: relative;
              margin: auto;
              width: 640px;
            }
            
            h3 {
              position: absolute;
              top: 0px;
              left: 10px;
            }
            
            div#explanation {
              position: absolute;
              top: 50px;
              left: 20px;
              width: 360px;
              font-family: sans-serif;
              color: #a0a0a0;
              font-size: 0.7em;
              
            }
            
            #stats {
              position: relative;
              height: 140px;
              background-color: #F4F5F3;
              margin-bottom: 7px;
              margin-top: 10px;
            }
            
            #stats table {
              position: absolute;
              table-layout: fixed;
              right: 15px;
              top: 5px;
              font-family: sans-serif;
              font-size: 0.85em;
              font-weight: 600;
            }
            
            #stats th {
              font-weight: 600;
              color: darkgrey;
            }
            
            #stats .count-cell, .time-cell {
              width: 80px;
              text-align: right;
            }
            
            #stats td {
              color: white;
              vertical-align: middle;
              padding: 2px;
            }
            
            #the-viz {
              position: relative;
              width: 640px;
              height: 400px;
            }
            
            #the-controls {
              position: relative;
              height: 160px;
              margin-top: 7px;
              background-color: #F4F5F3;
            }
            
            button {
              width: 50px;
            }
            
            #the-run-button {
              display: block;
              position: absolute;
              right: 10px;
              top: 10px;
            }
            
            #the-reset-button {
              display: block;
              position: absolute;
              right: 10px;
              top: 35px;
              
            }
            
            #max-cars-div {
              position: absolute;
              right: 10px;
              top: 70px;  
            }
            
            #max-cars-input {
              width: 50px;
            }
            
            
            #the-controls .label {
              display: block;
              font-family: sans-serif;
              font-weight: 500;
              font-size: 0.85em;
              color: darkgrey;
              margin-bottom: 5px;
            }
            
            #the-controls .slider-output {
              width: 30px;
              position: absolute;
              left: 170px;
              top: 0px;
              font-family: sans-serif;
              font-weight: 600;
              font-size: 0.85em;
              color: darkgrey;
            }
            
            #launch-rate-slider-div {
              display: block;
              width: 210px;
              position: absolute;
              left: 10px;
              top: 10px;    
            }
            
            #congestion-slider-div {
              display: block;
              width: 210px;
              position: absolute;
              left: 10px;
              top: 60px;    
            }
            
            .slider {
              width: 200px;
              margin: 0px;  
            }
            
            
            #launch-menu-div {
              width: 150px;
              position: absolute;
              left: 10px;
              top: 110px;  
            }
            
            #mode-menu-div {
              display: block;
              width: 160px;
              position: absolute;
              left: 300px;
              top: 10px;  
            }
            
            #speed-menu-div {
              width: 160px;
              position: absolute;
              left: 300px;
              top: 60px;  
            }
            
            #selection-method-menu-div {
              width: 160px;
              position: absolute;
              left: 300px;
              top: 110px;  
            }
            
            select {
              display: block;
              width: 150px;
            }
            
            
            #geek-out {
              font-family: sans-serif;
              font-size: 9px;
              position: absolute;
              bottom: 3px;
              right: 5px;
              cursor: default;
              color: blue;
            }
            
            #hint-toggle {
              font-family: sans-serif;
              font-size: 9px;
              position: absolute;
              bottom: 3px;
              right: 80px;
              cursor: default;
              color: blue;
            }
            
            
            #geek-out:hover, #hint-toggle:hover {
              color: orange;
            }
            
            .hidden-control {
              display: none;
            }
            
            path.thin-road {
              stroke-width: 4px;
              stroke: #f5f5f5;
              fill: none;
            }
            
            path.wide-road {
              stroke-width: 9px;
              stroke: #f5f5f5;
              stroke-linecap: round;
              fill: none;
            }
            
            path#river {
              stroke: #73acd0;
              stroke-width: 25px;
              fill: none;
            }
            
            circle.junction {
              fill: #f5f5f5;
              stroke-width: 1px;
              stroke: #aaaaaa;
            }
            
            path#sn-bridge.closed,
            path#ns-bridge.closed {
              stroke-opacity: 0.2;
            }
            
            path#barricade {
              stroke-width: 3px;
              stroke: red;
              fill: none;
              stroke-linecap: round;
            }
            
            path#barricade.hidden {
              display: none;
            }
            
            text {  
              font-family: sans-serif;
              fill: #575757;
            }
         ]]></style>
          <g id="the-coordinate-frame" transform="translate(0, 400) scale(1, -1)">
            <rect id="the-frame" x="0" y="0" width="640" height="400" fill="#b5b2a3" stroke="#717171"></rect>
            <path id="river" d="M -10 190 C 20 220 200 220 320 200 S 620 180 650 210"/>
            <path id="a" class="thin-road" d="M 50 180 L 320 180"/>
            <path id="b" class="thin-road" d="M 320 220 L 590 220"/>
            <path id="A" class="wide-road" d="M 50 180 C 65 445 295 444 320 220" />
            <path id="B" class="wide-road" d="M 320 180 C 345 -44 575 -45 590 220" />
            <path id="sn-bridge" class="wide-road closed" d="M 320 180 L 320 220" />
            <path id="ns-bridge" class="wide-road closed" d="M 320 220 L 320 180" />
            <path id="barricade" d="M 315 195 L 325 205 M 315 205 L 325 195" />
            <circle id="orig" class="junction" cx="50" cy="180" r="10" />
            <circle id="dest" class="junction" cx="590" cy="220" r="10" />
            <circle id="south" class="junction" cx="320" cy="180" r="6" />
            <circle id="north" class="junction" cx="320" cy="220" r="6" />
         </g>
          <text x="50" y="247" text-anchor="middle">Origin</text>
          <text x="590" y="165" text-anchor="middle">Destination</text>
          <text x="185" y="40" text-anchor="middle">A</text>
          <text x="185" y="235" text-anchor="middle">a</text>
          <text x="455" y="175" text-anchor="middle">b</text>
          <text x="455" y="373" text-anchor="middle">B</text>
         </svg>        
        """
        # Вариант загрузки из строки:
        self.svg_widget.renderer().load(svg_content.encode('utf-8'))
        # Если у вас SVG сохранён в файле, можно использовать:
        # self.svg_widget.load("traffic.svg")

        viz_layout.addWidget(self.svg_widget)
        main_layout.addWidget(viz_frame, 0, 1)

        # --- Блок управления ---
        controls_frame = QFrame()
        controls_frame.setFrameStyle(QFrame.Panel | QFrame.Raised)
        controls_frame.setLineWidth(2)
        controls_layout = QGridLayout(controls_frame)
        controls_layout.setContentsMargins(10, 10, 10, 10)
        controls_layout.setSpacing(5)

        # Кнопки "Go" и "Reset"
        self.go_button = QPushButton("Go")
        self.resetButton = QPushButton("Reset")
        controls_layout.addWidget(self.go_button, 0, 0)
        controls_layout.addWidget(self.resetButton, 0, 1)

        # Слайдер "Vehicle Launch Rate"
        launch_rate_frame = QWidget()
        launch_rate_layout = QHBoxLayout(launch_rate_frame)
        launch_rate_layout.setContentsMargins(0, 0, 0, 0)
        launch_rate_layout.setSpacing(5)
        launch_rate_label = QLabel("Vehicle Launch Rate")
        launch_rate_layout.addWidget(launch_rate_label)
        self.launch_rate_slider = QSlider(Qt.Horizontal)
        self.launch_rate_slider.setRange(0, 100)  # 0.00 - 1.00 с шагом 0.01
        self.launch_rate_slider.setValue(55)
        self.launch_rate_slider.setSingleStep(1)
        launch_rate_layout.addWidget(self.launch_rate_slider)
        self.launch_rate_value_label = QLabel("0.55")
        launch_rate_layout.addWidget(self.launch_rate_value_label)
        self.launch_rate_slider.valueChanged.connect(
            lambda val: self.launch_rate_value_label.setText(f"{val / 100:.2f}")
        )
        controls_layout.addWidget(launch_rate_frame, 1, 0, 1, 2)

        # Слайдер "Congestion Coefficient"
        congestion_frame = QWidget()
        congestion_layout = QHBoxLayout(congestion_frame)
        congestion_layout.setContentsMargins(0, 0, 0, 0)
        congestion_layout.setSpacing(5)
        congestion_label = QLabel("Congestion Coefficient")
        congestion_layout.addWidget(congestion_label)
        self.congestion_slider = QSlider(Qt.Horizontal)
        self.congestion_slider.setRange(0, 100)
        self.congestion_slider.setValue(55)
        self.congestion_slider.setSingleStep(1)
        congestion_layout.addWidget(self.congestion_slider)
        self.congestion_value_label = QLabel("0.55")
        congestion_layout.addWidget(self.congestion_value_label)
        self.congestion_slider.valueChanged.connect(
            lambda val: self.congestion_value_label.setText(f"{val / 100:.2f}")
        )
        controls_layout.addWidget(congestion_frame, 2, 0, 1, 2)

        # Выпадающее меню "Launch Timing"
        launch_timing_frame = QWidget()
        launch_timing_layout = QHBoxLayout(launch_timing_frame)
        launch_timing_layout.setContentsMargins(0, 0, 0, 0)
        launch_timing_layout.setSpacing(5)
        launch_timing_label = QLabel("Launch Timing")
        launch_timing_layout.addWidget(launch_timing_label)
        self.launch_timing_combo = QComboBox()
        launch_timing_options = ["poisson", "uniform", "periodic"]
        self.launch_timing_combo.addItems(launch_timing_options)
        launch_timing_layout.addWidget(self.launch_timing_combo)
        controls_layout.addWidget(launch_timing_frame, 3, 0, 1, 2)

        # Выпадающее меню "Routing Mode"
        routing_mode_frame = QWidget()
        routing_mode_layout = QHBoxLayout(routing_mode_frame)
        routing_mode_layout.setContentsMargins(0, 0, 0, 0)
        routing_mode_layout.setSpacing(5)
        routing_mode_label = QLabel("Routing Mode")
        routing_mode_layout.addWidget(routing_mode_label)
        self.routing_mode_combo = QComboBox()
        routing_mode_options = ["selfish", "random"]
        self.routing_mode_combo.addItems(routing_mode_options)
        routing_mode_layout.addWidget(self.routing_mode_combo)
        controls_layout.addWidget(routing_mode_frame, 4, 0, 1, 2)

        # Выпадающее меню "Speed Measurement"
        speed_menu_frame = QWidget()
        speed_menu_layout = QHBoxLayout(speed_menu_frame)
        speed_menu_layout.setContentsMargins(0, 0, 0, 0)
        speed_menu_layout.setSpacing(5)
        speed_menu_label = QLabel("Speed Measurement")
        speed_menu_layout.addWidget(speed_menu_label)
        self.speed_combo = QComboBox()
        speed_menu_options = ["theoretical", "actual", "historical"]
        self.speed_combo.addItems(speed_menu_options)
        speed_menu_layout.addWidget(self.speed_combo)
        controls_layout.addWidget(speed_menu_frame, 5, 0, 1, 2)

        # Выпадающее меню "Route Selection Method"
        selection_method_frame = QWidget()
        selection_method_layout = QHBoxLayout(selection_method_frame)
        selection_method_layout.setContentsMargins(0, 0, 0, 0)
        selection_method_layout.setSpacing(5)
        selection_method_label = QLabel("Route Selection Method")
        selection_method_layout.addWidget(selection_method_label)
        self.selection_method_combo = QComboBox()
        selection_method_options = ["minimum", "weighted-probability"]
        self.selection_method_combo.addItems(selection_method_options)
        selection_method_layout.addWidget(self.selection_method_combo)
        controls_layout.addWidget(selection_method_frame, 6, 0, 1, 2)

        # Поле ввода "Max Cars"
        max_cars_frame = QWidget()
        max_cars_layout = QHBoxLayout(max_cars_frame)
        max_cars_layout.setContentsMargins(0, 0, 0, 0)
        max_cars_layout.setSpacing(5)
        max_cars_label = QLabel("Max Cars")
        max_cars_layout.addWidget(max_cars_label)
        self.max_cars_entry = QLineEdit()
        max_cars_layout.addWidget(self.max_cars_entry)
        controls_layout.addWidget(max_cars_frame, 7, 0, 1, 2)

        # Дополнительные кнопки
        more_controls_button = QPushButton("More controls")
        hide_hover_button = QPushButton("Hide hover hints")
        controls_layout.addWidget(more_controls_button, 8, 0)
        controls_layout.addWidget(hide_hover_button, 8, 1)

        main_layout.addWidget(controls_frame, 1, 0)

        # --- Блок подписи ---
        caption_frame = QFrame()
        caption_frame.setFrameStyle(QFrame.Panel | QFrame.Raised)
        caption_frame.setLineWidth(2)
        caption_layout = QVBoxLayout(caption_frame)
        caption_layout.setContentsMargins(10, 10, 10, 10)
        caption_label = QLabel("Здесь будет подпись")
        caption_label.setAlignment(Qt.AlignCenter)
        caption_layout.addWidget(caption_label)
        main_layout.addWidget(caption_frame, 1, 1)

        # Настройка пропорций столбцов и строк
        main_layout.setColumnStretch(0, 1)
        main_layout.setColumnStretch(1, 1)
        main_layout.setRowStretch(0, 1)
        main_layout.setRowStretch(1, 0)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = TrafficApp()
    window.show()
    sys.exit(app.exec_())
