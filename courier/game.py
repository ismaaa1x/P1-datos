import arcade
from .api import get_city_map, get_jobs

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
        self.current_job = None
        width = self.city_map.width * TILE_SIZE
        height = self.city_map.height * TILE_SIZE
        super().__init__(width, height, "Courier Quest - Pedidos", resizable=True)
        self.set_minimum_size(400, 300)
        self.set_maximum_size(1200, 900)
        arcade.set_background_color(arcade.color.SKY_BLUE)
        self.player_pos = self.buscar_inicio_en_calle()

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

        if self.current_job:
            x, y = self.current_job.dropoff[0], self.current_job.dropoff[1]
            px = x * TILE_SIZE + TILE_SIZE / 2
            py = self.height - (y * TILE_SIZE + TILE_SIZE / 2)
            arcade.draw_rectangle_outline(px, py, TILE_SIZE, TILE_SIZE, arcade.color.GOLD, 2)
        else:
            for job in self.jobs:
                x, y = job.pickup[0], job.pickup[1]
                px = x * TILE_SIZE + TILE_SIZE / 2
                py = self.height - (y * TILE_SIZE + TILE_SIZE / 2)
                arcade.draw_rectangle_outline(px, py, TILE_SIZE, TILE_SIZE, arcade.color.BLUE, 1)

        x, y = self.player_pos[1], self.player_pos[0]
        px = x * TILE_SIZE + TILE_SIZE / 2
        py = self.height - (y * TILE_SIZE + TILE_SIZE / 2)
        arcade.draw_rectangle_filled(px, py, TILE_SIZE - 2, TILE_SIZE - 2, arcade.color.ORANGE)

        text = f"Jugador: fila {self.player_pos[0]}, columna {self.player_pos[1]}"
        arcade.draw_text(text, 10, 10, arcade.color.BLACK, 14)

        if self.current_job:
            txt = f"Llevando: {self.current_job.id}"
            arcade.draw_text(txt, 10, 30, arcade.color.BLACK, 14)

    def mover_jugador(self, dx, dy):
        nueva_fila = self.player_pos[0] + dy
        nueva_col = self.player_pos[1] + dx
        if 0 <= nueva_fila < self.city_map.height and 0 <= nueva_col < self.city_map.width:
            tile = self.city_map.tiles[nueva_fila][nueva_col]
            if tile == "C":
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
            drop_x, drop_y = self.current_job.dropoff
            if (col, fila) == (drop_x, drop_y):
                self.current_job = None
        else:
            for job in self.jobs:
                px, py = job.pickup
                dist = abs(col - px) + abs(fila - py)
                if dist <= 2:
                    self.current_job = job
                    break


