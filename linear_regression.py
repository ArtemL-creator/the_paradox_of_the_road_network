import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score
import os

# --- Настройки ---
RESULTS_CSV_FILE = 'resources\\simulation_log.csv' # Путь к вашему CSV файлу
# Целевая переменная (что прогнозируем)
TARGET_COLUMN = 'Total Ср. Время (норм.)'
# Столбец с результатом запуска (для фильтрации успешных)
OUTCOME_COLUMN = 'Итог Запуска'

# Столбцы, которые будем использовать как ПРИЗНАКИ (для прогнозирования)
# Выберем, которые варьировали и которые, влияют на время
FEATURE_COLUMNS = [
    'Режим Скорости',
    'Метод Выбора', # Соответствует Routing Mode и Selection Method вместе взятым в логе
    'Светофоры',
    'Случ-е События',
    'Мост', # Состояние моста
    'Интенс-ть',
    'Коэф. Сопрот-я',
    # 'Фазы (Длит-ти)', # Этот столбец в формате строки и может быть N/A, его сложно использовать напрямую в простой регрессии
]

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

# 2. Удаляем строки, где целевая переменная отсутствует ('N/A')
df_cleaned = df_cleaned[df_cleaned[TARGET_COLUMN] != 'N/A'].copy()

# 3. Преобразуем целевую переменную в числовой формат (float)
df_cleaned[TARGET_COLUMN] = pd.to_numeric(df_cleaned[TARGET_COLUMN])

print(f"Записей после фильтрации по '{OUTCOME_COLUMN}' = 'OK' и наличию '{TARGET_COLUMN}': {len(df_cleaned)}")

if len(df_cleaned) == 0:
    print("\nПосле очистки данных не осталось записей для прогнозирования.")
    exit()

# --- Подготовка признаков (X) и целевой переменной (y) ---

# Выбираем только нужные колонки признаков из очищенных данных
X_raw = df_cleaned[FEATURE_COLUMNS].copy()
y = df_cleaned[TARGET_COLUMN].copy()

# Преобразуем категориальные признаки в числовой формат с помощью One-Hot Encoding
# drop_first=True удаляет первый столбец для каждой категории, избегая избыточности (мультиколлинеарности) для линейных моделей
X = pd.get_dummies(X_raw, columns=[col for col in FEATURE_COLUMNS if X_raw[col].dtype == 'object'], drop_first=True)
# Если есть другие не-числовые типы кроме object, возможно, потребуется явное их указание или обработка

print("\nПодготовленные признаки для модели (фрагмент):")
print(X.head())
print(f"\nРазмерность признаков: {X.shape}")
print("\nЦелевая переменная (фрагмент):")
print(y.head())


# --- Разделение данных на обучающую и тестовую выборки ---
# test_size=0.20 означает, что 20% данных пойдут на тестирование, 80% на обучение
# random_state для воспроизводимости результатов разбиения
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.20, random_state=42)

print(f"\nДанные разделены: Обучающая выборка = {len(X_train)} записей, Тестовая выборка = {len(X_test)} записей.")


# --- Создание и обучение модели линейной регрессии ---
model = LinearRegression()

# Обучаем модель на обучающих данных
model.fit(X_train, y_train)

print("\nМодель линейной регрессии обучена.")

# Вывод коэффициентов модели
print("\nКоэффициенты модели:")
# Создаем Series для удобного сопоставления коэффициентов с именами признаков
coefficients = pd.Series(model.coef_, index=X.columns)
print(coefficients)
print(f"\nСвободный член (intercept): {model.intercept_:.4f}")

# Интерпретация:
# - Положительный коэффициент означает, что с увеличением значения признака (или если это категориальный признак, при его наличии, по сравнению с базовой категорией, которая была отброшена drop_first=True) прогнозируемое время УВЕЛИЧИВАЕТСЯ.
# - Отрицательный коэффициент означает, что прогнозируемое время УМЕНЬШАЕТСЯ.
# - Величина коэффициента показывает НА СКОЛЬКО изменяется время при изменении признака на 1 единицу (для числовых) или при переходе к данной категории (для категориальных).

# --- Прогнозирование и оценка модели ---
# Делаем прогнозы на тестовой выборке
y_pred = model.predict(X_test)

# Оцениваем модель
mse = mean_squared_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)

print("\n--- Оценка модели на тестовой выборке ---")
print(f"Средняя квадратичная ошибка (MSE): {mse:.4f}")
print(f"Корень из средней квадратичной ошибки (RMSE): {np.sqrt(mse):.4f}") # RMSE часто более нагляден
print(f"Коэффициент детерминации (R-squared): {r2:.4f}")

# Интерпретация метрик:
# - MSE/RMSE: Средняя ошибка прогноза в единицах целевой переменной. RMSE легче интерпретировать, он в тех же единицах, что и время.
# - R-squared: Доля дисперсии (разброса) целевой переменной, объясняемая моделью. Значение от 0 до 1. Чем ближе к 1, тем лучше модель "улавливает" зависимости в данных. Если R-squared близок к 0, модель не сильно лучше простого предсказания среднего значения.

# --- Пример использования обученной модели для нового прогноза ---
print("\n--- Пример прогноза для новой ситуации ---")

# Создайте DataFrame с новыми параметрами.
# Важно! Колонки должны быть ТОЧНО такие же, как в X (с one-hot кодированием и т.д.)
# Самый надежный способ - создать DataFrame с исходными параметрами и прогнать его через pd.get_dummies с теми же колонками, что и для обучения
example_data_raw = pd.DataFrame([{
    'Режим Скорости': 'historical',
    'Метод Выбора': 'selfish',
    'Светофоры': 'Вкл',
    'Случ-е События': 'Нет',
    'Мост': 'Открыт',
    'Интенс-ть': 0.45,
    'Коэф. Сопрот-я': 0.5,
}])

# Применяем ту же One-Hot Encoding, что и для обучающих данных
# reindex позволяет убедиться, что все колонки из X присутствуют, заполняя отсутствующие нулями
example_data_processed = pd.get_dummies(example_data_raw, columns=[col for col in FEATURE_COLUMNS if example_data_raw[col].dtype == 'object'], drop_first=True).reindex(columns=X.columns, fill_value=0)


# Делаем прогноз
predicted_time_example = model.predict(example_data_processed)

print(f"\nПараметры для прогноза: {example_data_raw.iloc[0].to_dict()}")
print(f"Прогнозируемое нормализованное среднее время: {predicted_time_example[0]:.4f}")