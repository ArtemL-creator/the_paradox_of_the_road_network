import tkinter as tk
from tkinter import ttk, messagebox
import joblib
import pandas as pd
import numpy as np
import os

# --- Пути к сохраненным файлам модели ---
MODEL_DIR = 'models'
# Теперь мы загружаем весь пайплайн целиком
MODEL_FILENAME = os.path.join(MODEL_DIR, 'best_regression_pipeline.pkl')

# Глобальные переменные для модели
pipeline_model = None

# Списки признаков для создания DataFrame при предсказании
# Они должны быть известны GUI или получены из модели
# Лучше всего, если модель сама "знает" свои входные признаки,
# но пока что будем явно их указывать, как в обучении
NUMERIC_FEATURES = ['Интенс-ть', 'Коэф. Сопрот-я']
CATEGORICAL_FEATURES = ['Режим Скорости', 'Метод Выбора', 'Светофоры', 'Случ-е События', 'Мост']

def load_model():
    """Загружает обученный пайплайн."""
    global pipeline_model
    try:
        pipeline_model = joblib.load(MODEL_FILENAME)
        print("Модель-пайплайн успешно загружена.")
        return True
    except FileNotFoundError as e:
        messagebox.showerror("Ошибка загрузки", f"Файл модели не найден: {e}. Убедитесь, что вы запустили скрипт обучения и модель сохранена в папке 'models'.")
        return False
    except Exception as e:
        messagebox.showerror("Ошибка загрузки", f"Произошла ошибка при загрузке модели: {e}")
        return False

def update_selection_method_state(*args):
    """Обновляет состояние виджета выбора метода маршрута в зависимости от режима маршрутизации."""
    if routing_mode_var.get() == "random":
        selection_method_combobox.config(state="disabled")
    else: # "selfish"
        selection_method_combobox.config(state="readonly")

def predict_time():
    """Собирает параметры из GUI и делает предсказание с помощью загруженной модели."""
    if pipeline_model is None:
        messagebox.showerror("Ошибка", "Модель не загружена.")
        return

    try:
        # Сбор параметров из GUI
        bridge_blocked_val = "Закрыт" if bridge_blocked_var.get() == "True" else "Открыт"
        traffic_light_on_val = "Вкл" if traffic_light_on_var.get() == "True" else "Выкл"
        road_events_on_val = "Да" if road_events_on_var.get() == "True" else "Нет"
        routing_mode_val = routing_mode_var.get()
        speed_mode_val = speed_mode_var.get()

        # Если режим маршрутизации "random", "Метод Выбора" не имеет значения.
        # Для корректной передачи в модель, передаем один из валидных вариантов,
        # так как OHE все равно превратит его в нужные dummy-колонки.
        if routing_mode_val == "random":
             selection_method_val = "minimum" # Или любой другой из ['minimum', 'weighted-probability']
        else:
            selection_method_val = selection_method_var.get()

        launch_rate_val = float(launch_rate_entry.get())
        congestion_coef_val = float(congestion_coef_entry.get())

        if not (0.0 <= launch_rate_val <= 1.0):
            messagebox.showerror("Ошибка ввода", "Интенсивность запуска (Launch Rate) должна быть между 0.0 и 1.0.")
            return
        if not (0.0 <= congestion_coef_val <= 1.0):
            messagebox.showerror("Ошибка ввода", "Коэффициент сопротивления (Congestion Coef) должен быть между 0.0 и 1.0.")
            return

    except ValueError:
        messagebox.showerror("Ошибка ввода", "Пожалуйста, введите корректные числовые значения.")
        return
    except Exception as e:
        messagebox.showerror("Ошибка", f"Произошла непредвиденная ошибка при сборе параметров: {e}")
        return

    # Создание DataFrame для предсказания (одна строка)
    # Важно: колонки должны быть в том же порядке и с теми же именами, что и в X_raw при обучении
    input_data_raw = pd.DataFrame([{
        'Интенс-ть': launch_rate_val,
        'Коэф. Сопрот-я': congestion_coef_val,
        'Режим Скорости': speed_mode_val,
        'Метод Выбора': selection_method_val,
        'Светофоры': traffic_light_on_val,
        'Случ-е События': road_events_on_val,
        'Мост': bridge_blocked_val,
    }])

    try:
        # Пайплайн сам выполнит все необходимые преобразования
        predicted_log_time = pipeline_model.predict(input_data_raw)[0]

        # Обратная трансформация для получения времени в исходном масштабе
        predicted_original_time = np.expm1(predicted_log_time) # expm1(x) = exp(x) - 1

        prediction_result_label.config(text=f"Прогнозируемое нормализованное время: {predicted_original_time:.4f}")
    except Exception as e:
        messagebox.showerror("Ошибка предсказания", f"Не удалось сделать предсказание: {e}")


