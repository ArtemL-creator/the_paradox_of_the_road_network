import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import subprocess
import sys
import os
import threading # Для запуска симуляции в отдельном потоке

# --- Путь к вашему основному скрипту симуляции ---
SIMULATION_SCRIPT = 'traffic.py'

class RedirectText:
    """Класс для перенаправления вывода stdout/stderr в текстовый виджет Tkinter."""
    def __init__(self, widget, tag_success="green", tag_error="red"):
        self.widget = widget
        self.tag_success = tag_success
        self.tag_error = tag_error
        self.widget.tag_config(self.tag_success, foreground="green")
        self.widget.tag_config(self.tag_error, foreground="red")

    def write(self, text):
        self.widget.insert(tk.END, text)
        self.widget.see(tk.END) # Прокручиваем к концу
        self.widget.update_idletasks() # Обновляем виджет немедленно

    def flush(self):
        pass # Необходимо для совместимости с sys.stdout

def update_selection_method_state(*args):
    """Обновляет состояние виджета выбора метода маршрута в зависимости от режима маршрутизации."""
    if routing_mode_var.get() == "random":
        selection_method_combobox.config(state="disabled")
    else: # "selfish"
        selection_method_combobox.config(state="readonly")

def start_simulation_thread():
    """Запускает симуляцию в отдельном потоке, чтобы GUI не зависал."""
    # Очищаем текстовый вывод перед новым запуском
    output_text_widget.delete(1.0, tk.END)
    output_text_widget.insert(tk.END, "Запуск симуляции...\n", "green")
    output_text_widget.update_idletasks()

    # Отключаем кнопку запуска, чтобы предотвратить множественные запуски
    run_button.config(state="disabled")

    # Создаем поток для запуска run_simulation
    simulation_thread = threading.Thread(target=run_simulation)
    simulation_thread.daemon = True # Поток завершится, когда закроется главное окно
    simulation_thread.start()

def run_simulation():
    """Функция для сбора параметров из GUI и запуска симуляции."""
    # Собираем значения из виджетов
    try:
        bridge_blocked_val = bridge_blocked_var.get() == "True"
        traffic_light_on_val = traffic_light_on_var.get() == "True"
        road_events_on_val = road_events_on_var.get() == "True"
        is_writing_val = is_writing_var.get() == "True"

        routing_mode_val = routing_mode_var.get()
        selection_method_val = selection_method_var.get()
        speed_mode_val = speed_mode_var.get()

        launch_rate_val = float(launch_rate_entry.get())
        congestion_coef_val = float(congestion_coef_entry.get())

        if not (0.0 <= launch_rate_val <= 1.0):
            messagebox.showerror("Ошибка ввода", "Интенсивность запуска (Launch Rate) должна быть между 0.0 и 1.0.")
            return
        if not (0.0 <= congestion_coef_val <= 1.0):
            messagebox.showerror("Ошибка ввода", "Коэффициент сопротивления (Congestion Coef) должен быть между 0.0 и 1.0.")
            return

    except ValueError:
        messagebox.showerror("Ошибка ввода", "Пожалуйста, введите корректные числовые значения для Launch Rate и Congestion Coef.")
        root.after(100, lambda: run_button.config(state="normal")) # Включаем кнопку обратно
        return
    except Exception as e:
        messagebox.showerror("Ошибка", f"Произошла непредвиденная ошибка при сборе параметров: {e}")
        root.after(100, lambda: run_button.config(state="normal"))
        return

    # Формируем команду для запуска traffic.py
    command = [sys.executable, SIMULATION_SCRIPT]

    command.append('--bridge_blocked'); command.append(str(bridge_blocked_val))
    command.append('--traffic_light_on'); command.append(str(traffic_light_on_val))
    command.append('--road_events_on'); command.append(str(road_events_on_val))
    command.append('--routing_mode'); command.append(routing_mode_val)
    command.append('--speed_mode'); command.append(speed_mode_val)

    if routing_mode_val != "random":
        command.append('--selection_method'); command.append(selection_method_val)

    command.append('--launch_rate'); command.append(str(launch_rate_val))
    command.append('--congestion_coef'); command.append(str(congestion_coef_val))
    command.append('--is_writing'); command.append(str(is_writing_val))

    # Выводим параметры запуска в текстовое поле GUI
    output_text_widget.insert(tk.END, f"\nЗапуск симуляции с параметрами:\n", "green")
    for i in range(0, len(command), 2):
        if i + 1 < len(command):
            output_text_widget.insert(tk.END, f"  {command[i].lstrip('--')}: {command[i+1]}\n")
    output_text_widget.see(tk.END) # Прокручиваем к концу
    output_text_widget.update_idletasks()


    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8')

        # Читаем вывод построчно и направляем в GUI
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                output_text_widget.insert(tk.END, output)
                output_text_widget.see(tk.END) # Прокручиваем к концу
                output_text_widget.update_idletasks() # Обновляем виджет немедленно

        stderr_output = process.stderr.read() # Читаем весь stderr после завершения stdout

        if process.returncode == 0:
            output_text_widget.insert(tk.END, "\nСимуляция завершена успешно!\n", "green")
            root.after(100, lambda: messagebox.showinfo("Завершение симуляции", "Симуляция завершена успешно!"))
        else:
            output_text_widget.insert(tk.END, f"\nСимуляция завершилась с ошибкой. Код: {process.returncode}\n", "red")
            output_text_widget.insert(tk.END, "--- Ошибки симуляции (stderr) ---\n", "red")
            output_text_widget.insert(tk.END, stderr_output, "red")
            root.after(100, lambda: messagebox.showerror("Ошибка симуляции", f"Симуляция завершилась с ошибкой. Код: {process.returncode}\nСм. вывод в GUI для подробностей."))

    except FileNotFoundError:
        output_text_widget.insert(tk.END, f"Ошибка: Скрипт симуляции не найден по пути: {SIMULATION_SCRIPT}\n", "red")
        root.after(100, lambda: messagebox.showerror("Ошибка", f"Скрипт симуляции не найден по пути: {SIMULATION_SCRIPT}"))
    except Exception as e:
        output_text_widget.insert(tk.END, f"Произошла ошибка при запуске симуляции: {e}\n", "red")
        root.after(100, lambda: messagebox.showerror("Ошибка запуска", f"Произошла ошибка при запуске симуляции: {e}"))
    finally:
        # Всегда включаем кнопку запуска обратно после завершения или ошибки
        root.after(100, lambda: run_button.config(state="normal"))


