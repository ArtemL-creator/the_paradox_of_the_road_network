import tkinter as tk
import tkinter.ttk as ttk # Для стилизованных виджетов (если хотите более современный вид)

class TrafficApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Traffic Simulation")

        # Главный контейнер
        content_frame = ttk.Frame(self, padding="12 12 12 12") # Отступы
        content_frame.grid(column=0, row=0, sticky=(tk.N, tk.W, tk.E, tk.S))
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        # --- Блок статистики ---
        stats_frame = ttk.Frame(content_frame, padding="10 10 10 10", borderwidth=2, relief=tk.GROOVE)
        stats_frame.grid(column=0, row=0, sticky=(tk.N, tk.W))

        ttk.Label(stats_frame, text="Playing in traffic", font=('Helvetica', 12, 'bold')).grid(column=0, row=0, columnspan=3, sticky=(tk.NW))

        explanation_text = "Roads A and B take a roundabout route but can carry unlimited traffic. Roads a and b are shorter but subject to congestion: The more cars, the slower they go. Initially, just two routes lead from Origin to Destination: Ab and aB. Clicking on the bridge in the middle of the map opens up two more pathways: AB and ab. Will these added routes improve the flow of traffic? For more information see bit-player.org; source code on Github."
        ttk.Label(stats_frame, text=explanation_text, wraplength=300, justify=tk.LEFT).grid(column=0, row=1, columnspan=3, sticky=(tk.W))

        # Таблица статистики
        stats_table_frame = ttk.Frame(stats_frame)
        stats_table_frame.grid(column=0, row=2, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S))

        ttk.Label(stats_table_frame, text="Route", font=('Helvetica', 10, 'bold')).grid(column=0, row=0, padx=5, pady=5, sticky=tk.W)
        ttk.Label(stats_table_frame, text="Count", font=('Helvetica', 10, 'bold')).grid(column=1, row=0, padx=5, pady=5, sticky=tk.W)
        ttk.Label(stats_table_frame, text="Time", font=('Helvetica', 10, 'bold')).grid(column=2, row=0, padx=5, pady=5, sticky=tk.W)

        routes = ["Ab", "aB", "AB", "ab", "Total"]
        self.count_vars = {}
        self.time_vars = {}
        for i, route in enumerate(routes):
            ttk.Label(stats_table_frame, text=route).grid(column=0, row=i+1, padx=5, pady=2, sticky=tk.W)
            self.count_vars[route] = tk.StringVar(value="0")
            self.time_vars[route] = tk.StringVar(value="--")
            ttk.Label(stats_table_frame, textvariable=self.count_vars[route]).grid(column=1, row=i+1, padx=5, pady=2, sticky=tk.W)
            ttk.Label(stats_table_frame, textvariable=self.time_vars[route]).grid(column=2, row=i+1, padx=5, pady=2, sticky=tk.W)

        # --- Блок визуализации (заглушка, нужно будет Canvas для рисования) ---
        viz_frame = ttk.Frame(content_frame, padding="10 10 10 10", borderwidth=2, relief=tk.GROOVE)
        viz_frame.grid(column=1, row=0, sticky=(tk.N, tk.E, tk.S))
        ttk.Label(viz_frame, text="Здесь будет визуализация (SVG)").pack(pady=20) # Заглушка

        # --- Блок управления ---
        controls_frame = ttk.Frame(content_frame, padding="10 10 10 10", borderwidth=2, relief=tk.GROOVE)
        controls_frame.grid(column=0, row=1, columnspan=2, sticky=(tk.W, tk.E, tk.S))

        ttk.Button(controls_frame, text="Go").grid(column=0, row=0, padx=5, pady=5, sticky=tk.W)
        ttk.Button(controls_frame, text="Reset").grid(column=1, row=0, padx=5, pady=5, sticky=tk.W)

        # Слайдер "Vehicle Launch Rate"
        launch_rate_frame = ttk.Frame(controls_frame)
        launch_rate_frame.grid(column=0, row=1, columnspan=2, padx=5, pady=5, sticky=tk.W)
        ttk.Label(launch_rate_frame, text="Vehicle Launch Rate").grid(column=0, row=0, sticky=tk.W)
        self.launch_rate_var = tk.DoubleVar(value=0.55)
        launch_rate_slider = tk.Scale(launch_rate_frame, orient=tk.HORIZONTAL, from_=0.0, to=1.0, resolution=0.01, variable=self.launch_rate_var)
        launch_rate_slider.grid(column=0, row=1, sticky=(tk.W, tk.E))
        ttk.Label(launch_rate_frame, textvariable=self.launch_rate_var).grid(column=1, row=1, padx=5, sticky=tk.W)

        # Слайдер "Congestion Coefficient"
        congestion_frame = ttk.Frame(controls_frame)
        congestion_frame.grid(column=0, row=2, columnspan=2, padx=5, pady=5, sticky=tk.W)
        ttk.Label(congestion_frame, text="Congestion Coefficient").grid(column=0, row=0, sticky=tk.W)
        self.congestion_var = tk.DoubleVar(value=0.55)
        congestion_slider = tk.Scale(congestion_frame, orient=tk.HORIZONTAL, from_=0.0, to=1.0, resolution=0.01, variable=self.congestion_var)
        congestion_slider.grid(column=0, row=1, sticky=(tk.W, tk.E))
        ttk.Label(congestion_frame, textvariable=self.congestion_var).grid(column=1, row=1, padx=5, sticky=tk.W)

        # Выпадающие меню (заглушки)
        launch_timing_frame = ttk.Frame(controls_frame)
        launch_timing_frame.grid(column=0, row=3, columnspan=2, padx=5, pady=5, sticky=tk.W)
        ttk.Label(launch_timing_frame, text="Launch Timing").grid(column=0, row=0, sticky=tk.W)
        launch_timing_options = ["poisson", "uniform", "periodic"]
        self.launch_timing_var = tk.StringVar(value=launch_timing_options[0])
        launch_timing_menu = ttk.OptionMenu(launch_timing_frame, self.launch_timing_var, *launch_timing_options)
        launch_timing_menu.grid(column=0, row=1, sticky=tk.W)

        routing_mode_frame = ttk.Frame(controls_frame)
        routing_mode_frame.grid(column=0, row=4, columnspan=2, padx=5, pady=5, sticky=tk.W)
        ttk.Label(routing_mode_frame, text="Routing Mode").grid(column=0, row=0, sticky=tk.W)
        routing_mode_options = ["selfish", "random"]
        self.routing_mode_var = tk.StringVar(value=routing_mode_options[0])
        routing_mode_menu = ttk.OptionMenu(routing_mode_frame, self.routing_mode_var, *routing_mode_options)
        routing_mode_menu.grid(column=0, row=1, sticky=tk.W)

        speed_menu_frame = ttk.Frame(controls_frame)
        speed_menu_frame.grid(column=0, row=5, columnspan=2, padx=5, pady=5, sticky=tk.W)
        ttk.Label(speed_menu_frame, text="Speed Measurement").grid(column=0, row=0, sticky=tk.W)
        speed_menu_options = ["theoretical", "actual", "historical"]
        self.speed_menu_var = tk.StringVar(value=speed_menu_options[0])
        speed_menu = ttk.OptionMenu(speed_menu_frame, self.speed_menu_var, *speed_menu_options)
        speed_menu.grid(column=0, row=1, sticky=tk.W)

        selection_method_frame = ttk.Frame(controls_frame)
        selection_method_frame.grid(column=0, row=6, columnspan=2, padx=5, pady=5, sticky=tk.W)
        ttk.Label(selection_method_frame, text="Route Selection Method").grid(column=0, row=0, sticky=tk.W)
        selection_method_options = ["minimum", "weighted-probability"]
        self.selection_method_var = tk.StringVar(value=selection_method_options[0])
        selection_method_menu = ttk.OptionMenu(selection_method_frame, self.selection_method_var, *selection_method_options)
        selection_method_menu.grid(column=0, row=1, sticky=tk.W)

        # Поле ввода "Max Cars"
        max_cars_frame = ttk.Frame(controls_frame)
        max_cars_frame.grid(column=0, row=7, columnspan=2, padx=5, pady=5, sticky=tk.W)
        ttk.Label(max_cars_frame, text="Max Cars").grid(column=0, row=0, sticky=tk.W)
        self.max_cars_entry = ttk.Entry(max_cars_frame)
        self.max_cars_entry.grid(column=0, row=1, sticky=tk.W)

        ttk.Button(controls_frame, text="More controls").grid(column=0, row=8, padx=5, pady=5, sticky=tk.W) # Функциональность "geeky hidden-control" нужно будет реализовать отдельно
        ttk.Button(controls_frame, text="Hide hover hints").grid(column=1, row=8, padx=5, pady=5, sticky=tk.W) # Функциональность "hint-toggle"  нужно будет реализовать отдельно

        # --- Блок подписи ---
        caption_frame = ttk.Frame(content_frame, padding="10 10 10 10", borderwidth=2, relief=tk.GROOVE)
        caption_frame.grid(column=1, row=1, sticky=(tk.W, tk.E, tk.S))
        ttk.Label(caption_frame, text="Здесь будет подпись").pack(pady=10) # Заглушка

        # Заполнение отступами для равномерного распределения
        for child in content_frame.winfo_children():
            child.grid_configure(padx=5, pady=5)

if __name__ == "__main__":
    app = TrafficApp()
    app.mainloop()

