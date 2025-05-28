import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import sys
import os

# --- Путь к вашему основному скрипту симуляции ---
SIMULATION_SCRIPT = 'traffic.py'

def update_selection_method_state(*args):
    """Обновляет состояние виджета выбора метода маршрута в зависимости от режима маршрутизации."""
    if routing_mode_var.get() == "random":
        selection_method_combobox.config(state="disabled")
        # Опционально: сбросить значение, если оно было установлено для "selfish"
        # selection_method_var.set("N/A") # Можно сбросить, если хотите
    else: # "selfish"
        selection_method_combobox.config(state="readonly")
        # Опционально: установить значение по умолчанию, если оно было сброшено
        # if selection_method_var.get() == "N/A":
        #    selection_method_var.set("minimum")


def run_simulation():
    """Функция для сбора параметров из GUI и запуска симуляции."""
    # Собираем значения из виджетов
    try:
        # Булевы значения
        bridge_blocked_val = bridge_blocked_var.get() == "True"
        traffic_light_on_val = traffic_light_on_var.get() == "True"
        road_events_on_val = road_events_on_var.get() == "True"
        is_writing_val = is_writing_var.get() == "True"

        # Строковые значения
        routing_mode_val = routing_mode_var.get()
        # Если routing_mode_val = "random", selection_method не имеет значения, но нам нужно передать что-то
        # Мы можем передать его текущее значение или заглушку.
        # В вашем traffic.py парсер уже обрабатывает это, если он не нужен.
        selection_method_val = selection_method_var.get()
        speed_mode_val = speed_mode_var.get()


        # Числовые значения
        launch_rate_val = float(launch_rate_entry.get())
        congestion_coef_val = float(congestion_coef_entry.get())

        # Валидация числовых значений (простые проверки)
        if not (0.0 <= launch_rate_val <= 1.0):
            messagebox.showerror("Ошибка ввода", "Интенсивность запуска (Launch Rate) должна быть между 0.0 и 1.0.")
            return
        # Предполагаем такой же диапазон для congestion_coef
        if not (0.0 <= congestion_coef_val <= 1.0):
            messagebox.showerror("Ошибка ввода", "Коэффициент сопротивления (Congestion Coef) должен быть между 0.0 и 1.0.")
            return

    except ValueError:
        messagebox.showerror("Ошибка ввода", "Пожалуйста, введите корректные числовые значения для Launch Rate и Congestion Coef.")
        return
    except Exception as e:
        messagebox.showerror("Ошибка", f"Произошла непредвиденная ошибка при сборе параметров: {e}")
        return

    # Формируем команду для запуска traffic.py
    command = [sys.executable, SIMULATION_SCRIPT]

    # Добавляем все параметры как аргументы командной строки
    command.append('--bridge_blocked')
    command.append(str(bridge_blocked_val))
    command.append('--traffic_light_on')
    command.append(str(traffic_light_on_val))
    command.append('--road_events_on')
    command.append(str(road_events_on_val))
    command.append('--routing_mode')
    command.append(routing_mode_val)
    command.append('--speed_mode')
    command.append(speed_mode_val)

    # Добавляем selection_method только если routing_mode не "random"
    # Это сделает команду более чистой, хотя ваш parser.py все равно справится
    if routing_mode_val != "random":
        command.append('--selection_method')
        command.append(selection_method_val)


    command.append('--launch_rate')
    command.append(str(launch_rate_val))
    command.append('--congestion_coef')
    command.append(str(congestion_coef_val))

    # Добавляем флаг для записи в файл на основе выбора пользователя
    command.append('--is_writing')
    command.append(str(is_writing_val))

    print(f"Запуск симуляции с параметрами: {command[2:]}") # Проверяем команду в консоли

    try:
        # Запускаем дочерний процесс
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8')
        stdout, stderr = process.communicate() # Ждем завершения и получаем вывод

        if process.returncode == 0:
            messagebox.showinfo("Завершение симуляции", "Симуляция завершена успешно!")
            print("--- Вывод симуляции (stdout) ---")
            print(stdout)
            if stderr:
                print("--- Ошибки симуляции (stderr) ---")
                print(stderr)
        else:
            messagebox.showerror("Ошибка симуляции", f"Симуляция завершилась с ошибкой. Код: {process.returncode}\nСм. консоль для подробностей.")
            print("--- Ошибки симуляции (stderr) ---")
            print(stderr)
            print("--- Вывод симуляции (stdout) ---")
            print(stdout)

    except FileNotFoundError:
        messagebox.showerror("Ошибка", f"Скрипт симуляции не найден по пути: {SIMULATION_SCRIPT}")
    except Exception as e:
        messagebox.showerror("Ошибка запуска", f"Произошла ошибка при запуске симуляции: {e}")

# --- Создание графического интерфейса ---
root = tk.Tk()
root.title("Настройки Симуляции Транспорта")
root.geometry("450x550") # Увеличим немного размер окна

# Создаем фрейм для удобства размещения элементов
frame = ttk.Frame(root, padding="10")
frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

# Настраиваем колонки и строки для растягивания
root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)
frame.columnconfigure(1, weight=1)

# --- Параметры симуляции ---

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
# Привязываем функцию update_selection_method_state к изменению routing_mode
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


# Кнопка запуска симуляции
run_button = ttk.Button(frame, text="Запустить Симуляцию", command=run_simulation)
run_button.grid(row=row_num, column=0, columnspan=3, pady=20)

# Инициализируем состояние selection_method при запуске
update_selection_method_state()

root.mainloop()