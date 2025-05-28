import pandas as pd
import numpy as np
import os

# --- Настройки ---
RESULTS_CSV_FILE = 'resources\\simulation_log.csv' # Путь к вашему CSV файлу
# Столбец с целевой переменной (нормализованное среднее время)
TIME_COLUMN = 'Total Ср. Время (норм.)'
# Столбец, указывающий состояние моста
BRIDGE_COLUMN = 'Мост'
# Столбец с результатом запуска
OUTCOME_COLUMN = 'Итог Запуска'

# Столбцы, которые определяют УНИКАЛЬНУЮ ПАРУ запусков (должны быть одинаковыми для закрытого и открытого моста в паре)
# Исключаем BRIDGE_COLUMN и OUTCOME_COLUMN, а также уникальные Run ID
# Включаем все параметры, которые варьировали или оставляли одинаковыми для пары
PAIR_GROUPING_COLUMNS = [
    'Режим Скорости',
    'Метод Выбора',
    'Светофоры',
    'Случ-е События',
    'Интенс-ть',
    'Коэф. Сопрот-я',
    # 'Фазы (Длит-ти)', # Можно добавить, если фазы варьировались между парами
]

# Точность округления для числовых колонок при группировке, чтобы избежать проблем с float
ROUND_DECIMALS = 6

# --- Загрузка и подготовка данных ---
if not os.path.exists(RESULTS_CSV_FILE):
    print(f"Ошибка: Файл данных не найден по пути {RESULTS_CSV_FILE}")
    print("Пожалуйста, убедитесь, что вы запустили симуляцию и файл создан.")
    exit()

try:
    df = pd.read_csv(RESULTS_CSV_FILE, encoding='utf-8-sig')
except Exception as e:
    print(f"Ошибка при чтении CSV файла: {e}")
    exit()

print(f"Успешно загружены данные из {RESULTS_CSV_FILE}. Всего записей: {len(df)}")

# --- Очистка данных ---
# 1. Оставляем только успешные запуски ('OK')
df_cleaned = df[df[OUTCOME_COLUMN] == 'OK'].copy()

# 2. Удаляем строки, где время ('Total Ср. Время (норм.)') отсутствует ('N/A') или не является числом
df_cleaned = df_cleaned[df_cleaned[TIME_COLUMN] != 'N/A'].copy()
df_cleaned[TIME_COLUMN] = pd.to_numeric(df_cleaned[TIME_COLUMN]) # Преобразуем в числовой тип

print(f"Записей после фильтрации по '{OUTCOME_COLUMN}' = 'OK' и наличию '{TIME_COLUMN}': {len(df_cleaned)}")

if len(df_cleaned) == 0:
    print("\nПосле очистки данных не осталось записей для анализа.")
    exit()

# --- Подготовка для группировки пар ---
# Округляем числовые колонки, используемые для группировки, чтобы избежать проблем с float
for col in PAIR_GROUPING_COLUMNS:
    if df_cleaned[col].dtype in ['float64', 'float32']:
        df_cleaned[f'{col}_rounded'] = df_cleaned[col].round(ROUND_DECIMALS)
        # Используем округленные колонки для группировки
        PAIR_GROUPING_COLUMNS[PAIR_GROUPING_COLUMNS.index(col)] = f'{col}_rounded'

# Проверка наличия всех нужных колонок для группировки
if not all(col in df_cleaned.columns for col in PAIR_GROUPING_COLUMNS + [BRIDGE_COLUMN, TIME_COLUMN]):
    missing_cols = set(PAIR_GROUPING_COLUMNS + [BRIDGE_COLUMN, TIME_COLUMN]) - set(df_cleaned.columns)
    print(f"\nОшибка: Отсутствуют необходимые столбцы для анализа в очищенных данных: {missing_cols}")
    print("Доступные столбцы:", df_cleaned.columns.tolist())
    exit()


# --- Поиск и анализ пар ---
paired_analysis_results = []

# Группируем данные по колонкам, которые должны быть одинаковыми в паре
grouped = df_cleaned.groupby(PAIR_GROUPING_COLUMNS)

print(f"\nНайдено {len(grouped)} уникальных комбинаций параметров (потенциальных пар).")

valid_pairs_count = 0

