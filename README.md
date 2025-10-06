Se utilizaron estructuras datos lineales como list y tuple, un ejemplo del uso de List es en  
List[Job] en CourierQuestGame ya que aquí se usan listas para guardar los distintos estados de los trabajos del jugador:

jobs: todos los trabajos posibles.

active_jobs: los que están disponibles actualmente.

completed: los ya entregados.

failed: los que se perdieron o vencieron.

Justificación:

Las listas son ideales porque, el orden de llegada y liberación de trabajos es importante, Se necesita agregar y eliminar trabajos de forma secuencial, No se requiere búsqueda compleja por clave (como en un diccionario), por lo que la lista es suficiente.

Complejidad:

Agregar trabajo (append) → O(1)

Eliminar vencidos (recorriendo) → O(n)

Buscar o recorrer para actualizar → O(n)

y un ejemplo del Tuple es en  Tuple[int, int] en Job.pickup y Job.dropoff

Asi se ve en el codigo 
pickup: Tuple[int, int]
dropoff: Tuple[int, int]

y cada trabajo gurda sus coordenadas de recolección y entrega como tuplas (x,y)

Justificación:

La tupla es inmutable, liviana y perfecta para representar un par de valores que no cambiarán, También facilita comparar posiciones o acceder por índice (pos[0], pos[1]).

Complejidad:

Acceso a una coordenada → O(1)

Comparación de tuplas → O(1) (ya que solo hay dos elementos).
