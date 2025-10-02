import arcade
from .api import get_city_map, get_jobs, get_weather
from .models import Job, WeatherReport

TILE_SIZE = 32
PLAYER_SPEED = 3

TILE_COLORS = {
    "C": arcade.color.LIGHT_GRAY,
    "P": arcade.color.DARK_SPRING_GREEN,
    "B": arcade.color.DARK_SLATE_GRAY
}

CLIMA_MULTIPLICADOR = {
    "clear": 1.00,
    "clouds": 0.98,
    "rain": 0.85,
    "storm": 0.75,
    "fog": 0.88,
    "wind": 0.92,
    "heat": 0.90,
    "cold": 0.92
}

class CourierQuestGame(arcade.View):
    def __init__(self):
        super().__init__()

        self.city_map = get_city_map()
        self.jobs = get_jobs()
        self.weather: WeatherReport = get_weather()

        self.player_pos = self.buscar_inicio_en_calle()
        self.current_job: Job | None = None
        self.completed = []
        self.failed = []
        self.total_money = 0.0
        self.resistencia = 100
        self.exhausto = False

        self.game_time = 0.0
        self.remaining_time = self.city_map.goal or 1500
        self.release_index = 0
        self.active_jobs = []
        self.burst_index = 0
        self.burst_timer = 0
        self.current_burst = self.weather.bursts[0] if self.weather.bursts else None

        map_width = self.city_map.width * TILE_SIZE
        map_height = self.city_map.height * TILE_SIZE
        max_width = 1000
        max_height = 800
        scale_x = max_width / map_width
        scale_y = max_height / map_height
        self.scale = min(scale_x, scale_y, 1.0)

        self.window.set_size(int(map_width * self.scale), int(map_height * self.scale))
        arcade.set_background_color(arcade.color.SKY_BLUE)

    def buscar_inicio_en_calle(self):
        for y, fila in enumerate(self.city_map.tiles):
            for x, tile in enumerate(fila):
                if tile == "C":
                    return (y, x)
        return (0, 0)

    def on_draw(self):
        self.clear()
        for y, fila in enumerate(self.city_map.tiles):
            for x, tile in enumerate(fila):
                color = TILE_COLORS.get(tile, arcade.color.RED)
                px = x * TILE_SIZE * self.scale + TILE_SIZE * self.scale / 2
                py = self.window.height - (y * TILE_SIZE * self.scale + TILE_SIZE * self.scale / 2)
                arcade.draw_rectangle_filled(px, py, TILE_SIZE * self.scale - 1, TILE_SIZE * self.scale - 1, color)

        for job in self.active_jobs:
            x, y = job.pickup
            px = x * TILE_SIZE * self.scale + TILE_SIZE * self.scale / 2
            py = self.window.height - (y * TILE_SIZE * self.scale + TILE_SIZE * self.scale / 2)
            arcade.draw_rectangle_outline(px, py, TILE_SIZE * self.scale, TILE_SIZE * self.scale, arcade.color.BLUE, 2)

        if self.current_job:
            x, y = self.current_job.dropoff
            px = x * TILE_SIZE * self.scale + TILE_SIZE * self.scale / 2
            py = self.window.height - (y * TILE_SIZE * self.scale + TILE_SIZE * self.scale / 2)
            arcade.draw_rectangle_outline(px, py, TILE_SIZE * self.scale, TILE_SIZE * self.scale, arcade.color.GOLD, 3)

        x, y = self.player_pos[1], self.player_pos[0]
        px = x * TILE_SIZE * self.scale + TILE_SIZE * self.scale / 2
        py = self.window.height - (y * TILE_SIZE * self.scale + TILE_SIZE * self.scale / 2)
        arcade.draw_rectangle_filled(px, py, TILE_SIZE * self.scale - 2, TILE_SIZE * self.scale - 2, arcade.color.ORANGE)

        y_pos = self.window.height - 20
        arcade.draw_text(f"Tiempo: {int(self.game_time)}s / {self.remaining_time}s", 10, y_pos, arcade.color.BLACK, 14)
        y_pos -= 20
        arcade.draw_text(f"Dinero: ₡{self.total_money:.2f} / ₡{self.city_map.goal}", 10, y_pos, arcade.color.BLACK, 14)
        y_pos -= 20
        arcade.draw_text(f"Clima: {self.current_burst.condition if self.current_burst else 'clear'}", 10, y_pos, arcade.color.BLACK, 14)
        y_pos -= 20
        arcade.draw_text(f"Resistencia: {int(self.resistencia)}", 10, y_pos, arcade.color.BLACK, 14)
        y_pos -= 20
        arcade.draw_text(f"Pedidos activos: {len(self.active_jobs)}", 10, y_pos, arcade.color.BLACK, 14)
        y_pos -= 20
        arcade.draw_text(f"Pedidos completados: {len(self.completed)}", 10, y_pos, arcade.color.BLACK, 14)
        y_pos -= 20
        arcade.draw_text(f"Pedidos fallidos: {len(self.failed)}", 10, y_pos, arcade.color.BLACK, 14)

    def mover_jugador(self, dx, dy):
        if self.exhausto:
            return

        nueva_fila = self.player_pos[0] + dy
        nueva_col = self.player_pos[1] + dx
        if 0 <= nueva_fila < self.city_map.height and 0 <= nueva_col < self.city_map.width:
            tile = self.city_map.tiles[nueva_fila][nueva_col]
            if not self.city_map.legend[tile].blocked:
                peso_total = self.current_job.weight if self.current_job else 0
                clima = self.current_burst.condition if self.current_burst else "clear"
                intensidad = self.current_burst.intensity if self.current_burst else 0

                m_clima = CLIMA_MULTIPLICADOR.get(clima, 1.0)
                m_peso = max(0.8, 1 - 0.03 * peso_total)
                m_tile = self.city_map.legend[tile].surface_weight or 1.0
                m_resistencia = 1.0 if self.resistencia > 30 else 0.8 if self.resistencia > 10 else 0.0

                velocidad = PLAYER_SPEED * m_clima * m_peso * m_tile * m_resistencia
                self.player_pos = (nueva_fila, nueva_col)

                gasto = 0.5
                if peso_total > 3:
                    gasto += 0.2 * (peso_total - 3)
                if clima in ["rain", "wind"]:
                    gasto += 0.1
                elif clima == "storm":
                    gasto += 0.3
                elif clima == "heat":
                    gasto += 0.2

                self.resistencia -= gasto
                if self.resistencia <= 0:
                    self.exhausto = True

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
                if (fila, col) == (py, px) or abs(fila - py) + abs(col - px) == 1:
                    self.current_job = job
                    self.active_jobs.remove(job)
                    break

    def on_update(self, delta_time):
        self.game_time += delta_time
        self.burst_timer += delta_time

        # Actualizar clima
        if self.burst_timer >= self.current_burst.duration_sec:
            self.burst_index += 1
            if self.burst_index < len(self.weather.bursts):
                self.current_burst = self.weather.bursts[self.burst_index]
                self.burst_timer = 0

        # Liberar nuevos pedidos
        if self.release_index < len(self.jobs):
            next_job = self.jobs[self.release_index]
            if self.game_time >= next_job.release_time:
                self.active_jobs.append(next_job)
                self.release_index += 1

        # Verificar pedidos fallidos
        still_active = []
        for job in self.active_jobs:
            if self.game_time > job.release_time + 300:
                self.failed.append(job)
            else:
                still_active.append(job)
        self.active_jobs = still_active

        # Recuperar resistencia si está exhausto
        if self.exhausto and self.resistencia < 30:
            self.resistencia += 5 * delta_time
            if self.resistencia >= 30:
                self.exhausto = False

        # Fin del juego
        if self.game_time >= self.remaining_time or self.total_money >= self.city_map.goal:
            from main import PantallaFinal
            final = PantallaFinal(self.total_money, len(self.completed), len(self.failed))
            self.window.show_view(final)