# Проходим по каждой группе
for name, group in grouped:
    # Проверяем, является ли группа валидной парой:
    # 1. В группе должно быть ровно 2 записи.
    # 2. В колонке BRIDGE_COLUMN должны быть уникальные значения 'Открыт' и 'Закрыт'.
    if len(group) == 2 and set(group[BRIDGE_COLUMN].unique()) == {'Открыт', 'Закрыт'}:
        valid_pairs_count += 1
        # Извлекаем времена для закрытого и открытого моста
        time_closed = group[group[BRIDGE_COLUMN] == 'Закрыт'][TIME_COLUMN].iloc[0]
        time_open = group[group[BRIDGE_COLUMN] == 'Открыт'][TIME_COLUMN].iloc[0]

        # Вычисляем разницу: Время_Открыт - Время_Закрыт
        time_difference = time_open - time_closed

        # Сохраняем результаты для этой пары
        pair_data = dict(zip(PAIR_GROUPING_COLUMNS, name)) # Параметры, определяющие пару
        pair_data['Время_Закрыт'] = time_closed
        pair_data['Время_Открыт'] = time_open
        pair_data['Разница_Время_(Открыт - Закрыт)'] = time_difference

        paired_analysis_results.append(pair_data)
    # else:
        # print(f"Пропущена группа (не пара): {name} (записей: {len(group)}, мосты: {group[BRIDGE_COLUMN].unique().tolist()})")


# Преобразуем результаты анализа пар в DataFrame для удобства
if not paired_analysis_results:
    print("\nНе найдено действительных парных запусков для анализа.")
    exit()

analysis_df = pd.DataFrame(paired_analysis_results)

print(f"\nНайдено {valid_pairs_count} действительных парных запусков для анализа.")

# --- Статистика по разнице во времени ---
average_difference = analysis_df['Разница_Время_(Открыт - Закрыт)'].mean()
median_difference = analysis_df['Разница_Время_(Открыт - Закрыт)'].median()

# Количество случаев, когда открытие моста...
paradox_cases = (analysis_df['Разница_Время_(Открыт - Закрыт)'] > 0).sum() # ...увеличило время (парадокс)
benefit_cases = (analysis_df['Разница_Время_(Открыт - Закрыт)'] < 0).sum() # ...уменьшило время (польза)
neutral_cases = (analysis_df['Разница_Время_(Открыт - Закрыт)'] == 0).sum() # ...не изменило время (точно равно 0)
# Удобнее считать почти нейтральные случаи, используя небольшой допуск
tolerance = 1e-9
almost_neutral_cases = analysis_df['Разница_Время_(Открыт - Закрыт)'].apply(lambda x: abs(x) <= tolerance).sum()
strictly_paradox_cases = (analysis_df['Разница_Время_(Открыт - Закрыт)'] > tolerance).sum()
strictly_benefit_cases = (analysis_df['Разница_Время_(Открыт - Закрыт)'] < -tolerance).sum()


print("\n--- Результаты парного анализа влияния моста ---")
print(f"Всего проанализировано пар: {valid_pairs_count}")
print(f"Средняя разница времени (Открыт - Закрыт): {average_difference:.4f}")
print(f"Медианная разница времени (Открыт - Закрыт): {median_difference:.4f}")
print("\nВлияние открытия моста на среднее время в пути (с учетом допуска):")
print(f"  Увеличило время (парадокс): {strictly_paradox_cases} случаев ({strictly_paradox_cases/valid_pairs_count:.1%})")
print(f"  Уменьшило время (польза):   {strictly_benefit_cases} случаев ({strictly_benefit_cases/valid_pairs_count:.1%})")
print(f"  Почти не изменило время:  {almost_neutral_cases} случаев ({almost_neutral_cases/valid_pairs_count:.1%})")


# --- Дополнительный анализ: зависимость разницы от параметров ---
print("\n--- Зависимость разницы от параметров ---")

# Пример: как разница зависит от Интенсивности
if 'Интенс-ть_rounded' in analysis_df.columns:
    # Группируем результаты анализа пар по округленной интенсивности
    intensity_analysis = analysis_df.groupby('Интенс-ть_rounded')['Разница_Время_(Открыт - Закрыт)'].agg(['mean', 'count'])
    print("\nСредняя разница в зависимости от Интенсивности:")
    print(intensity_analysis)

# Пример: как разница зависит от Режима Скорости и Режима Маршрутизации
if 'Режим Скорости' in analysis_df.columns and 'Routing Mode' in analysis_df.columns:
     # Используем исходные (не округленные) колонки для строковых параметров при анализе
     original_speed_col = [c for c in PAIR_GROUPING_COLUMNS if c.startswith('Режим Скорости')][0].replace('_rounded', '')
     original_routing_col = [c for c in PAIR_GROUPING_COLUMNS if c.startswith('Routing Mode')][0].replace('_rounded', '')

     combined_mode_analysis = analysis_df.groupby([original_speed_col, original_routing_col])['Разница_Время_(Открыт - Закрыт)'].agg(['mean', 'count'])
     print("\nСредняя разница в зависимости от Режима Скорости и Режима Маршрутизации:")
     print(combined_mode_analysis)


# Код для построения графиков,
# например, plot analysis_df['Разница_Время_(Открыт - Закрыт)'] против analysis_df['Интенс-ть_rounded']
import matplotlib.pyplot as plt
import seaborn as sns