# --- Создание графического интерфейса ---
root = tk.Tk()
root.title("Настройки Симуляции Транспорта")
root.geometry("800x700") # Увеличим размер окна, чтобы вместить текстовое поле

# Создаем фрейм для удобства размещения элементов
frame = ttk.Frame(root, padding="10")
frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

# Создаем фрейм для текстового вывода внизу
output_frame = ttk.LabelFrame(root, text="Вывод симуляции", padding="10")
output_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=10, pady=10)

# Настраиваем растягивание для root и фреймов
root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)
root.rowconfigure(1, weight=2) # Делаем фрейм вывода больше

frame.columnconfigure(1, weight=1)
output_frame.columnconfigure(0, weight=1)
output_frame.rowconfigure(0, weight=1)

# --- Параметры симуляции (без изменений, кроме добавления в output_text_widget) ---
# ... (оставил без изменений, чтобы сократить код здесь, вставьте из своего) ...
row_num = 0

# bridge_blocked
ttk.Label(frame, text="Мост заблокирован:").grid(row=row_num, column=0, sticky=tk.W, pady=2)
bridge_blocked_var = tk.StringVar(value="False") # Значение по умолчанию
bridge_blocked_cb_true = ttk.Radiobutton(frame, text="Да", variable=bridge_blocked_var, value="True")
bridge_blocked_cb_true.grid(row=row_num, column=1, sticky=tk.W)
bridge_blocked_cb_false = ttk.Radiobutton(frame, text="Нет", variable=bridge_blocked_var, value="False")
bridge_blocked_cb_false.grid(row=row_num, column=2, sticky=tk.W)
row_num += 1

# traffic_light_on
ttk.Label(frame, text="Светофоры включены:").grid(row=row_num, column=0, sticky=tk.W, pady=2)
traffic_light_on_var = tk.StringVar(value="False") # Значение по умолчанию
traffic_light_on_cb_true = ttk.Radiobutton(frame, text="Да", variable=traffic_light_on_var, value="True")
traffic_light_on_cb_true.grid(row=row_num, column=1, sticky=tk.W)
traffic_light_on_cb_false = ttk.Radiobutton(frame, text="Нет", variable=traffic_light_on_var, value="False")
traffic_light_on_cb_false.grid(row=row_num, column=2, sticky=tk.W)
row_num += 1

