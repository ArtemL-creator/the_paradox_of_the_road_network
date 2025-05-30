import os
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler, PolynomialFeatures
from sklearn.linear_model import Ridge, Lasso, ElasticNet
from sklearn.metrics import mean_squared_error, r2_score
import joblib

# --- Настройки ---
DATA_FILE = 'resources/simulation_log.csv'
TARGET_COLUMN = 'Total Ср. Время (норм.)'
OUTCOME_COLUMN = 'Итог Запуска'
NUMERIC_FEATURES = ['Интенс-ть', 'Коэф. Сопрот-я']
CATEGORICAL_FEATURES = ['Режим Скорости', 'Метод Выбора', 'Светофоры', 'Случ-е События', 'Мост']
MODEL_DIR = 'models'
os.makedirs(MODEL_DIR, exist_ok=True)

# --- Загрузка и очистка данных ---
df = pd.read_csv(DATA_FILE, encoding='utf-8-sig')
df = df[df[OUTCOME_COLUMN] == 'OK'].copy()
df = df[df[TARGET_COLUMN] != 'N/A'].copy()
df[TARGET_COLUMN] = pd.to_numeric(df[TARGET_COLUMN])

# Целевая переменная в лог-преобразовании
X_raw = df[NUMERIC_FEATURES + CATEGORICAL_FEATURES]
y_raw = np.log1p(df[TARGET_COLUMN])

# --- Разделение данных ---
X_train, X_test, y_train, y_test = train_test_split(
    X_raw, y_raw, test_size=0.2, random_state=42
)

# --- Построение препроцессинга и pipeline ---
numeric_pipe = Pipeline([
    ('poly', PolynomialFeatures(include_bias=False)),
    ('scaler', StandardScaler()),
])
categorical_pipe = OneHotEncoder(drop='first', sparse_output=False)

preprocessor = ColumnTransformer([
    ('num', numeric_pipe, NUMERIC_FEATURES),
    ('cat', categorical_pipe, CATEGORICAL_FEATURES),
])

pipeline = Pipeline([
    ('preproc', preprocessor),
    ('reg', Ridge()),
])

# --- Сетка гиперпараметров ---
param_grid = [
    {
        'preproc__num__poly__degree': [1, 2, 3],
        'reg': [Ridge()],
        'reg__alpha': [0.001, 0.01, 0.1, 1.0, 10.0],
    },
    {
        'preproc__num__poly__degree': [1, 2, 3],
        'reg': [Lasso(max_iter=10000)],
        'reg__alpha': [0.001, 0.01, 0.1, 1.0, 10.0],
    },
    {
        'preproc__num__poly__degree': [1, 2, 3],
        'reg': [ElasticNet(max_iter=10000)],
        'reg__alpha': [0.001, 0.01, 0.1, 1.0, 10.0],
        'reg__l1_ratio': [0.2, 0.5, 0.8],
    }
]

grid_search = GridSearchCV(
    pipeline,
    param_grid,
    cv=5,
    scoring='neg_root_mean_squared_error',
    n_jobs=-1,
)

grid_search.fit(X_train, y_train)

# --- Результаты подбора ---
best_model = grid_search.best_estimator_
best_params = grid_search.best_params_
best_score = -grid_search.best_score_
print("Лучшие параметры:", best_params)
print(f"RMSE (CV): {best_score:.4f}")

# --- Оценка на тестовой выборке ---
y_pred_log = best_model.predict(X_test)
y_pred = np.expm1(y_pred_log)
y_test_orig = np.expm1(y_test)

mse = mean_squared_error(y_test_orig, y_pred)
rmse = np.sqrt(mse)
r2 = r2_score(y_test_orig, y_pred)

print("\n--- Оценка модели на тестовой выборке ---")
print(f"Средняя квадратичная ошибка (MSE): {mse:.4f}")
print(f"Корень из средней квадратичной ошибки (RMSE): {np.sqrt(mse):.4f}")  # RMSE часто более нагляден
print(f"Коэффициент детерминации (R-squared): {r2:.4f}")

# Интерпретация метрик:
# - MSE/RMSE: Средняя ошибка прогноза в единицах целевой переменной. RMSE легче интерпретировать, он в тех же единицах, что и время.
# - R-squared: Доля дисперсии (разброса) целевой переменной, объясняемая моделью. Значение от 0 до 1. Чем ближе к 1, тем лучше модель "улавливает" зависимости в данных. Если R-squared близок к 0, модель не сильно лучше простого предсказания среднего значения.

# --- Сохранение итоговой модели ---
joblib.dump(best_model, os.path.join(MODEL_DIR, 'best_regression_pipeline.pkl'))
print(f"Модель сохранена в {MODEL_DIR}/best_regression_pipeline.pkl")
