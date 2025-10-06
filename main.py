import arcade
from courier.game import CourierQuestGame

class PantallaInicio(arcade.View):  # Pantalla de inicio del juego
    def __init__(self):
        super().__init__()
        self.fondo = arcade.load_texture("assets/inicio.png")  # Imagen de fondo

    def on_show(self):
        arcade.set_background_color(arcade.color.BLACK)

    def on_draw(self):
        self.clear()
        arcade.draw_lrwh_rectangle_textured(0, 0, self.window.width, self.window.height, self.fondo)

    def on_key_press(self, key, modifiers):  # Inicia el juego al presionar Enter
        if key == arcade.key.ENTER:
            juego = CourierQuestGame()
            self.window.show_view(juego)

class PantallaFinal(arcade.View):  # Pantalla que se muestra al finalizar el juego
    def __init__(self, dinero, completados, fallidos):
        super().__init__()
        self.dinero = dinero
        self.completados = completados
        self.fallidos = fallidos

    def on_show(self):
        arcade.set_background_color(arcade.color.BLACK)

    def on_draw(self):
        self.clear()
        arcade.draw_text("¡Juego terminado!", self.window.width // 2, self.window.height // 2 + 60,
                         arcade.color.YELLOW, 32, anchor_x="center")
        arcade.draw_text(f"Dinero ganado: ₡{self.dinero:.2f}", self.window.width // 2, self.window.height // 2 + 20,
                         arcade.color.WHITE, 20, anchor_x="center")
        arcade.draw_text(f"Pedidos completados: {self.completados}", self.window.width // 2, self.window.height // 2 - 10,
                         arcade.color.GREEN, 18, anchor_x="center")
        arcade.draw_text(f"Pedidos fallidos: {self.fallidos}", self.window.width // 2, self.window.height // 2 - 40,
                         arcade.color.RED, 18, anchor_x="center")
        arcade.draw_text("Presiona R para reiniciar", self.window.width // 2, self.window.height // 2 - 80,
                         arcade.color.LIGHT_GRAY, 16, anchor_x="center")

    def on_key_press(self, key, modifiers):
        if key == arcade.key.R:
            self.window.show_view(PantallaInicio())

if __name__ == "__main__":
    ventana = arcade.Window(800, 600, "Courier Quest", resizable=True)
    inicio = PantallaInicio()
    ventana.show_view(inicio)
    arcade.run()
