import arcade
from .api import get_city_map, get_jobs

TILE_SIZE = 20
COLOR = {
    "C": arcade.color.LIGHT_GRAY,
    "P": arcade.color.DARK_SPRING_GREEN,
    "B": arcade.color.DARK_SLATE_GRAY
}

class CourierQuestGame(arcade.Window):
    def __init__(self):
        self.city = get_city_map()
        self.jobs_all = get_jobs()
        self.jobs_available = []
        self.current_job = None
        self.money = 0.0
        self.elapsed = 0.0
        self.goal = float(self.city.goal or 1500.0)
        self.max_time = int(self.city.max_time or 900)
        w = self.city.width * TILE_SIZE
        h = self.city.height * TILE_SIZE
        super().__init__(w, h, "Courier Quest", resizable=True)
        self.set_minimum_size(500, 400)
        arcade.set_background_color(arcade.color.SKY_BLUE)
        self.player_pos = self._start_on_street()
        self.game_over = False
        self.win = False

    def _start_on_street(self):
        for y, row in enumerate(self.city.tiles):
            for x, t in enumerate(row):
                if t == "C":
                    return (y, x)
        return (0, 0)

    def setup(self):
        pass

    def on_update(self, dt):
        if self.game_over:
            return
        self.elapsed += dt
        tsec = int(self.elapsed)
        self.jobs_available = [j for j in self.jobs_all if j.release_time <= tsec and (self.current_job is None or j.id != self.current_job.id)]
        if self.money >= self.goal:
            self.game_over = True
            self.win = True
        if tsec >= self.max_time:
            self.game_over = True
            self.win = self.money >= self.goal

    def on_draw(self):
        self.clear()
        for y, row in enumerate(self.city.tiles):
            for x, t in enumerate(row):
                px = x * TILE_SIZE + TILE_SIZE / 2
                py = self.height - (y * TILE_SIZE + TILE_SIZE / 2)
                arcade.draw_rectangle_filled(px, py, TILE_SIZE - 1, TILE_SIZE - 1, COLOR.get(t, arcade.color.RED))
        if self.current_job:
            dx, dy = self.current_job.dropoff
            px = dx * TILE_SIZE + TILE_SIZE / 2
            py = self.height - (dy * TILE_SIZE + TILE_SIZE / 2)
            arcade.draw_rectangle_outline(px, py, TILE_SIZE, TILE_SIZE, arcade.color.GOLD, 2)
        for job in self.jobs_available:
            px, py = job.pickup
            px = px * TILE_SIZE + TILE_SIZE / 2
            py = self.height - (py * TILE_SIZE + TILE_SIZE / 2)
            arcade.draw_rectangle_outline(px, py, TILE_SIZE, TILE_SIZE, arcade.color.BLUE, 1)
        x, y = self.player_pos[1], self.player_pos[0]
        px = x * TILE_SIZE + TILE_SIZE / 2
        py = self.height - (y * TILE_SIZE + TILE_SIZE / 2)
        arcade.draw_rectangle_filled(px, py, TILE_SIZE - 2, TILE_SIZE - 2, arcade.color.ORANGE)
        tleft = max(0, self.max_time - int(self.elapsed))
        hud = f"$ {int(self.money)}  Tiempo {tleft}s  Meta {int(self.goal)}"
        arcade.draw_text(hud, 10, 10, arcade.color.BLACK, 14)
        if self.current_job:
            arcade.draw_text(f"Pedido {self.current_job.id}", 10, 30, arcade.color.BLACK, 14)
        if self.game_over:
            msg = "Victoria" if self.win else "Tiempo agotado"
            arcade.draw_text(msg, self.width/2-80, self.height/2, arcade.color.BLACK, 24)

    def mover(self, dx, dy):
        if self.game_over:
            return
        nf = self.player_pos[0] + dy
        nc = self.player_pos[1] + dx
        if 0 <= nf < self.city.height and 0 <= nc < self.city.width:
            if self.city.tiles[nf][nc] == "C":
                self.player_pos = (nf, nc)

    def on_key_press(self, key, modifiers):
        if key == arcade.key.UP:
            self.mover(0, -1)
        elif key == arcade.key.DOWN:
            self.mover(0, 1)
        elif key == arcade.key.LEFT:
            self.mover(-1, 0)
        elif key == arcade.key.RIGHT:
            self.mover(1, 0)
        elif key == arcade.key.E:
            self.interactuar()

    def interactuar(self):
        f, c = self.player_pos
        if self.current_job:
            dx, dy = self.current_job.dropoff
            if abs(c - dx) + abs(f - dy) <= 1:
                self.money += float(self.current_job.payout)
                self.jobs_all = [j for j in self.jobs_all if j.id != self.current_job.id]
                self.current_job = None
        else:
            for j in self.jobs_available:
                px, py = j.pickup
                if abs(c - px) + abs(f - py) <= 2:
                    self.current_job = j
                    break
