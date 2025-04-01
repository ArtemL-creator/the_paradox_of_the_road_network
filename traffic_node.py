from traffic import Node
from traffic_light import TrafficLight

class TrafficNode(Node):
    def __init__(self, *, id_str, x=0, y=0, traffic_light: TrafficLight, phase_map: dict):
        """
        phase_map – словарь, где ключ – номер фазы (например, 1 или 2),
                     а значение – множество идентификаторов участков, для которых сигнал считается зелёным.
                     Например: {1: {"sn-bridge"}, 2: {"other-link"}}
        """
        super().__init__(id_str, x, y)
        self.traffic_light = traffic_light
        self.phase_map = phase_map

    def dispatch(self):
        if self.car:
            # print(f"[LOG DISPATCH] Узел {self.node_name} пытается отправить машину {self.car.serial_number}")
            current_phase = self.traffic_light.get_phase()
            print(f"[LOG DISPATCH] Узел {self.node_name}: текущая фаза = {current_phase}")
            # Определяем следующий участок по маршруту (ключ – имя узла)
            next_link = self.car.route.directions.get(self.node_name)
            if next_link is not None:
                print(f"[LOG DISPATCH] Узел {self.node_name}: следующий участок - {next_link.id}")
                allowed_links = self.phase_map.get(current_phase, set())
                # print(f"[LOG DISPATCH] Узел {self.node_name}: разрешённые участки в фазе {current_phase}: {allowed_links}")
                if next_link.id in allowed_links:
                    print(f"[LOG DISPATCH] Узел {self.node_name}: для участка {next_link.id} сигнал зелёный.")
                    free_lane = next_link.choose_free_lane()
                    if free_lane is not None:
                        if free_lane.queue.len == 0 or free_lane.queue.items[-1].progress >= car_length:
                            print(f"[LOG DISPATCH] Узел {self.node_name}: машина {self.car.serial_number} отправлена на участок {next_link.id}, полоса {free_lane.lane_id}")
                            self.car.progress = 0
                            self.car.avatar.set_position(self.x, self.y)
                            free_lane.queue.enqueue(self.car)
                            next_link.update_speed()
                            self.car = None
                        else:
                            pass
                            # print(f"[LOG DISPATCH] Узел {self.node_name}: машина {self.car.serial_number} ждет на участке {next_link.id}, очередь не пуста или последняя машина не продвинулась достаточно.")
                    else:
                        pass
                        # print(f"[LOG DISPATCH] Узел {self.node_name}: нет свободных полос на участке {next_link.id} для машины {self.car.serial_number}!")
                else:
                    self.car.waiting_time += 1  # где 1 – шаг симуляции
                    print(f"[LOG DISPATCH] Узел {self.node_name}: машина {self.car.serial_number} ждёт {self.car.waiting_time} сек")
                    print(f"[LOG DISPATCH] Узел {self.node_name}: для участка {next_link.id} сигнал красный. Машина {self.car.serial_number} остаётся на узле.")
                    return  # Ничего не делаем – машина остаётся в узле до зелёного сигнала
            else:
                pass
                # print(f"[LOG DISPATCH] Узел {self.node_name}: нет следующего участка в маршруте для машины {self.car.serial_number}!")

    # def calc_travel_time_theoretical_with_traffic_lights(self):
    #     tt = 0
    #     for link in self.itinerary:
    #         tt += link.travel_time
    #     # Предположим, что для каждого TrafficNode среднее ожидание = delay_per_node
    #     delay_per_node = 0  # по умолчанию 0 для узлов без светофора
    #     # Если узел является TrafficNode, можно взять, например, delay = cycle_time/2
    #     # Предположим, что узлы orig и dest не имеют светофора, а только узлы south и north.
    #     num_traffic_nodes = 0
    #     for node in [south, north]:
    #         if isinstance(node, TrafficNode):
    #             num_traffic_nodes += 1
    #             # Допустим, для этого узла задержка = (phase1_duration + phase2_duration)/4
    #             delay_per_node += (node.traffic_light.phase1_duration + node.traffic_light.phase2_duration) / 4
    #     if num_traffic_nodes > 0:
    #         average_delay = delay_per_node / num_traffic_nodes
    #     else:
    #         average_delay = 0
    #     # Итоговое время маршрута – время по участкам плюс суммарная задержка на узлах
    #     self.travel_time = tt + num_traffic_nodes * average_delay

    # def calc_travel_time_actual_with_traffic_lights(self):
    #     n = 0
    #     total_tt = 0
    #     for c in car_array:
    #         if c and c.route == self and c.odometer > 0 and (global_clock - c.depart_time) != 0:
    #             # Реальное время = время в пути + время ожидания
    #             actual_time = (global_clock - c.depart_time) + c.waiting_time
    #             total_tt += actual_time
    #             n += 1
    #     if n == 0:
    #         self.travel_time = self.route_length / speed_limit
    #     else:
    #         self.travel_time = total_tt / n