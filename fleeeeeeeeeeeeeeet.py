import asyncio
import flet as ft

async def main(page: ft.Page):
    # Создаем Stack для абсолютного позиционирования
    stack = ft.Stack(width=400, height=200)

    # Начальная позиция по оси X
    x_pos = 0

    # Создаем круг (контейнер с закругленными углами)
    circle = ft.Container(
        width=50,
        height=50,
        bgcolor=ft.Colors.BLUE,
        border_radius=25,
        left=x_pos,
        top=100,
        animate=ft.Animation(200, ft.AnimationCurve.EASE_IN_OUT),
    )
    # Добавляем круг в Stack
    stack.controls.append(circle)

    # Флаг для контроля анимации
    animation_running = False

    async def animate():
        nonlocal x_pos, animation_running
        animation_running = True
        while animation_running:
            await asyncio.sleep(0.1)  # задержка 100 мс
            x_pos += 10
            if x_pos > 400:
                x_pos = -50
            circle.left = x_pos
            circle.update()
            await page.update_async()

    def start_anim(e: ft.ControlEvent):
        nonlocal animation_running
        if not animation_running:
            asyncio.create_task(animate())

    def stop_anim(e: ft.ControlEvent):
        nonlocal animation_running
        animation_running = False

    # Создаем кнопки для управления анимацией
    btn_start = ft.ElevatedButton("Start Moving", on_click=start_anim)
    btn_stop = ft.ElevatedButton("Stop Moving", on_click=stop_anim)

    # Добавляем Stack и кнопки на страницу через page.add()
    page.add(stack, btn_start, btn_stop)
    await page.update_async()

ft.app(target=main)
