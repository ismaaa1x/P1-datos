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

    
    width = self.city_map.width * TILE_SIZE
    height = self.city_map.height * TILE_SIZE
    self.window.set_size(width, height)
    arcade.set_background_color(arcade.color.SKY_BLUE)
