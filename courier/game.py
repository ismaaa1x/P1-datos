import arcade #libreria para crear juegos 2D
import json
import os
import datetime

from .api import get_jobs, get_weather # funciones para obtener datos de la API
from .models import Job, WeatherReport # modelos de datos
from courier.models import CityMap as CityMapModel # modelo del mapa de la ciudad
from courier.city_map import CityMapData # clase para manejar el mapa de la ciudad

TILE_SIZE = 32 # tamaño de cada celda del mapa en pixeles
PLAYER_SPEED = 3 # velocidad base del jugador en celdas por segundo

CLIMA_MULTIPLICADOR = { # multiplicadores de tiempo segun el clima
    "clear": 1.00, 
    "clouds": 0.98,
    "rain": 0.85,
    "storm": 0.75,
    "fog": 0.88,
    "wind": 0.92,
    "heat": 0.90,
    "cold": 0.92
}

class CourierQuestGame(arcade.View): # Clase principal del juego
    def __init__(self): 
        super().__init__() 

       
        ruta_mapa = os.path.join(os.path.dirname(__file__), "..", "api_cache", "city_map.json") # Ruta al archivo del mapa de la ciudad
        with open(ruta_mapa, "r", encoding="utf-8") as f: # Abre el archivo del mapa
            raw = json.load(f) # Carga los datos JSON
            model = CityMapModel.model_validate(raw["data"]) 
            self.city_map = CityMapData(model) 

       
        self.historial_movimientos = [] # lista para almacenar historial de movimientos
        self.max_deshacer = 15 # maximo de movimientos que se pueden deshacer

        #carga de las imagenes 
        self.sprite_edificio = arcade.load_texture("assets/edificio.png") 
        self.sprite_arbusto = arcade.load_texture("assets/arbusto.png")
        self.sprite_pedido = arcade.load_texture("assets/box.png")
        self.sprite_entrega = arcade.load_texture("assets/icon.png")
        self.sprite_repartidor = arcade.load_texture("assets/chatex.png")
        self.angulo_repartidor = 0

        
        self.jobs = get_jobs() #obtiene la lista de pedidos
        self.weather: WeatherReport = get_weather() #obtiene el reporte del clima
        self.burst_index = 0
        self.burst_timer = 0
        self.current_burst = self.weather.bursts[0] if self.weather.bursts else None #evento climatico actual

        #define el estado inicial del jugador, energia,dinero, etc
        self.player_pos = self.buscar_inicio_en_calle() 
        self.current_job: Job | None = None
        self.completed = []
        self.failed = []
        self.total_money = 0.0
        self.resistencia = 100
        self.exhausto = False
        self.game_time = 0.0

       # tiempo restante para completar el objetivo, ajustado por el clima
        clima_actual = self.current_burst.condition if self.current_burst else "clear"
        multiplicador = CLIMA_MULTIPLICADOR.get(clima_actual, 1.0)
        self.remaining_time = int((self.city_map.goal or 1500) * multiplicador)

        self.release_index = 0 
        self.active_jobs = [] #lista de pedidos activos

       # configura la ventana del juego
        map_width = self.city_map.width * TILE_SIZE
        map_height = self.city_map.height * TILE_SIZE
        self.panel_width = 300
        scale_x = (1000 - self.panel_width) / map_width
        scale_y = 800 / map_height
        self.scale = min(scale_x, scale_y, 1.0)
        
        self.window.set_size(int(map_width * self.scale + self.panel_width), int(map_height * self.scale))
        arcade.set_background_color(arcade.color.SKY_BLUE)


    def obtener_vecinos(self, y, x): # Obtiene los vecinos de una celda que son calles
            vecinos = { 
                "arriba": y > 0 and self.city_map.tiles[y - 1][x] == "C",
                "abajo": y < self.city_map.height - 1 and self.city_map.tiles[y + 1][x] == "C",
                "izquierda": x > 0 and self.city_map.tiles[y][x - 1] == "C",
                "derecha": x < self.city_map.width - 1 and self.city_map.tiles[y][x + 1] == "C"
            }
            return vecinos


    def on_resize(self, width, height): # Maneja el redimensionamiento de la ventana
        super().on_resize(width, height)
        self.window.set_viewport(0, width, 0, height)

        map_width = self.city_map.width * TILE_SIZE
        map_height = self.city_map.height * TILE_SIZE
        panel_width = 300
        scale_x = (width - panel_width) / map_width
        scale_y = height / map_height
        self.scale = min(scale_x, scale_y, 1.0)

    def buscar_inicio_en_calle(self): # Busca una celda de calle para iniciar al jugador
        for y, fila in enumerate(self.city_map.tiles):
            for x, tile in enumerate(fila):
                if tile == "C":
                    return (y, x)
        return (0, 0)

    def on_draw(self): # Dibuja todos los elementos del juego
        self.clear() 

        
        for y, fila in enumerate(self.city_map.tiles): 
            for x, tile in enumerate(fila):
                px = x * TILE_SIZE * self.scale + TILE_SIZE * self.scale / 2
                py = self.window.height - (y * TILE_SIZE * self.scale + TILE_SIZE * self.scale / 2)

                if tile == "C": # Dibuja las calles
                    arcade.draw_rectangle_filled( 
                        px, py,
                        TILE_SIZE * self.scale,
                        TILE_SIZE * self.scale,
                        arcade.color.BLACK
                    )

                elif tile == "P": # Dibuja los arbustos
                    arcade.draw_texture_rectangle(
                        px, py,
                        TILE_SIZE * self.scale * 1.2,
                        TILE_SIZE * self.scale * 1.2,
                        self.sprite_arbusto
                    )

       
        for edificio in self.city_map.buildings: # Dibuja los edificios detectados
            x = edificio["x"]
            y = edificio["y"]
            w = edificio["width"]
            h = edificio["height"]
            px = x * TILE_SIZE * self.scale + (w * TILE_SIZE * self.scale) / 2
            py = self.window.height - (y * TILE_SIZE * self.scale + (h * TILE_SIZE * self.scale) / 2)
            arcade.draw_texture_rectangle(px, py, w * TILE_SIZE * self.scale, h * TILE_SIZE * self.scale, self.sprite_edificio)

        
        for job in self.active_jobs: # Dibuja los  pedidos activos
            x, y = job.pickup
            px = x * TILE_SIZE * self.scale + TILE_SIZE * self.scale / 2
            py = self.window.height - (y * TILE_SIZE * self.scale + TILE_SIZE * self.scale / 2)
            arcade.draw_texture_rectangle(px, py, TILE_SIZE * self.scale * 1.0, TILE_SIZE * self.scale * 1.0, self.sprite_pedido)

       
        if self.current_job: # Dibuja el punto de entrega del pedido actual
            x, y = self.current_job.dropoff
            px = x * TILE_SIZE * self.scale + TILE_SIZE * self.scale / 2
            py = self.window.height - (y * TILE_SIZE * self.scale + TILE_SIZE * self.scale / 2)
            arcade.draw_texture_rectangle(px, py, TILE_SIZE * self.scale * 1.2, TILE_SIZE * self.scale * 1.2, self.sprite_entrega)

       
        x, y = self.player_pos[1], self.player_pos[0] # Dibuja al jugador
        px = x * TILE_SIZE * self.scale + TILE_SIZE * self.scale / 2
        py = self.window.height - (y * TILE_SIZE * self.scale + TILE_SIZE * self.scale / 2)
        arcade.draw_texture_rectangle(px, py, TILE_SIZE * self.scale * 1.4, TILE_SIZE * self.scale * 1.4, self.sprite_repartidor, angle=self.angulo_repartidor)

        
        self.dibujar_panel_lateral() 






    def dibujar_barra(self, x, y, valor, maximo, etiqueta): # Dibuja una barra de resistencia y reputacion
        ancho = 200
        alto = 16
        porcentaje = max(0, min(valor / maximo, 1.0))
        if porcentaje > 0.7:
            color_barra = arcade.color.GREEN
        elif porcentaje > 0.4:
            color_barra = arcade.color.ORANGE
        else:
            color_barra = arcade.color.RED
        arcade.draw_rectangle_filled(x + ancho / 2, y, ancho, alto, arcade.color.GRAY)
        arcade.draw_rectangle_filled(x + (porcentaje * ancho) / 2, y, porcentaje * ancho, alto, color_barra)
        arcade.draw_text(f"{etiqueta}: {int(valor)} / {int(maximo)}", x, y + 20, arcade.color.BLACK, 12)

    def dibujar_panel_lateral(self): # Dibuja el panel lateral con informacion del juego
        x0 = self.window.width - self.panel_width
        y = self.window.height - 30

        
        arcade.draw_lrtb_rectangle_filled(x0, self.window.width, self.window.height, 0, arcade.color.LIGHT_GRAY)

        
        arcade.draw_text("Estado del repartidor", x0 + 20, y, arcade.color.BLACK, 18)
        y -= 40

       
        arcade.draw_text(f"Tiempo: {int(self.game_time)}s / {self.remaining_time}s", x0 + 20, y, arcade.color.BLACK, 14)
        y -= 30
        arcade.draw_text(f"Clima: {self.current_burst.condition}", x0 + 20, y, arcade.color.BLACK, 14)
        y -= 40

        
        self.dibujar_barra(x0 + 20, y, self.resistencia, 100, "Resistencia")
        y -= 50
        reputacion = max(0, 10 * len(self.completed) / (1 + len(self.completed) + len(self.failed)))
        self.dibujar_barra(x0 + 20, y, reputacion, 10, "Reputación")
        y -= 50

       
        arcade.draw_text(f"Velocidad: {PLAYER_SPEED:.2f} m/s", x0 + 20, y, arcade.color.BLACK, 14)
        y -= 30
        arcade.draw_text(f"Dinero: ₡{self.total_money:.2f}", x0 + 20, y, arcade.color.BLACK, 14)
        y -= 30
        arcade.draw_text(f"Pedidos activos: {len(self.active_jobs)}", x0 + 20, y, arcade.color.BLACK, 14)
        y -= 30

        
        if self.release_index < len(self.jobs):
            siguiente = self.jobs[self.release_index]
            arcade.draw_text(f"Próximo pedido en: {int(siguiente.release_time - self.game_time)}s", x0 + 20, y, arcade.color.DARK_RED, 12)
            y -= 30

       
        arcade.draw_text("Pedidos:", x0 + 20, y, arcade.color.BLACK, 14)
        y -= 20
        for job in self.active_jobs[:5]:
            arcade.draw_text(f"{job.id} → ({job.dropoff[0]},{job.dropoff[1]})", x0 + 20, y, arcade.color.DARK_BLUE, 12)
            y -= 15
            arcade.draw_text(f"₡{job.payout:.2f} | {job.weight}kg", x0 + 20, y, arcade.color.DARK_GREEN, 12)
            y -= 25

       
        y -= 20
        arcade.draw_text("Controles:", x0 + 20, y, arcade.color.BLACK, 16)
        y -= 20
        arcade.draw_text("← ↑ ↓ →  Mover repartidor", x0 + 20, y, arcade.color.DARK_GRAY, 14)
        y -= 20
        arcade.draw_text("U  Deshacer movimiento", x0 + 20, y, arcade.color.DARK_GRAY, 14)
        y -= 20
        arcade.draw_text("G  Guardar partida", x0 + 20, y, arcade.color.DARK_GRAY, 14)
        y -= 20
        arcade.draw_text("H  Ver historial", x0 + 20, y, arcade.color.DARK_GRAY, 14)
        y -= 20
        arcade.draw_text("R  Reiniciar partida", x0 + 20, y, arcade.color.DARK_GRAY, 14)
        y -= 20
        arcade.draw_text("ESC  Terminar juego", x0 + 20, y, arcade.color.DARK_GRAY, 14)



    def mover_jugador(self, dx, dy): # controla el movimiento del jugador y aplica restricciones
        if self.exhausto:
            return

        nueva_fila = self.player_pos[0] + dy
        nueva_col = self.player_pos[1] + dx

       
        if 0 <= nueva_fila < self.city_map.height and 0 <= nueva_col < self.city_map.width:
            tile = self.city_map.tiles[nueva_fila][nueva_col]

            
            if not self.city_map.legend[tile].blocked:
                
                if len(self.historial_movimientos) >= self.max_deshacer:
                    self.historial_movimientos.pop(0)
                self.historial_movimientos.append(self.player_pos)

               
                peso_total = self.current_job.weight if self.current_job else 0
                clima = self.current_burst.condition if self.current_burst else "clear"
                intensidad = self.current_burst.intensity if self.current_burst else 0

                m_clima = CLIMA_MULTIPLICADOR.get(clima, 1.0)
                m_peso = max(0.8, 1 - 0.03 * peso_total)
                m_tile = self.city_map.legend[tile].surface_weight or 1.0
                m_resistencia = 1.0 if self.resistencia > 30 else 0.8 if self.resistencia > 10 else 0.0

                velocidad = PLAYER_SPEED * m_clima * m_peso * m_tile * m_resistencia 
                self.velocidad_actual = velocidad 

                
                if dx == 0 and dy == -1:
                    self.angulo_repartidor = 270
                elif dx == 0 and dy == 1:
                    self.angulo_repartidor = 90
                elif dx == -1 and dy == 0:
                    self.angulo_repartidor = 180
                elif dx == 1 and dy == 0:
                    self.angulo_repartidor = 0

                
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


    def on_key_press(self, key, modifiers): # Maneja la entrada del teclado para mover al jugador y otras acciones


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
        elif key == arcade.key.U and self.historial_movimientos:
             self.player_pos = self.historial_movimientos.pop()
        elif key == arcade.key.U and self.historial_movimientos:
                self.player_pos = self.historial_movimientos.pop()

        elif key == arcade.key.G:
                self.guardar_historial()
                print(" Partida guardada.")

        elif key == arcade.key.H:
                self.mostrar_historial()

        elif key == arcade.key.R:
                from main import CourierQuestGame
                nuevo_juego = CourierQuestGame()
                self.window.show_view(nuevo_juego)

        elif key == arcade.key.ESCAPE:
                self.finalizar_partida()






    def interactuar(self): # Maneja la interaccion del jugador con pedidos
        fila, col = self.player_pos
        if self.current_job: # Si ya tiene un pedido, verifica si esta en el punto de entrega
            dx, dy = self.current_job.dropoff
            if (fila, col) == (dy, dx) or abs(fila - dy) + abs(col - dx) == 1:
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

    def on_update(self, delta_time): # Actualiza el estado del juego cada frame
        self.game_time += delta_time
        self.burst_timer += delta_time

       
        if self.burst_timer >= self.current_burst.duration_sec: # Cambia el evento climatico si ha pasado su duracion
            self.burst_index += 1
            if self.burst_index < len(self.weather.bursts):
                self.current_burst = self.weather.bursts[self.burst_index]
                self.burst_timer = 0

        
        if self.release_index < len(self.jobs): # Libera nuevos pedidos segun el tiempo de juego
            next_job = self.jobs[self.release_index]
            if self.game_time >= next_job.release_time:
                self.active_jobs.append(next_job)
                self.release_index += 1

       
        still_active = [] # Verifica los pedidos activos y marca como fallidos los que han expirado
        for job in self.active_jobs:
            if self.game_time > job.release_time + 300:
                self.failed.append(job)
            else:
                still_active.append(job)
        self.active_jobs = still_active

        
        if self.exhausto and self.resistencia < 30: # Regenera la resistencia si el jugador esta exhausto
            self.resistencia += 5 * delta_time
            if self.resistencia >= 30:
                self.exhausto = False

        
        tiempo_terminado = self.game_time >= self.remaining_time # Verifica si se ha cumplido alguna condicion de fin de juego
        pedidos_terminados = not self.active_jobs and not self.current_job
        objetivo_dinero = self.total_money >= self.city_map.goal

        if tiempo_terminado or pedidos_terminados or objetivo_dinero: 
            self.finalizar_partida()


             

    def guardar_historial(self): # Guarda el historial de la partida en un archivo JSON

        reputacion = max(0, 10 * len(self.completed) / (1 + len(self.completed) + len(self.failed)))
        partida = {
            "fecha": datetime.datetime.now().isoformat(),
            "clima": self.current_burst.condition if self.current_burst else "clear",
            "duracion": self.game_time,
            "dinero": self.total_money,
            "reputacion": reputacion,
            "pedidos_completados": len(self.completed),
            "pedidos_fallidos": len(self.failed)
        }

        ruta = os.path.join(os.path.dirname(__file__), "..", "saves", "historial.json")
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                historial = json.load(f)
        except FileNotFoundError:
            historial = []

        historial.append(partida)

        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(historial, f, indent=4)




    def mostrar_historial(self): # Muestra el historial de partidas guardadas
        ruta = os.path.join(os.path.dirname(__file__), "..", "saves", "historial.json")
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                historial = json.load(f)
            print("\n  Historial de partidas:")
            for partida in historial:
                print(f"- {partida['fecha']}: €{partida['dinero']} | Clima: {partida['clima']} | Reputación: {partida['reputacion']} | {partida['pedidos_completados']} pedidos completados")
        except FileNotFoundError:
            print("No hay historial guardado.")


    def finalizar_partida(self): # Finaliza la partida y muestra el resumen
        self.guardar_historial()
        self.mostrar_historial()
        print(" La partida ha terminado.")
        arcade.close_window()
