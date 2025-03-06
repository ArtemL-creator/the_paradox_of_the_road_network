import tkinter as tk

class VisualObject:
    def __init__(self, canvas, x, y, radius=20, color='blue'):
        """
        При создании объекта рисуется круг (овал) на переданном Canvas.
        :param canvas: экземпляр tk.Canvas, на котором рисуем.
        :param x: координата X центра фигуры.
        :param y: координата Y центра фигуры.
        :param radius: радиус круга.
        :param color: цвет заливки фигуры.
        """
        self.canvas = canvas
        self.x = x
        self.y = y
        self.radius = radius
        self.color = color
        # Рисуем круг: метод create_oval возвращает id созданного объекта
        self.id = self.canvas.create_oval(
            x - radius, y - radius, x + radius, y + radius,
            fill=color
        )

    def move(self, dx, dy):
        """
        Сдвигает фигуру на dx по оси X и dy по оси Y.
        """
        self.canvas.move(self.id, dx, dy)
        self.x += dx
        self.y += dy

def main():
    root = tk.Tk()
    root.title("Пример с визуальными объектами")
    canvas = tk.Canvas(root, width=400, height=300, bg='white')
    canvas.pack()

    # Создадим несколько объектов класса VisualObject
    objects = []
    positions = [(50, 50), (150, 100), (250, 150), (350, 200)]
    for pos in positions:
        obj = VisualObject(canvas, pos[0], pos[1], radius=20, color='green')
        objects.append(obj)

    # Пример анимации: перемещаем все объекты вправо каждую 50 мс
    def animate():
        for obj in objects:
            obj.move(2, 0)
            # Можно добавить проверку границ и логику "зацикливания"
        root.after(50, animate)

    animate()
    root.mainloop()

if __name__ == '__main__':
    main()
