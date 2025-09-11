import arcade
from collections import deque
from ..api_client import get_map, get_jobs, get_weather

# ------------------ Normalizadores ------------------

def _unwrap_data(obj):
    # Desenvuelve formatos tipo {"version": "...", "data": {...}}
    if isinstance(obj, dict) and "data" in obj and isinstance(obj["data"], dict):
        return obj["data"]
    return obj

def _norm_map(m):
    m = _unwrap_data(m)
    if not isinstance(m, dict):
        raise ValueError(f"Mapa inválido: tipo {type(m)}")
    # si viene envuelto en "map"
    if "map" in m and isinstance(m["map"], dict):
        m = m["map"]
    tiles = m.get("tiles") or m.get("grid") or m.get("matrix") or m.get("cells")
    legend = m.get("legend") or m.get("key") or {}
    width  = m.get("width") or m.get("w")
    height = m.get("height") or m.get("h")
    if tiles is None:
        raise ValueError(f"Mapa inválido: no hay 'tiles'/'grid'/'matrix'/'cells'. Claves: {list(m.keys())}")
    if width is None:
        width = len(tiles[0]) if tiles else 0
    if height is None:
        height = len(tiles)
    return {
        "tiles": tiles,
        "legend": legend,
        "width": int(width),
        "height": int(height),
    }

def _to_float(x, default=0.0):
    try:
        return float(x)
    except Exception:
        return float(default)

def _norm_jobs(j):
    j = _unwrap_data(j)

    # Si viene como dict, intenta localizar la lista de pedidos buscando claves comunes
    if isinstance(j, dict):
        # 1) claves habituales
        for key in ("jobs", "orders", "items", "list", "results", "records"):
            if key in j and isinstance(j[key], list):
                j = j[key]
                break
        # 2) si sigue siendo dict, busca la PRIMERA lista en cualquiera de sus valores
        if isinstance(j, dict):
            for v in j.values():
                if isinstance(v, list):
                    j = v
                    break

    if not isinstance(j, list):
        # Mensaje útil para depurar si cambiara el formato
        raise ValueError(f"Jobs inválidos: tipo {type(j)}. Claves disponibles: {list(j.keys()) if isinstance(j, dict) else 'n/a'}")

    out = []
    for p in j:
        if not isinstance(p, dict):
            continue
        pid = p.get("id") or p.get("job_id") or p.get("code") or "?"
        pickup  = p.get("pickup")  or p.get("source") or p.get("from")
        dropoff = p.get("dropoff") or p.get("target") or p.get("to")

        # Acepta coordenadas como tuplas/listas o dicts tipo {"x":..,"y":..}
        def _coord(val):
            if isinstance(val, (list, tuple)) and len(val) >= 2:
                return int(val[0]), int(val[1])
            if isinstance(val, dict) and "x" in val and "y" in val:
                return int(val["x"]), int(val["y"])
            return None

        pu = _coord(pickup)
        do = _coord(dropoff)
        if pu is None or do is None:
            continue

        out.append({
            "id": pid,
            "pickup": pu,
            "dropoff": do,
            "weight": _to_float(p.get("weight", 0)),
            "payout": _to_float(p.get("payout", 0)),
            "priority": _to_float(p.get("priority", 0)),
            "deadline_s": _to_float(p.get("deadline"), float("inf")),
            "release_time": _to_float(p.get("release_time"), 0),
        })
    return out


def _norm_weather(w):
    w = _unwrap_data(w)
    if isinstance(w, dict) and "bursts" in w and isinstance(w["bursts"], list):
        return w
    # permitir {"weather": {"bursts": [...]}}
    if isinstance(w, dict) and "weather" in w and isinstance(w["weather"], dict):
        ww = w["weather"]
        if "bursts" in ww and isinstance(ww["bursts"], list):
            return ww
    return {"bursts": []}

# ------------------ Juego ------------------

TAM_CELDA = 32
MARGEN = 2
V0 = 3.0
K_COSTE = 1.2

COLORES = {
    "C": arcade.color.SILVER,
    "B": arcade.color.DARK_BROWN,
    "P": arcade.color.DARK_SEA_GREEN,
}

