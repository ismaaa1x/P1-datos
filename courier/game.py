import arcade
from .api import get_city_map, get_jobs, get_weather
from .models import Job, WeatherReport

TILE_SIZE = 20

TILE_COLORS = {
    "C": arcade.color.LIGHT_GRAY,
    "P": arcade.color.DARK_SPRING_GREEN,
    "B": arcade.color.DARK_SLATE_GRAY
}

class CourierQuestGame(arcade.Window):
    def __init__(self):
        self.city_map = get_city_map()
        self.jobs = get_jobs()
        self.weather: WeatherReport = get_weather()
        self.current_job: Job | None = None
        self.completed = []
        self.failed = []
        self.total_money = 0.0
        self.game_time = 0
        self.release_index = 0
        self.active_jobs = []
        self.remaining_time = self.city_map.goal or 1500
        width = self.city_map.width * TILE_SIZE
        height = self.city_map.height * TILE_SIZE
        super().__init__(width, height, "Courier Quest - Pedidos", resizable=True)
        self.set_minimum_size(400, 300)
        self.set_maximum_size(1200, 900)
        arcade.set_background_color(arcade.color.SKY_BLUE)
        self.player_pos = self.buscar_inicio_en_calle()
        self.current_burst = None
        self.burst_index = 0
        self.burst_timer = 0
        if self.weather.bursts:
            self.current_burst = self.weather.bursts[0]

    def buscar_inicio_en_calle(self):
        for y, fila in enumerate(self.city_map.tiles):
            for x, tile in enumerate(fila):
                if tile == "C":
                    return (y, x)
        return (0, 0)

    def setup(self):
        pass

    def on_draw(self):
        self.clear()
        for y, fila in enumerate(self.city_map.tiles):
            for x, tile in enumerate(fila):
                color = TILE_COLORS.get(tile, arcade.color.RED)
                px = x * TILE_SIZE + TILE_SIZE / 2
                py = self.height - (y * TILE_SIZE + TILE_SIZE / 2)
                arcade.draw_rectangle_filled(px, py, TILE_SIZE - 1, TILE_SIZE - 1, color)

        for job in self.active_jobs:
            x, y = job.pickup[0], job.pickup[1]
            px = x * TILE_SIZE + TILE_SIZE / 2
            py = self.height - (y * TILE_SIZE + TILE_SIZE / 2)
            arcade.draw_rectangle_outline(px, py, TILE_SIZE, TILE_SIZE, arcade.color.BLUE, 2)

        if self.current_job:
            x, y = self.current_job.dropoff
            px = x * TILE_SIZE + TILE_SIZE / 2
            py = self.height - (y * TILE_SIZE + TILE_SIZE / 2)
            arcade.draw_rectangle_outline(px, py, TILE_SIZE, TILE_SIZE, arcade.color.GOLD, 3)

        x, y = self.player_pos[1], self.player_pos[0]
        px = x * TILE_SIZE + TILE_SIZE / 2
        py = self.height - (y * TILE_SIZE + TILE_SIZE / 2)
        arcade.draw_rectangle_filled(px, py, TILE_SIZE - 2, TILE_SIZE - 2, arcade.color.ORANGE)

        y_pos = self.height - 20
        arcade.draw_text(f"Tiempo: {self.game_time}s / {self.remaining_time}s", 10, y_pos, arcade.color.BLACK, 14)
        y_pos -= 20
        arcade.draw_text(f"Dinero: ₡{self.total_money:.2f} / ₡{self.city_map.goal}", 10, y_pos, arcade.color.BLACK, 14)
        y_pos -= 20
        arcade.draw_text(f"Clima: {self.current_burst.condition if self.current_burst else 'clear'}", 10, y_pos, arcade.color.BLACK, 14)
        y_pos -= 20
        arcade.draw_text(f"Pedidos activos: {len(self.active_jobs)}", 10, y_pos, arcade.color.BLACK, 14)
        y_pos -= 20
        arcade.draw_text(f"Pedidos completados: {len(self.completed)}", 10, y_pos, arcade.color.BLACK, 14)
        y_pos -= 20
        arcade.draw_text(f"Pedidos fallidos: {len(self.failed)}", 10, y_pos, arcade.color.BLACK, 14)

    def mover_jugador(self, dx, dy):
        nueva_fila = self.player_pos[0] + dy
        nueva_col = self.player_pos[1] + dx
        if 0 <= nueva_fila < self.city_map.height and 0 <= nueva_col < self.city_map.width:
            tile = self.city_map.tiles[nueva_fila][nueva_col]
            if not self.city_map.legend[tile].blocked:

                self.player_pos = (nueva_fila, nueva_col)

    def on_key_press(self, key, modifiers):
        if key == arcade.key.UP:
            self.mover_jugador(0, -1)
        elif key == arcade.key.DOWN:
            self.mover_jugador(0, 1)
        elif key == arcade.key.LEFT:
            self.mover_jugador(-1, 0)
        elif key == arcade.key.RIGHT:
            self.mover_jugador(1, 0)
        elif key == arcade.key.E:
            self.interactuar()

    def interactuar(self):
        fila, col = self.player_pos
        if self.current_job:
            if (fila, col) == tuple(reversed(self.current_job.dropoff)):
                self.total_money += self.current_job.payout
                self.completed.append(self.current_job)
                self.current_job = None
        else:
            for job in self.active_jobs:
                px, py = job.pickup
                dist = abs(col - px) + abs(fila - py)
                if dist == 1:
                    self.current_job = job
                    self.active_jobs.remove(job)
                    break

    def on_update(self, delta_time):
        self.game_time += 1
        self.burst_timer += 1

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
