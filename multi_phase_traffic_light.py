class MultiPhaseTrafficLight:
    """
    Управляет светофором с произвольным количеством фаз,
    каждая из которых имеет свою заданную длительность.
    Фазы идентифицируются их порядковым индексом в списке (0, 1, 2...).
    """

    def __init__(self, phase_durations: list[int]):
        """
        Инициализирует многофазный светофор.

        Args:
            phase_durations (list[int]): Список целых чисел, где каждое число -
                                         длительность соответствующей фазы в
                                         тактах/шагах симуляции. Фазы идут
                                         в порядке их следования в цикле.
                                         Например: [30, 5, 25, 5] для 4-х фаз.
                                         Длительности должны быть > 0.
        """
        if not phase_durations or not all(isinstance(d, int) and d > 0 for d in phase_durations):
            raise ValueError("phase_durations должен быть непустым списком положительных целых чисел.")

        self.phase_durations = phase_durations
        self.num_phases = len(phase_durations)
        self.current_phase_index = 0  # Начинаем с первой фазы (индекс 0)
        self.timer = 0  # Время, прошедшее в текущей фазе

        total_cycle_time = sum(self.phase_durations)
        print(
            f"MultiPhaseTrafficLight создан: {self.num_phases} фаз(ы), длительности={self.phase_durations}, цикл={total_cycle_time} шагов.")

    def update(self, time_step: int = 1):
        """
        Обновляет состояние светофора на указанное количество шагов времени.
        Обычно time_step равен приращению global_clock за один вызов step().
        Например, если global_clock += speed_limit, то time_step=speed_limit.
        Если global_clock += 1, то time_step=1.
        """
        if time_step <= 0:
            return

        self.timer += time_step
        current_phase_duration = self.phase_durations[self.current_phase_index]

        # Используем 'while', так как time_step может быть большим,
        # и светофор может успеть сменить несколько фаз за один вызов update.
        while self.timer >= current_phase_duration:
            # Время текущей фазы истекло
            overflow = self.timer - current_phase_duration # На сколько времени "перешагнули"

            # Переходим к следующей фазе (с зацикливанием)
            self.current_phase_index = (self.current_phase_index + 1) % self.num_phases

            # Сбрасываем таймер для новой фазы, учитывая "перешагнувшее" время
            self.timer = overflow

            # Обновляем длительность для следующей проверки в цикле while
            # (на случай, если overflow >= длительности новой фазы)
            current_phase_duration = self.phase_durations[self.current_phase_index]
            # print(f"[Debug TrafficLight] Phase changed to {self.current_phase_index} at timer overflow {overflow}") # Отладка

    def get_phase(self) -> int:
        """
        Возвращает ИНДЕКС текущей активной фазы (0, 1, 2...).
        Этот индекс используется в TrafficNode для поиска в phase_map.
        """
        return self.current_phase_index

    def get_time_in_phase(self) -> int:
        """Возвращает время (в шагах), прошедшее с начала текущей фазы."""
        return self.timer

    def get_current_phase_duration(self) -> int:
        """Возвращает полную длительность текущей активной фазы."""
        return self.phase_durations[self.current_phase_index]

    def reset(self):
        """Сбрасывает светофор в начальное состояние (фаза 0, таймер 0)."""
        self.current_phase_index = 0
        self.timer = 0
        print("Светофор сброшен.")

