import sys
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QSlider, QComboBox, QTableWidget, QTableWidgetItem

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Styled Interface")
        self.setGeometry(100, 100, 800, 600)

        # Create main layout
        layout = QVBoxLayout()

        # Create a title
        self.title = QLabel("Title Example")
        self.title.setStyleSheet("font-family: sans-serif; font-size: 2em; color: #a0a0a0;")
        layout.addWidget(self.title)

        # Create a h3-like label with specific styling
        self.h3_label = QLabel("Section Title")
        self.h3_label.setStyleSheet("font-family: sans-serif; color: #a0a0a0; text-align: left; font-weight: 400; font-size: 2em; margin: 0.25em;")
        layout.addWidget(self.h3_label)

        # Create the stats section with a table
        self.stats_table = QTableWidget(3, 2)  # 3 rows, 2 columns
        self.stats_table.setHorizontalHeaderLabels(["Label", "Value"])
        self.stats_table.setItem(0, 0, QTableWidgetItem("Item 1"))
        self.stats_table.setItem(0, 1, QTableWidgetItem("100"))
        self.stats_table.setItem(1, 0, QTableWidgetItem("Item 2"))
        self.stats_table.setItem(1, 1, QTableWidgetItem("200"))
        self.stats_table.setItem(2, 0, QTableWidgetItem("Item 3"))
        self.stats_table.setItem(2, 1, QTableWidgetItem("300"))
        self.stats_table.setStyleSheet("""
            QTableWidget {
                font-family: sans-serif;
                font-size: 0.85em;
                font-weight: 600;
                background-color: #F4F5F3;
            }
            QTableWidget QHeaderView::section {
                background-color: #F4F5F3;
                font-weight: 600;
                color: darkgrey;
            }
            QTableWidgetItem {
                padding: 5px;
                text-align: right;
            }
        """)
        layout.addWidget(self.stats_table)

        # Create sliders for controls
        self.launch_rate_slider = QSlider(Qt.Orientation.Horizontal)
        self.launch_rate_slider.setRange(0, 100)
        self.launch_rate_slider.setValue(50)
        self.launch_rate_slider.setStyleSheet("QSlider { width: 200px; }")
        layout.addWidget(self.launch_rate_slider)

        self.congestion_slider = QSlider(Qt.Orientation.Horizontal)
        self.congestion_slider.setRange(0, 100)
        self.congestion_slider.setValue(50)
        self.congestion_slider.setStyleSheet("QSlider { width: 200px; }")
        layout.addWidget(self.congestion_slider)

        # Create buttons
        self.run_button = QPushButton("Run")
        self.run_button.setStyleSheet("""
            QPushButton {
                width: 50px;
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        layout.addWidget(self.run_button)

        self.reset_button = QPushButton("Reset")
        self.reset_button.setStyleSheet("""
            QPushButton {
                width: 50px;
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #e53935;
            }
        """)
        layout.addWidget(self.reset_button)

        # Create combo boxes (dropdown menus)
        self.mode_menu = QComboBox()
        self.mode_menu.addItems(["Mode 1", "Mode 2", "Mode 3"])
        self.mode_menu.setStyleSheet("QComboBox { width: 150px; }")
        layout.addWidget(self.mode_menu)

        self.speed_menu = QComboBox()
        self.speed_menu.addItems(["Speed 1", "Speed 2", "Speed 3"])
        self.speed_menu.setStyleSheet("QComboBox { width: 150px; }")
        layout.addWidget(self.speed_menu)

        self.selection_method_menu = QComboBox()
        self.selection_method_menu.addItems(["Method 1", "Method 2", "Method 3"])
        self.selection_method_menu.setStyleSheet("QComboBox { width: 150px; }")
        layout.addWidget(self.selection_method_menu)

        # Set the layout to the window
        self.setLayout(layout)

        # Apply some global styles
        self.setStyleSheet("""
            body {
                font-family: sans-serif;
                font-size: 1em;
            }
            QLabel {
                font-family: sans-serif;
                color: #808080;
            }
            #geek-out {
                font-family: sans-serif;
                font-size: 8px;
                position: absolute;
                bottom: 3px;
                right: 5px;
            }
        """)

        # Add a geek-out label at the bottom
        self.geek_out_label = QLabel("Geek Out")
        self.geek_out_label.setStyleSheet("font-family: sans-serif; font-size: 8px; position: absolute; bottom: 3px; right: 5px;")
        self.geek_out_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom)
        self.layout().addWidget(self.geek_out_label)

# Create and run the application
app = QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec())