# road_events_on
ttk.Label(frame, text="Дорожные события:").grid(row=row_num, column=0, sticky=tk.W, pady=2)
road_events_on_var = tk.StringVar(value="False") # Значение по умолчанию
road_events_on_cb_true = ttk.Radiobutton(frame, text="Да", variable=road_events_on_var, value="True")
road_events_on_cb_true.grid(row=row_num, column=1, sticky=tk.W)
road_events_on_cb_false = ttk.Radiobutton(frame, text="Нет", variable=road_events_on_var, value="False")
road_events_on_cb_false.grid(row=row_num, column=2, sticky=tk.W)
row_num += 1

# routing_mode
ttk.Label(frame, text="Режим маршрутизации:").grid(row=row_num, column=0, sticky=tk.W, pady=2)
routing_mode_var = tk.StringVar(value="selfish") # Значение по умолчанию
routing_mode_combobox = ttk.Combobox(frame, textvariable=routing_mode_var,
                                     values=["selfish", "random"], state="readonly")
routing_mode_combobox.grid(row=row_num, column=1, columnspan=2, sticky=(tk.W, tk.E))
routing_mode_var.trace_add("write", update_selection_method_state)
row_num += 1

# speed_mode
ttk.Label(frame, text="Режим скорости:").grid(row=row_num, column=0, sticky=tk.W, pady=2)
speed_mode_var = tk.StringVar(value="theoretical") # Значение по умолчанию
speed_mode_combobox = ttk.Combobox(frame, textvariable=speed_mode_var,
                                  values=["historical", "actual", "theoretical"], state="readonly")
speed_mode_combobox.grid(row=row_num, column=1, columnspan=2, sticky=(tk.W, tk.E))
row_num += 1

# selection_method
ttk.Label(frame, text="Метод выбора маршрута:").grid(row=row_num, column=0, sticky=tk.W, pady=2)
selection_method_var = tk.StringVar(value="minimum") # Значение по умолчанию
selection_method_combobox = ttk.Combobox(frame, textvariable=selection_method_var,
                                       values=["minimum", "weighted-probability"], state="readonly")
selection_method_combobox.grid(row=row_num, column=1, columnspan=2, sticky=(tk.W, tk.E))
row_num += 1

# launch_rate
ttk.Label(frame, text="Интенсивность запуска (0.0-1.0):").grid(row=row_num, column=0, sticky=tk.W, pady=2)
launch_rate_entry = ttk.Entry(frame)
launch_rate_entry.insert(0, "0.45") # Значение по умолчанию
launch_rate_entry.grid(row=row_num, column=1, columnspan=2, sticky=(tk.W, tk.E))
row_num += 1

# congestion_coef
ttk.Label(frame, text="Коэф. сопротивления (0.0-1.0):").grid(row=row_num, column=0, sticky=tk.W, pady=2)
congestion_coef_entry = ttk.Entry(frame)
congestion_coef_entry.insert(0, "0.5") # Значение по умолчанию
congestion_coef_entry.grid(row=row_num, column=1, columnspan=2, sticky=(tk.W, tk.E))
row_num += 1

# is_writing (новый параметр)
ttk.Label(frame, text="Записывать результаты в файл:").grid(row=row_num, column=0, sticky=tk.W, pady=2)
is_writing_var = tk.StringVar(value="False") # Значение по умолчанию
is_writing_cb_true = ttk.Radiobutton(frame, text="Да", variable=is_writing_var, value="True")
is_writing_cb_true.grid(row=row_num, column=1, sticky=tk.W)
is_writing_cb_false = ttk.Radiobutton(frame, text="Нет", variable=is_writing_var, value="False")
is_writing_cb_false.grid(row=row_num, column=2, sticky=tk.W)
row_num += 1
# --- Конец параметров симуляции ---


# Текстовое поле для вывода результатов
output_text_widget = scrolledtext.ScrolledText(output_frame, wrap=tk.WORD, width=80, height=20, font=("Consolas", 10))
output_text_widget.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

# Кнопка запуска симуляции
run_button = ttk.Button(frame, text="Запустить Симуляцию", command=start_simulation_thread) # Вызываем start_simulation_thread
run_button.grid(row=row_num, column=0, columnspan=3, pady=20)

# Инициализируем состояние selection_method при запуске
update_selection_method_state()

root.mainloop()