# --- Шаг 1: Создайте новую комбинированную категориальную колонку ---
# Это объединит "Метод Выбора" и "Режим Скорости" в одну строку,
# например, "Эгоистичный (Исторический)" или "Случайный (Актуальный)".
# Затем эта новая колонка будет использоваться для свойства 'style' (форма маркера).
if 'Метод Выбора' in analysis_df.columns and 'Режим Скорости' in analysis_df.columns:
    analysis_df['Комбинированный_Режим'] = analysis_df['Метод Выбора'] + ' (' + analysis_df['Режим Скорости'] + ')'
else:
    print("Ошибка: Отсутствуют столбцы 'Метод Выбора' или 'Режим Скорости' в DataFrame.")
    # Если эти столбцы отсутствуют, дальнейшее выполнение кода может привести к ошибке.
    # Здесь можно добавить обработку этой ситуации или прервать выполнение.
    # Для демонстрации будем предполагать, что они существуют.


# --- Шаг 2: Определите список различных маркеров ---
# Эти маркеры будут использоваться для различных значений 'Комбинированный_Режим'.
# Выбирайте маркеры, которые хорошо различимы в черно-белом режиме.
# Здесь представлены комбинации форм и типов заполнения (заполненные, полые, с линиями).
# Важно, чтобы количество маркеров было достаточным для всех уникальных значений 'Комбинированный_Режим'.
# Например, если у вас 2 метода выбора и 3 режима скорости, то будет 6 уникальных комбинаций.
# Подбирайте количество и типы маркеров под свои конкретные данные, чтобы все комбинации были представлены.
custom_markers = [
    'o',    # Круг (заполненный)
    's',    # Квадрат (заполненный)
    'D',    # Ромб (заполненный)
    '^',    # Треугольник вверх (заполненный)
    'v',    # Треугольник вниз (заполненный)
    'P',    # Плюс (заполненный)
    'X',    # X-образный маркер (заполненный)
    'h',    # Шестиугольник 1
    'p',    # Пятиугольник
    '*',    # Звезда
    'd',    # Тонкий ромб
    'H',    # Шестиугольник 2
    'o',    # Круг (полый) - используем повторно для заполнения, если не хватает
    's',    # Квадрат (полый)
    'D',    # Ромб (полый)
    '^'     # Треугольник вверх (полый)
]

# Убедитесь, что список маркеров достаточно длинный для всех уникальных комбинаций
num_unique_combinations = analysis_df['Комбинированный_Режим'].nunique()
if num_unique_combinations > len(custom_markers):
    print(f"Предупреждение: Недостаточно уникальных маркеров. Нужно {num_unique_combinations}, доступно {len(custom_markers)}. Добавьте больше в custom_markers или рассмотрите другой способ кодирования.")
    # Если комбинаций слишком много, можно использовать `itertools.cycle(custom_markers)`
    # или рассмотреть уменьшение количества варьируемых параметров для одного графика.

# --- Шаг 3: Измените код построения графика ---
# Проверяем, что анализ дал результаты и есть данные для графика
if not analysis_df.empty:
    plt.figure(figsize=(12, 8)) # Увеличим размер графика для лучшей читаемости точек и легенды

    # Используем правильные имена столбцов из DataFrame
    sns.scatterplot(
        data=analysis_df,
        x='Интенс-ть_rounded',
        # x='Коэф. Сопрот-я_rounded',
        y='Разница_Время_(Открыт - Закрыт)',
        # hue='Метод Выбора', # ИСПРАВЛЕНО: Использовать имя столбца из данных
        style='Комбинированный_Режим', # Это имя столбца по CSV
        s=100, # Размер точек
        alpha=0.7, # Прозрачность точек
    color = 'black'  # Устанавливаем все точки черными для черно-белой печати
    )

    plt.axhline(0, color='grey', linestyle='--', linewidth=0.8) # Линия на уровне 0 для визуализации разницы
    plt.title('Влияние Интенсивности на разницу времени (Открыт - Закрыт) по режимам')
    # plt.title('Влияние Коэффициента Сопротивления на разницу времени (Открыт - Закрыт) по режимам')
    plt.xlabel(f'Интенсивность запуска (округлено до {ROUND_DECIMALS} знаков)')
    # plt.xlabel(f'Коэффициент сопротивления (округлено до {ROUND_DECIMALS} знаков)')
    plt.ylabel('Разница в нормализованном среднем времени (Время_Открыт - Время_Закрыт)')
    plt.grid(True, which='both', linestyle=':', linewidth=0.5)

    plt.legend(title='Обозначения:', bbox_to_anchor=(1.02, 1), loc='upper left') # Настройка легенды
    plt.tight_layout() # Автоматическая настройка отступов
    plt.show()
else:
    print("\nНет данных в analysis_df для построения графика.")

# Можно сохранить результаты парного анализа в новый CSV файл для удобства
# analysis_df.to_csv('resources\\paired_analysis_results.csv', index=False, encoding='utf-8-sig')
# print("\nРезультаты парного анализа сохранены в 'resources\\paired_analysis_results.csv'")