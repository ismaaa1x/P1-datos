from courier.models import CityMap as CityMapModel

class CityMapData:
    def __init__(self, model: CityMapModel): # Inicializa el mapa de la ciudad a partir del modelo
        
        self.tiles = model.tiles # matriz de listas que representa el mapa de la ciudad
        self.width = model.width # numero de columnas en el mapa
        self.height = model.height # numero de filas en el mapa
        self.legend = model.legend # diccionario que explica los simbolos en el mapa
        self.goal = model.goal  # objetivo de tiempo para completar el mapa
        self.max_time = model.max_time # tiempo maximo permitido para completar el mapa

      
        self.buildings = [] # lista para almacenar informacion sobre edificios
        self.detectar_edificios() # detecta y almacena informacion sobre edificios en el mapa

    def detectar_edificios(self): # Detecta edificios en el mapa y almacena su informacion
        visitado = [[False for _ in fila] for fila in self.tiles] # matriz para rastrear celdas visitadas
        edificios = [] # lista para almacenar informacion sobre edificios detectados

        for y in range(self.height): # Recorre cada fila del mapa
            for x in range(self.width): # Recorre cada columna del mapa
                if self.tiles[y][x] == "B" and not visitado[y][x]: # Si encuentra una celda de edificio no visitada
                    ancho = 0
                    alto = 0

                    
                    while x + ancho < self.width and self.tiles[y][x + ancho] == "B" and not visitado[y][x + ancho]: # Expande el ancho del edificio
                        ancho += 1 

                   
                    while y + alto < self.height and all( # Verifica que toda la fila siguiente sea parte del edificio
                        self.tiles[y + alto][x + dx] == "B" and not visitado[y + alto][x + dx]
                        for dx in range(ancho)
                    ):
                        alto += 1

                   
                    for dy in range(alto): # Marca todas las celdas del edificio como visitadas
                        for dx in range(ancho):
                            visitado[y + dy][x + dx] = True

                    edificios.append({ # Almacena la informacion del edificio detectado
                        "x": x,
                        "y": y,
                        "width": ancho,
                        "height": alto
                    })

        self.buildings = edificios # Actualiza la lista de edificios con la informacion detectada
