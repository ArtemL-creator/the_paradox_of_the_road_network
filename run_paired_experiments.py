import subprocess
import random
import time
import sys
import os

# --- Настройки автоматизации ---
# Укажите путь к вашему основному скрипту симуляции
SIMULATION_SCRIPT = 'traffic.py'  # Замените на реальное имя файла
# Имя файла для сохранения результатов
RESULTS_CSV_FILE = 'resources\\simulation_log.csv'

# Количество ПАР запусков (т.е. сколько раз будут сгенерированы УНИКАЛЬНЫЕ случайные параметры для пары мост закрыт/мост открыт)
# Общее количество симуляций будет N_PAIRS * 2
N_PAIRS = 50  # Задайте желаемое количество пар запусков (т.е. 50 с закрытым мостом и 50 с открытым)

# Определение диапазонов или списков возможных значений для случайного выбора
# Исключаем 'bridge_blocked' из этого списка, так как он будет перебираться явно
parameter_generation_rules = {
    'congestion_coef': (0.45, 0.55),
    'launch_rate': (0.45, 0.55),  # Случайное значение float между 0.3 и 1.0
    'traffic_light_on': [True, False],  # Случайный выбор из [True, False]
    'road_events_on': [True, False],  # Случайный выбор из [True, False]
    'routing_mode': ["selfish", "random"],  # Случайный выбор из ["selfish", "random"]
    'speed_mode': ["theoretical", "actual", "historical"],
    # Случайный выбор из ["historical", "actual", "theoretical"] - выбрал 2 для примера
    'selection_method': ["minimum", "weighted-probability"],  # Случайный выбор из [..., ...] (актуально для selfish)
    # Добавьте другие параметры, которые должны быть одинаковыми для пары, но случайными между парами
    # ,
}

# Пауза между отдельными запусками симуляции (в секундах)
PAUSE_SECONDS = 1

# --- Запуск симуляций со случайными параметрами и парным сравнением мостов ---

print(f"Запуск {N_PAIRS} пар симуляций (всего {N_PAIRS * 2} запусков).")
print("Параметры, генерируемые случайным образом для каждой пары:")
for name, rule in parameter_generation_rules.items():
    print(f"  {name}: {rule}")
print("Парное сравнение для параметра 'bridge_blocked': [True, False]")
print("-" * 30)

run_count = 0  # Общий счетчик запусков симуляции
successful_runs = 0

for pair_index in range(N_PAIRS):
    # 1. Генерируем случайные параметры для всей пары (кроме bridge_blocked)
    base_random_params = {}
    for param_name, rule in parameter_generation_rules.items():
        if isinstance(rule, tuple):  # Диапазон для float
            min_val, max_val = rule
            base_random_params[param_name] = random.uniform(min_val, max_val)
        elif isinstance(rule, list):  # Выбор из списка
            base_random_params[param_name] = random.choice(rule)
        # Добавьте другие типы правил, если нужно

    print(f"--- Запуск пары {pair_index + 1}/{N_PAIRS} с базовыми параметрами: {base_random_params} ---")

    # 2. Запускаем симуляцию дважды для этой пары параметров: bridge_blocked=True, затем bridge_blocked=False
    bridge_states_to_test = [True, False]  # Сначала закрытый, потом открытый
    # bridge_states_to_test = [False, True] # Или сначала открытый, потом закрытый - не имеет значения для итогового лога

    for is_blocked in bridge_states_to_test:
        run_count += 1  # Увеличиваем общий счетчик запусков перед каждым реальным запуском

        # Формируем команду для вызова скрипта симуляции
        command = [sys.executable, SIMULATION_SCRIPT]

        # Добавляем базовые случайные параметры, сгенерированные для этой пары
        for param_name, param_value in base_random_params.items():
            command.append(f'--{param_name}')
            # Передаем как строку, парсер в simulation_main.py преобразует в нужный тип
            command.append(str(param_value))

        # ЯВНО добавляем параметр bridge_blocked для текущего состояния в паре
        command.append('--bridge_blocked')
        command.append(str(is_blocked))  # Передаем 'True' или 'False' как строку

        print(f"  Запуск {run_count}/{N_PAIRS * 2}: Bridge Blocked = {is_blocked}")
        # print(f"  Команда для выполнения: {' '.join(command)}") # Отладочная печать команды

        try:
            # Запускаем дочерний процесс
            result = subprocess.run(command, check=True, capture_output=True, text=True, encoding='utf-8')

            print("  Запуск завершен успешно.")
            successful_runs += 1
            # print("  Standard Output:\n", result.stdout) # Отладочная печать вывода
            # print("  Standard Error:\n", result.stderr) # Отладочная печать ошибок

        except subprocess.CalledProcessError as e:
            print(f"  !!! Ошибка при выполнении симуляции с параметрами {base_random_params} !!!")
            print(f"  Код завершения: {e.returncode}")
            print("  Standard Output:\n", e.stdout)
            print("  Standard Error:\n", e.stderr)
        except FileNotFoundError:
            print(f"  !!! Ошибка: Скрипт симуляции не найден по пути {SIMULATION_SCRIPT} !!!")
            # Останавливаем всю автоматизацию, если основной скрипт не найден
            # В данном случае, поскольку это во внутреннем цикле, можно просто break из внешнего
            exit()
        except Exception as e:
            print(f"  !!! Произошла неожиданная ошибка при запуске: {e} !!!")
            print(f"  Параметры запуска: {base_random_params}")

        # Делаем паузу после каждого отдельного запуска симуляции
        if PAUSE_SECONDS > 0 and run_count < N_PAIRS * 2:
            # print(f"  Пауза {PAUSE_SECONDS} сек...") # Может быть много строк
            time.sleep(PAUSE_SECONDS)

print("-" * 30)
print("Автоматизация завершена.")
print(f"Всего запланировано запусков (пар * 2): {N_PAIRS * 2}")
print(f"Успешно завершенных запусков: {successful_runs}")
print(f"Результаты записаны в файл {RESULTS_CSV_FILE} (если логгирование включено в скрипте симуляции).")
