import json
import os
import arcade

TAM_CELDA = 32
MARGEN = 2
RUTA_MAPA = os.path.join("datos", "ciudad.json")

COLORES = {
    "C": arcade.color.SILVER,
    "B": arcade.color.DARK_BROWN,
    "P": arcade.color.DARK_SEA_GREEN,
}

class Juego(arcade.Window):
    def __init__(self):
        data = self._cargar_mapa(RUTA_MAPA)
        self.mapa = data["tiles"]
        self.legend = data["legend"]
        self.ancho = data["width"]
        self.alto = data["height"]
        w = self.ancho * (TAM_CELDA + MARGEN) + MARGEN
        h = self.alto * (TAM_CELDA + MARGEN) + MARGEN + 40
        super().__init__(w, h, "Courier Quest - Grilla y Movimiento", update_rate=1/60)
        arcade.set_background_color(arcade.color.ASH_GREY)
        self.jx, self.jy = self._buscar_inicio()
        self.vel = 1

    def _cargar_mapa(self, ruta):
        if not os.path.exists(ruta):
            raise FileNotFoundError(f"No existe {ruta}. Crea datos/ciudad.json")
        with open(ruta, "r", encoding="utf-8") as f:
            raw = f.read().strip()
        if not raw:
            raise ValueError(f"Archivo vacío: {ruta}")
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON inválido en {ruta}: {e.msg} (línea {e.lineno}, col {e.colno})")
        for k in ("width", "height", "tiles", "legend"):
            if k not in data:
                raise ValueError(f"Falta clave '{k}' en {ruta}")
        if len(data["tiles"]) != data["height"]:
            raise ValueError("height no coincide con filas")
        for fila in data["tiles"]:
            if len(fila) != data["width"]:
                raise ValueError("width no coincide con columnas")
        return data

    def _bloqueado(self, x, y):
        codigo = self.mapa[y][x]
        return bool(self.legend.get(codigo, {}).get("blocked", False))

    def _buscar_inicio(self):
        for y, fila in enumerate(self.mapa):
            for x, c in enumerate(fila):
                if not self.legend.get(c, {}).get("blocked", False):
                    return x, y
        return 0, 0

    def _to_px(self, x, y):
        px = MARGEN + x * (TAM_CELDA + MARGEN)
        py = MARGEN + y * (TAM_CELDA + MARGEN)
        return px, py

    def on_draw(self):
        self.clear()
        for y, fila in enumerate(self.mapa):
            for x, c in enumerate(fila):
                px, py = self._to_px(x, y)
                color = COLORES.get(c, arcade.color.GRAY)
                arcade.draw_lrbt_rectangle_filled(
                    left=px, right=px + TAM_CELDA,
                    bottom=py, top=py + TAM_CELDA,
                    color=color
                )
        px, py = self._to_px(self.jx, self.jy)
        arcade.draw_lrbt_rectangle_filled(
            px + 4, px + TAM_CELDA - 4,
            py + 4, py + TAM_CELDA - 4,
            arcade.color.BLUE_SAPPHIRE
        )
        arcade.draw_text(
            f"Pos: ({self.jx},{self.jy})  |  Ancho:{self.ancho} Alto:{self.alto}",
            10, self.height - 30, arcade.color.BLACK, 14
        )

    def on_key_press(self, key, modifiers):
        dx = dy = 0
        if key in (arcade.key.W, arcade.key.UP):
            dy = -self.vel
        elif key in (arcade.key.S, arcade.key.DOWN):
            dy = self.vel
        elif key in (arcade.key.A, arcade.key.LEFT):
            dx = -self.vel
        elif key in (arcade.key.D, arcade.key.RIGHT):
            dx = self.vel
        elif key == arcade.key.ESCAPE:
            arcade.exit()
        nx, ny = self.jx + dx, self.jy + dy
        if 0 <= nx < self.ancho and 0 <= ny < self.alto and not self._bloqueado(nx, ny):
            self.jx, self.jy = nx, ny

if __name__ == "__main__":
    Juego()
    arcade.run()
