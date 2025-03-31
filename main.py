import flet as ft
from interface import ConsultaVuelosApp

def main(page: ft.Page):
    page.title = 'Consulta de Vuelos'
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.window.width = 700
    page.window.height = 800

    app = ConsultaVuelosApp(page)
    page.add(app.build())
    page.update()

if __name__ == "__main__":
    ft.app(target=main)
