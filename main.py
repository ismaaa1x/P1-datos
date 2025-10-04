import arcade
from courier.game import CourierQuestGame

class PantallaInicio(arcade.View):
    def __init__(self):
        super().__init__()
        self.fondo = arcade.load_texture("assets/inicio.png")  # Asegurate que la imagen esté en esta ruta

    def on_show(self):
        arcade.set_background_color(arcade.color.BLACK)

    def on_draw(self):
        self.clear()
        arcade.draw_lrwh_rectangle_textured(0, 0, self.window.width, self.window.height, self.fondo)

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ENTER:
            juego = CourierQuestGame()
            self.window.show_view(juego)

class PantallaFinal(arcade.View):
    def __init__(self, dinero, completados, fallidos):
        super().__init__()
        self.dinero = dinero
        self.completados = completados
        self.fallidos = fallidos

    def on_show(self):
        arcade.set_background_color(arcade.color.BLACK)

    def on_draw(self):
        self.clear()
        arcade.draw_text("¡Juego terminado!", self.window.width // 2, self.window.height // 2 + 60,
                         arcade.color.YELLOW, 32, anchor_x="center")
        arcade.draw_text(f"Dinero ganado: ₡{self.dinero:.2f}", self.window.width // 2, self.window.height // 2 + 20,
                         arcade.color.WHITE, 20, anchor_x="center")
        arcade.draw_text(f"Pedidos completados: {self.completados}", self.window.width // 2, self.window.height // 2 - 10,
                         arcade.color.GREEN, 18, anchor_x="center")
        arcade.draw_text(f"Pedidos fallidos: {self.fallidos}", self.window.width // 2, self.window.height // 2 - 40,
                         arcade.color.RED, 18, anchor_x="center")
        arcade.draw_text("Presiona R para reiniciar", self.window.width // 2, self.window.height // 2 - 80,
                         arcade.color.LIGHT_GRAY, 16, anchor_x="center")

    def on_key_press(self, key, modifiers):
        if key == arcade.key.R:
            self.window.show_view(PantallaInicio())

# Inyectar pantalla final en el juego
def courier_game_on_update(self, delta_time):
    self.game_time += delta_time
    self.burst_timer += delta_time

    if self.burst_timer >= self.current_burst.duration_sec:
        self.burst_index += 1
        if self.burst_index < len(self.weather.bursts):
            self.current_burst = self.weather.bursts[self.burst_index]
            self.burst_timer = 0

    if self.release_index < len(self.jobs):
        next_job = self.jobs[self.release_index]
        if self.game_time >= next_job.release_time:
            self.active_jobs.append(next_job)
            self.release_index += 1

    still_active = []
    for job in self.active_jobs:
        if self.game_time > job.release_time + 300:
            self.failed.append(job)
        else:
            still_active.append(job)
    self.active_jobs = still_active

    if self.exhausto and self.resistencia < 30:
        self.resistencia += 5 * delta_time
        if self.resistencia >= 30:
            self.exhausto = False

    if self.game_time >= self.remaining_time or self.total_money >= self.city_map.goal:
        final = PantallaFinal(self.total_money, len(self.completed), len(self.failed))
        self.window.show_view(final)

# Inyectar método en clase
CourierQuestGame.on_update = courier_game_on_update

# Lanzador principal
if __name__ == "__main__":
    ventana = arcade.Window(800, 600, "Courier Quest")
    inicio = PantallaInicio()
    ventana.show_view(inicio)
    arcade.run()