class Juego(arcade.Window):
    def __init__(self):
        # -------- MAPA --------
        mapa_raw = get_map()
        mapa = _norm_map(mapa_raw)
        self.mapa = mapa["tiles"]
        self.legend = mapa["legend"]
        self.ancho = mapa["width"]
        self.alto = mapa["height"]

        w = self.ancho * (TAM_CELDA + MARGEN) + MARGEN
        h = self.alto * (TAM_CELDA + MARGEN) + MARGEN + 64
        super().__init__(w, h, "Courier Quest - API + Offline", update_rate=1/60)
        arcade.set_background_color(arcade.color.ASH_GREY)

        # Debug opcional
        if isinstance(mapa_raw, dict):
            print("[DEBUG] map keys:", list(mapa_raw.keys()))

        self.jx, self.jy = self._buscar_inicio()
        self.vel = 1
        self.stamina = 100.0
        self.reputacion = 70.0
        self.cash = 0
        self.tiempo = 0.0

        # -------- PEDIDOS --------
        jobs_raw = get_jobs()
        if isinstance(jobs_raw, dict):
            print("[DEBUG] jobs dict keys:", list(jobs_raw.keys()))
        pedidos = _norm_jobs(jobs_raw)
        self.backlog = [p for p in pedidos if p["release_time"] > 0]
        self.disponibles = deque(sorted(
            [p for p in pedidos if p["release_time"] <= 0],
            key=lambda q: (-q["priority"], -q["payout"])
        ))
        self.inventario = deque()

        # -------- CLIMA --------
        weather_raw = get_weather()
        if isinstance(weather_raw, dict):
            print("[DEBUG] weather keys:", list(weather_raw.keys()))
        self.weather = _norm_weather(weather_raw)
        self.weather_t = 0.0
        self.weather_idx = 0
        self.weather_curr = {"condition": "clear", "intensity": 0.0}

        self.v_inst = V0

    # ---------- util ----------
    def _deadline_a_segundos(self, v):
        if v is None:
            return float("inf")
        try:
            return float(v)
        except Exception:
            return float("inf")

    def _bloqueado(self, x, y):
        c = self.mapa[y][x]
        return bool(self.legend.get(c, {}).get("blocked", False))

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

    def _barra(self, x, y, w, h, v, fondo, lleno):
        arcade.draw_lrbt_rectangle_filled(x, x + w, y, y + h, fondo)
        pct = max(0.0, min(1.0, v / 100.0))
        lw = int((w - 2) * pct)
        if lw > 0:
            arcade.draw_lrbt_rectangle_filled(x + 1, x + 1 + lw, y + 1, y + h - 1, lleno)

    # ---------- multiplicadores ----------
    def _mult_clima(self):
        cond = (self.weather_curr or {}).get("condition", "clear")
        if cond == "rain":
            return 0.90
        if cond == "storm":
            return 0.80
        if cond == "heat":
            return 0.85
        return 1.0

    def _mult_peso(self):
        peso = sum(p.get("weight", 0.0) for p in self.inventario)
        return max(0.5, 1.0 - 0.03 * peso)

    def _mult_reputacion(self):
        return 1.03 if self.reputacion >= 90 else 1.0

    def _mult_resistencia(self):
        if self.stamina < 10:
            return 0.0
        if self.stamina < 60:
            return 0.80
        return 1.0

    def _peso_superficie(self, nx, ny):
        code = self.mapa[ny][nx]
        return float(self.legend.get(code, {}).get("surface_weight", 1.0))

    def _velocidad_actual(self, nx, ny):
        m_clima = self._mult_clima()
        m_peso  = self._mult_peso()
        m_rep   = self._mult_reputacion()
        m_res   = self._mult_resistencia()
        s_w     = self._peso_superficie(nx, ny)
        v = 3.0 * m_clima * m_peso * m_rep * m_res * s_w
        return max(0.0, v)

    def _coste_resistencia_por_paso(self, v):
        if v <= 0.001:
            return 999.0
        return 1.2 / v

    # ---------- render ----------
    def on_draw(self):
        self.clear()

        # mapa
        for y, fila in enumerate(self.mapa):
            for x, c in enumerate(fila):
                px, py = self._to_px(x, y)
                color = COLORES.get(c, arcade.color.GRAY)
                arcade.draw_lrbt_rectangle_filled(px, px + TAM_CELDA, py, py + TAM_CELDA, color)

        # pickups
        for p in self.disponibles:
            x, y = p["pickup"]
            px, py = self._to_px(x, y)
            arcade.draw_circle_filled(px + TAM_CELDA / 2, py + TAM_CELDA / 2, 6, arcade.color.GOLD)

        # dropoffs
        for p in self.inventario:
            x, y = p["dropoff"]
            px, py = self._to_px(x, y)
            arcade.draw_circle_filled(px + TAM_CELDA / 2, py + TAM_CELDA / 2, 6, arcade.color.MEDIUM_PURPLE)

        # jugador
        px, py = self._to_px(self.jx, self.jy)
        arcade.draw_lrbt_rectangle_filled(px + 4, px + TAM_CELDA - 4, py + 4, py + TAM_CELDA - 4, arcade.color.BLUE_SAPPHIRE)

        # HUD
        self._barra(10, self.height - 24, 220, 12, self.stamina, arcade.color.DARK_GRAY, arcade.color.APPLE_GREEN)
        arcade.draw_text("RES", 236, self.height - 28, arcade.color.BLACK, 12)
        self._barra(280, self.height - 24, 220, 12, self.reputacion, arcade.color.DARK_GRAY, arcade.color.AZURE)
        arcade.draw_text("REP", 506, self.height - 28, arcade.color.BLACK, 12)

        total_peso = sum(p.get("weight", 0.0) for p in self.inventario)
        cond = (self.weather_curr or {}).get("condition", "clear")
        arcade.draw_text(
            f"Inv:{len(self.inventario)}  W:{total_peso:.1f}  $:{self.cash}  Clima:{cond}  v:{self.v_inst:.2f}",
            560, self.height - 28, arcade.color.BLACK, 12
        )

    # ---------- input ----------
    def on_key_press(self, key, modifiers):
        dx = dy = 0
        if key in (arcade.key.W, arcade.key.UP): dy = -self.vel
        elif key in (arcade.key.S, arcade.key.DOWN): dy = self.vel
        elif key in (arcade.key.A, arcade.key.LEFT): dx = -self.vel
        elif key in (arcade.key.D, arcade.key.RIGHT): dx = self.vel
        elif key == arcade.key.E:
            self._aceptar_cercano(); return
        elif key == arcade.key.SPACE:
            self._entregar_si_corresponde(); return
        elif key == arcade.key.ESCAPE:
            arcade.exit(); return

        if dx == dy == 0 or self.stamina <= 0:
            return

        nx, ny = self.jx + dx, self.jy + dy
        if 0 <= nx < self.ancho and 0 <= ny < self.alto and not self._bloqueado(nx, ny):
            v = self._velocidad_actual(nx, ny)
            if v <= 0.01:
                self.v_inst = 0.0
                return
            coste = self._coste_resistencia_por_paso(v)
            self.jx, self.jy = nx, ny
            self.stamina = max(0.0, self.stamina - coste)
            self.v_inst = v

    # ---------- juego ----------
    def _aceptar_cercano(self):
        if not self.disponibles:
            return
        candidatos = []
        for p in list(self.disponibles):
            x, y = p["pickup"]
            if abs(x - self.jx) + abs(y - self.jy) <= 1:
                candidatos.append(p)
        if not candidatos:
            return
        candidatos.sort(key=lambda p: (-p["priority"], -p["payout"]))
        elegido = candidatos[0]
        self.disponibles.remove(elegido)
        self.inventario.append(elegido)

    def _entregar_si_corresponde(self):
        if not self.inventario:
            return
        p = self.inventario[0]
        x, y = p["dropoff"]
        if (self.jx, self.jy) == (x, y):
            self.inventario.popleft()
            self.cash += p.get("payout", 0.0)
            if self.tiempo > float(p.get("deadline_s", float("inf"))):
                self.reputacion = max(0.0, self.reputacion - 8.0)
            else:
                self.reputacion = min(100.0, self.reputacion + 3.0)
            self.stamina = min(100.0, self.stamina + 5.0)

    def on_update(self, dt):
        self.tiempo += dt
        if self.stamina < 100.0:
            self.stamina = min(100.0, self.stamina + 4.0 * dt)

        if self.backlog:
            nuevos = [p for p in self.backlog if p["release_time"] <= self.tiempo]
            if nuevos:
                self.backlog = [p for p in self.backlog if p["release_time"] > self.tiempo]
                for p in nuevos:
                    self.disponibles.append(p)
                self.disponibles = deque(sorted(
                    list(self.disponibles),
                    key=lambda q: (-q["priority"], -q["payout"])
                ))

        bursts = (self.weather or {}).get("bursts", [])
        if bursts:
            self.weather_t += dt
            dur = float(bursts[self.weather_idx].get("duration_sec", 9999))
            if self.weather_t >= dur:
                self.weather_t = 0.0
                self.weather_idx = (self.weather_idx + 1) % len(bursts)
            self.weather_curr = bursts[self.weather_idx]
        else:
            self.weather_curr = {"condition": "clear", "intensity": 0.0}

def main():
    Juego()
    arcade.run()

if __name__ == "__main__":
    main()


