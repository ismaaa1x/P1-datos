from courier.models import CityMap as CityMapModel

class CityMapData:
    def __init__(self, model: CityMapModel):
        
        self.tiles = model.tiles
        self.width = model.width
        self.height = model.height
        self.legend = model.legend
        self.goal = model.goal
        self.max_time = model.max_time

      
        self.buildings = []
        self.detectar_edificios()

    def detectar_edificios(self):
        visitado = [[False for _ in fila] for fila in self.tiles]
        edificios = []

        for y in range(self.height):
            for x in range(self.width):
                if self.tiles[y][x] == "B" and not visitado[y][x]:
                    ancho = 0
                    alto = 0

                    
                    while x + ancho < self.width and self.tiles[y][x + ancho] == "B" and not visitado[y][x + ancho]:
                        ancho += 1

                   
                    while y + alto < self.height and all(
                        self.tiles[y + alto][x + dx] == "B" and not visitado[y + alto][x + dx]
                        for dx in range(ancho)
                    ):
                        alto += 1

                   
                    for dy in range(alto):
                        for dx in range(ancho):
                            visitado[y + dy][x + dx] = True

                    edificios.append({
                        "x": x,
                        "y": y,
                        "width": ancho,
                        "height": alto
                    })

        self.buildings = edificios
