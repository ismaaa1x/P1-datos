def __init__(self):   # Constructor de la clase Courier
    super().__init__()  # Llama al constructor de la clase base arcade.Window

    
    self.city_map = get_city_map() # Carga el mapa de la ciudad
    self.jobs = get_jobs() # Carga los trabajos disponibles
    self.weather: WeatherReport = get_weather() # Carga el reporte del clima

  
    self.player_pos = self.buscar_inicio_en_calle() # Encuentra la posición inicial del jugador
    self.current_job: Job | None = None # Trabajo actual del jugador
    self.completed = [] # Lista de trabajos completados
    self.failed = [] # Lista de trabajos fallidos
    self.total_money = 0.0 # Dinero total ganado
    self.resistencia = 100 # Resistencia inicial del jugador
    self.exhausto = False # Estado de agotamiento del jugador

   
    self.game_time = 0.0 # Tiempo de juego transcurrido
    self.remaining_time = self.city_map.goal or 1500 # Tiempo restante para completar el objetivo
    self.release_index = 0 # Índice para liberar trabajos
    self.active_jobs = [] # Lista de trabajos activos
    self.burst_index = 0 # Índice del evento climático actual
    self.burst_timer = 0 # Temporizador para el evento climático
    self.current_burst = self.weather.bursts[0] if self.weather.bursts else None # Evento climático actual

    
    width = self.city_map.width * TILE_SIZE # Ancho de la ventana basado en el mapa
    height = self.city_map.height * TILE_SIZE # Alto de la ventana basado en el mapa
    self.window.set_size(width, height) # Establece el tamaño de la ventana
    arcade.set_background_color(arcade.color.SKY_BLUE) # Color de fondo de la ventana
