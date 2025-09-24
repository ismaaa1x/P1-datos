import arcade
from .api import get_city_map

TILE_SIZE = 20

TILE_COLORS = {
    "C": arcade.color.LIGHT_GRAY,          # Calle
    "P": arcade.color.DARK_SPRING_GREEN,   # Parque
    "B": arcade.color.DARK_SLATE_GRAY      # Edificio
}

class CourierQuestGame(arcade.Window):
    def __init__(self):
        self.city_map = get_city_map()
        width = self.city_map.width * TILE_SIZE
        height = self.city_map.height * TILE_SIZE
        super().__init__(width, height, "Courier Quest - Mapa Real", resizable=True)
        self.set_minimum_size(400, 300)
        self.set_maximum_size(1200, 900)
        arcade.set_background_color(arcade.color.SKY_BLUE)

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
        arcade.draw_text("Mapa cargado desde el API", 10, 10, arcade.color.BLACK, 14)