# --- Создание графического интерфейса ---
root = tk.Tk()
root.title("Предсказание Времени Симуляции")
root.geometry("450x550")

frame = ttk.Frame(root, padding="10")
frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)
frame.columnconfigure(1, weight=1)

# --- Параметры для ввода (аналогичны GUI симуляции) ---
row_num = 0

# bridge_blocked
ttk.Label(frame, text="Мост заблокирован:").grid(row=row_num, column=0, sticky=tk.W, pady=2)
bridge_blocked_var = tk.StringVar(value="False")
ttk.Radiobutton(frame, text="Да", variable=bridge_blocked_var, value="True").grid(row=row_num, column=1, sticky=tk.W)
ttk.Radiobutton(frame, text="Нет", variable=bridge_blocked_var, value="False").grid(row=row_num, column=2, sticky=tk.W)
row_num += 1

# traffic_light_on
ttk.Label(frame, text="Светофоры включены:").grid(row=row_num, column=0, sticky=tk.W, pady=2)
traffic_light_on_var = tk.StringVar(value="False")
ttk.Radiobutton(frame, text="Да", variable=traffic_light_on_var, value="True").grid(row=row_num, column=1, sticky=tk.W)
ttk.Radiobutton(frame, text="Нет", variable=traffic_light_on_var, value="False").grid(row=row_num, column=2, sticky=tk.W)
row_num += 1

# road_events_on
ttk.Label(frame, text="Дорожные события:").grid(row=row_num, column=0, sticky=tk.W, pady=2)
road_events_on_var = tk.StringVar(value="False")
ttk.Radiobutton(frame, text="Да", variable=road_events_on_var, value="True").grid(row=row_num, column=1, sticky=tk.W)
ttk.Radiobutton(frame, text="Нет", variable=road_events_on_var, value="False").grid(row=row_num, column=2, sticky=tk.W)
row_num += 1

# routing_mode
ttk.Label(frame, text="Режим маршрутизации:").grid(row=row_num, column=0, sticky=tk.W, pady=2)
routing_mode_var = tk.StringVar(value="selfish")
routing_mode_combobox = ttk.Combobox(frame, textvariable=routing_mode_var,
                                     values=["selfish", "random"], state="readonly")
routing_mode_combobox.grid(row=row_num, column=1, columnspan=2, sticky=(tk.W, tk.E))
routing_mode_var.trace_add("write", update_selection_method_state)
row_num += 1

# speed_mode
ttk.Label(frame, text="Режим скорости:").grid(row=row_num, column=0, sticky=tk.W, pady=2)
speed_mode_var = tk.StringVar(value="theoretical")
speed_mode_combobox = ttk.Combobox(frame, textvariable=speed_mode_var,
                                  values=["historical", "actual", "theoretical"], state="readonly")
speed_mode_combobox.grid(row=row_num, column=1, columnspan=2, sticky=(tk.W, tk.E))
row_num += 1

# selection_method
ttk.Label(frame, text="Метод выбора маршрута:").grid(row=row_num, column=0, sticky=tk.W, pady=2)
selection_method_var = tk.StringVar(value="minimum")
selection_method_combobox = ttk.Combobox(frame, textvariable=selection_method_var,
                                       values=["minimum", "weighted-probability"], state="readonly")
selection_method_combobox.grid(row=row_num, column=1, columnspan=2, sticky=(tk.W, tk.E))
row_num += 1

# launch_rate
ttk.Label(frame, text="Интенсивность запуска (0.0-1.0):").grid(row=row_num, column=0, sticky=tk.W, pady=2)
launch_rate_entry = ttk.Entry(frame)
launch_rate_entry.insert(0, "0.45")
launch_rate_entry.grid(row=row_num, column=1, columnspan=2, sticky=(tk.W, tk.E))
row_num += 1

# congestion_coef
ttk.Label(frame, text="Коэф. сопротивления (0.0-1.0):").grid(row=row_num, column=0, sticky=tk.W, pady=2)
congestion_coef_entry = ttk.Entry(frame)
congestion_coef_entry.insert(0, "0.5")
congestion_coef_entry.grid(row=row_num, column=1, columnspan=2, sticky=(tk.W, tk.E))
row_num += 1

# Кнопка для предсказания
predict_button = ttk.Button(frame, text="Предсказать время", command=predict_time)
predict_button.grid(row=row_num, column=0, columnspan=3, pady=20)
row_num += 1

# Метка для вывода результата предсказания
prediction_result_label = ttk.Label(frame, text="Прогнозируемое нормализованное время: N/A", font=("Arial", 12, "bold"))
prediction_result_label.grid(row=row_num, column=0, columnspan=3, pady=10)


# Инициализация: загрузка модели и установка начального состояния виджета выбора метода
if load_model():
    update_selection_method_state()
    root.mainloop()
else:
    root.destroy()