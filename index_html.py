import tkinter as tk


def draw_traffic_simulation(canvas):
    # Рисуем фон (аналог <rect> с fill и stroke)
    canvas.create_rectangle(0, 0, 640, 400, fill="#b5b2a3", outline="#717171")

    # Рисуем "дороги"
    # Прямая дорога "a": линия от (50, 180) до (320, 180)
    canvas.create_line(50, 180, 320, 180, fill="black", width=2)

    # Прямая дорога "b": линия от (320, 220) до (590, 220)
    canvas.create_line(320, 220, 590, 220, fill="black", width=2)

    # Изогнутая дорога "A": аппроксимируем кривую с помощью smooth-линии
    # Точки: (50,180), (65,445), (295,444), (320,220)
    canvas.create_line(50, 180, 65, 445, 295, 444, 320, 220,
                       fill="gray", width=4, smooth=True)

    # Изогнутая дорога "B": аппроксимируем кривую
    # Точки: (320,180), (345,-44), (575,-45), (590,220)
    # Отрицательные значения y скорректируем сдвигом вниз (offset)
    offset = 50
    canvas.create_line(320, 180 + offset, 345, -44 + offset, 575, -45 + offset, 590, 220 + offset,
                       fill="gray", width=4, smooth=True)

    # Рисуем "мост" (линия между точками (320, 180) и (320, 220))
    canvas.create_line(320, 180, 320, 220, fill="gray", width=4)

    # Рисуем "узлы" (аналог кругов для исходной и конечной точек)
    # Origin
    canvas.create_oval(50 - 10, 180 - 10, 50 + 10, 180 + 10, fill="red")
    # Destination
    canvas.create_oval(590 - 10, 220 - 10, 590 + 10, 220 + 10, fill="green")

    # Добавляем подписи
    canvas.create_text(50, 247, text="Origin", anchor="n")
    canvas.create_text(590, 165, text="Destination", anchor="s")


def main():
    root = tk.Tk()
    root.title("Traffic Simulation")
    # Создаем холст с размерами, аналогичными viewBox в SVG
    canvas = tk.Canvas(root, width=640, height=400)
    canvas.pack()

    draw_traffic_simulation(canvas)

    root.mainloop()


if __name__ == '__main__':
    main()
