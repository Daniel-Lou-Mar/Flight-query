import os
import webbrowser
import flet as ft
import flet
from flet import (
    AppBar,
    Column,
    Row,
    Container,
    IconButton,
    Icon,
    NavigationRail,
    NavigationRailDestination,
    Page,
    Text,
    Card,
    Divider,
    PopupMenuButton,
    PopupMenuItem,
)
from flet import colors, icons
from functions import preguntar, guardar_configuracion, cargar_configuracion

class ConsultaVuelosApp(Row):
    def __init__(self, page,  *args,
        window_size=(400, 400),
        **kwargs,):
        super().__init__(*args, **kwargs)
        
        self.page = page
        self.page.title = "Consulta Vuelos"
        self.page.window.icon = r"Your icon path"
        
        # Conficuración de instrucciones
        self.config = cargar_configuracion()
        self.instrucciones_bool = self.config.get("mostrar_instrucciones", True)
        
        # Configuración de la página de consultas
        self.informe_entry = self.crear_campo_texto(label='Nombre del informe')
        self.estados_entry = self.crear_campo_texto(label='Estados (S-Salidas / L-Llegadas)')
        self.companias_entry = self.crear_campo_texto(label='Compañías')
        self.avion_entry = self.crear_campo_texto(label='Tipo de avión (ej: 320)')
        self.pais_entry = self.crear_campo_texto(label='País (ej: Spain)')
        self.dia_entry = self.crear_campo_texto(label='Día de la semana (ej: lunes)')
        self.inicio_entry = self.crear_campo_texto(label='Fecha de inicio (ej: 29JAN)')
        self.fin_entry = self.crear_campo_texto(label='Fecha de finalización (ej: 29JAN)')
        self.archivo_seleccionado = ft.Text('No se ha seleccionado archivo')
        self.page.theme = ft.Theme(font_family="Open Sans", use_material3=True)
        self.text_style = ft.TextStyle(
            font_family="Open Sans",
            size=15
        )

        # Elegir archivos
        self.ruta_archivo = None
        self.info_archivo = None
        self.file_picker = ft.FilePicker(on_result=self.file_picker_result)
        self.page.overlay.append(self.file_picker)
        
        # Vistas
        self.vista_consulta = self.crear_vista_consulta_vuelos()
        self.view_container = ft.AnimatedSwitcher(
            self.vista_consulta,
            transition=ft.AnimatedSwitcherTransition.FADE,
            duration=500,
            reverse_duration=100,
            switch_in_curve=ft.AnimationCurve.BOUNCE_OUT,
            expand=True)
        
        # Path consultas realizadas
        self.consultas_dir = os.path.join(os.getcwd(), "consultas_realizadas")
        os.makedirs(self.consultas_dir, exist_ok=True)

        
        # Configuración de la barra de navegación y menú
        self.navigation_bar = ft.NavigationBar(
            destinations=[
                ft.NavigationBarDestination(
                    icon=ft.icons.FLIGHT_TAKEOFF_OUTLINED,
                    selected_icon=ft.icons.FLIGHT_TAKEOFF,
                    label="Consulta de Vuelos"
                ),
                ft.NavigationBarDestination(
                    icon=ft.icons.HISTORY_OUTLINED,
                    selected_icon=ft.icons.HISTORY,
                    label="Consultas Realizadas"
                )
            ],
            on_change=self.cambiar_vista
        )
        self.menu = ft.PopupMenuButton(
            icon=ft.icons.QUESTION_MARK,
            items=[
                ft.PopupMenuItem(
                    text="Instrucciones",
                    icon=ft.icons.INFO_OUTLINED,
                    on_click=lambda e: self.vista_instrucciones()),
                ft.PopupMenuItem(
                    text="Créditos",
                    icon=ft.icons.CODE,
                    on_click=lambda e: page.open(self.vista_creditos())),
            ])
        
        self.es_inicio = True

    # Créditos
    def vista_creditos(self):
        return ft.AlertDialog(
            title=ft.Text("Créditos"),
            content=ft.Container(
                width=400,  # Ancho del diálogo
                height=115,  # Alto del diálogo
                padding=10,
                content=ft.Column([
                    ft.Text("Desarrollado por:", size=20),
                    ft.Text("Daniel Lou Marcial", size=18, weight=ft.FontWeight.BOLD),
                    ft.Row([
                        ft.Text("Github: ", size=18),
                        ft.TextButton(
                            "https://github.com/Daniel-Lou-M",
                            on_click=lambda e: webbrowser.open("https://github.com/Daniel-Lou-Mar"),
                            style=ft.ButtonStyle(
                                color=ft.colors.BLUE
                            ),
                        )
                    ]),
                ], spacing=10,),
            )
        )
    
    # Vista de consulta de vuelos
    def crear_vista_consulta_vuelos(self):
        return ft.Column([
            ft.Text("Consulta de Vuelos", style=ft.TextThemeStyle.HEADLINE_MEDIUM),
            self.informe_entry,
            self.estados_entry,
            self.companias_entry,
            self.avion_entry,
            self.pais_entry,
            self.dia_entry,
            self.inicio_entry,
            self.fin_entry,
            ft.Row([
                ft.ElevatedButton(text='Abrir archivo', on_click=self.abrir_archivo),
                ft.ElevatedButton(text='Realizar Consulta', on_click=self.realizar_consulta),
            ]),
            self.archivo_seleccionado
        ], spacing=10)

    def file_picker_result(self, e: ft.FilePickerResultEvent):
        if e.files:
            self.ruta_archivo = e.files[0].path
            self.archivo_seleccionado.value = f'Archivo seleccionado: {self.ruta_archivo}'
        else:
            self.archivo_seleccionado.value = 'No se ha seleccionado archivo'
        self.page.update()
    
    def abrir_archivo(self, e):
        self.file_picker.pick_files()

    # Realizar consulta vuelos
    def realizar_consulta(self, e):
        try:
            preguntar(
                self.ruta_archivo,
                self.informe_entry.value,
                self.avion_entry.value,
                self.estados_entry.value,
                self.companias_entry.value,
                self.pais_entry.value,
                self.dia_entry.value,
                self.inicio_entry.value,
                self.fin_entry.value
            )
            self.page.snack_bar = ft.SnackBar(ft.Text('Consulta realizada y archivo generado correctamente'))
        except Exception as ex:
            self.page.snack_bar = ft.SnackBar(ft.Text(f'Error: {ex}'))
        self.page.snack_bar.open = True
        
        if self.page.snack_bar not in self.page.overlay:
            self.page.overlay.append(self.page.snack_bar)
        self.page.update()

    # Vista de consultas realizadas
    def crear_vista_consultas_realizadas(self):
        archivos = [f for f in os.listdir(self.consultas_dir) if f.endswith('.xlsx')]
        listView = ft.ListView(expand=True, spacing=10, padding=20)
        if archivos:
            for archivo in archivos:
                archivo_txt = archivo.replace('.xlsx', '.txt')
                archivo_path_txt = os.path.join(self.consultas_dir, archivo_txt)
                with open(archivo_path_txt, 'r') as file:
                    contenido = []
                    for line_number, line in enumerate(file):
                        if line_number == 0:
                            fichero = os.path.basename(line.strip())
                            contenido.append(fichero)
                        else:
                            contenido.append(line.strip())

                detalles = "\n".join(contenido)
                details_container = ft.Container(
                    content=ft.Column([
                        ft.Text(f"Información de la consulta realizada:\n {detalles}"),
                        ft.ElevatedButton(
                            text="Abrir archivo XLSX",
                            on_click=lambda e, a=archivo: self.abrir_excel(a)
                        )
                    ], spacing=5),
                    visible=False
                )
                header = ft.Container(
                    content=ft.Row([
                        ft.Text(archivo, color=ft.colors.BLACK, expand=True),
                        ft.IconButton(
                            icon=ft.icons.KEYBOARD_ARROW_DOWN,
                            on_click=lambda e, dc=details_container: self.mostrar_detalles(dc)
                        )
                    ]),
                    bgcolor=ft.colors.BLUE_100,
                    padding=10
                )
                tile = ft.Column([header, details_container], spacing=5)
                listView.controls.append(tile)
            return ft.Column([
                ft.Text("Consultas Realizadas", style=ft.TextThemeStyle.HEADLINE_MEDIUM),
                listView
            ], spacing=10)
        else:
            return ft.Column([
                ft.Text("No hay consultas realizadas", style=ft.TextThemeStyle.HEADLINE_MEDIUM),
                listView
            ], spacing=10)

    def mostrar_detalles(self, detalles_container):
        detalles_container.visible = not detalles_container.visible
        self.page.update()

    def abrir_excel(self, nombre_archivo):
        ruta_archivo = os.path.join(self.consultas_dir, nombre_archivo)
        os.startfile(ruta_archivo)

    # Cambiar contenido de la vista
    def cambiar_contenido(self, contenido):
        self.view_container.content = contenido
        self.page.update()

    def cambiar_vista(self, e):
        if e.control.selected_index == 0:
            self.cambiar_contenido(self.vista_consulta)
        else:
            self.cambiar_contenido(self.crear_vista_consultas_realizadas())

    # Crear siempre el mismo campo de texto   
    def crear_campo_texto(self, label):
        return ft.TextField(
            label=label, border_color=ft.colors.SECONDARY,
            focused_border_color=ft.colors.PRIMARY_CONTAINER, text_style=ft.TextStyle(size=15)
        )

    # Se mostrarán las instrucciones
    def instrucciones_base(self):
        return ft.Column([
            ft.Row([
            ft.Icon(icons.INFO_OUTLINED, size=30, color=ft.colors.WHITE),
            ft.Text("Instrucciones", color=ft.colors.WHITE, size=22, weight=ft.FontWeight.BOLD),
            ], alignment=ft.MainAxisAlignment.CENTER),
            ft.Divider(color=ft.colors.BLACK),
            ft.Row(
            alignment=ft.MainAxisAlignment.CENTER,
            controls=[
                ft.Container(
                animate=ft.Animation(1000),
                width=300,
                height=500,
                border_radius=5,
                padding=10,
                expand=1,
                content=ft.Column([
                    ft.Text("1. Consulta de Vuelos", color=ft.colors.BLACK, size=18),
                    ft.Text("-Realiza una consulta de vuelos.", color=ft.colors.BLACK),
                    ft.Text("-El archivo seleccionado tiene que comenzar por 'S' o 'W' y los 2 últimos números del año.", color=ft.colors.BLACK),
                    ft.Text("-Únicamente los campos que son obligatorios son el nombre del informe y el rango de fecha.", color=ft.colors.BLACK),
                    ft.Text("-El resto de campos son opcionales.", color=ft.colors.BLACK),
                    ft.Text("-El nombre del informe es el nombre del archivo de salida.", color=ft.colors.BLACK),
                    ft.Text("-En las fechas hay que poner el el número del día del mes y las 3 primeras letras del mes en inglés.", color=ft.colors.BLACK),
                    ft.Text("-Se pueden poner varios días de la semana mientras estén separados por comas.", color=ft.colors.BLACK),
                    ft.Text("-Las aerolíneas se tienen que poner como en la base de datos, ejemplo IB -> Iberia.", color=ft.colors.BLACK),
                    ft.Text("-El tipo de avión se tiene que poner como en la base de datos, ejemplo 320 -> A320.", color=ft.colors.BLACK),
                    ft.Text("-El país se tiene que poner en inglés.", color=ft.colors.BLACK),
                    ft.Text("""-Una vez escrito todos los parámetros deseados hay que pulsar al botón de realizar consulta y se generará un informe en formato .xlsx en el caso de que haya coincidencias con su consulta. Para abrir el informe tendrá que ir a la página de consultas realizadas.""", color=ft.colors.BLACK),
                ]),
                bgcolor=ft.colors.BLUE_50,
                ),
                ft.VerticalDivider(width=9, thickness=3),
                ft.Container(
                animate=ft.Animation(1000),
                width=300,
                height=500,
                border_radius=5,
                padding=10,
                expand=1,
                content=ft.Column([
                    ft.Text("2. Consultas realizadas", color=ft.colors.BLACK),
                    ft.Text("-En esta sección se pueden ver todas las consultas realizadas.", color=ft.colors.BLACK),
                    ft.Text("-Todas las consultas realizadas se han guardado con sus respectivas condiciones.", color=ft.colors.BLACK),
                    ft.Text("-Al pulsar en cada desplegable de cada archivo se podrá ver la información de la consulta y abrir el archivo excel.", color=ft.colors.BLACK),
                ]),
                bgcolor=ft.colors.RED_100
                ),
            ],
            ),
            ])

    # Mostrar instrucciones
    def instrucciones(self):
        if self.es_inicio == False:
            return ft.Column([
                self.instrucciones_base(),
                ft.Container(expand=True, height=10),
                ft.Row([
                    ft.ElevatedButton(
                    text="Cerrar",
                    on_click=lambda e: self.vista_normal(),
                    width=115,
                    height=65,
                    )
                ], spacing=10, alignment=ft.MainAxisAlignment.CENTER, expand=True)])
        else:
            self.es_inicio = False
            return ft.Column([
                self.instrucciones_base(),
                ft.Container(expand=True, height=10),
                ft.Row([
                ft.Checkbox(label="No volver a mostrar instrucciones al inicio", value=not self.instrucciones_bool, on_change=lambda e: self.actualizar_preferencia_instrucciones(e)),
                ],
                spacing=10, alignment=ft.MainAxisAlignment.CENTER, expand=True),
                ft.Row([
                    ft.ElevatedButton(
                    text="Cerrar",
                    on_click=lambda e: self.vista_normal(),
                    width=115,
                    height=65,
                    )
                ], spacing=10, alignment=ft.MainAxisAlignment.CENTER, expand=True)])

        # Vista con instrucciones
    
    def vista_instrucciones(self):
        self.page.controls.clear()
        self.page.controls.append(self.instrucciones())
        self.page.update()
    
    # Cambio de preferencia de instrucciones al inicio
    def actualizar_preferencia_instrucciones(self, e):
        self.instrucciones_bool = not e.control.value
        self.config["mostrar_instrucciones"] = self.instrucciones_bool
        guardar_configuracion(self.config)

    # Vista sin instrucciones
    def vista_normal(self):
        self.page.controls.clear()
        self.page.controls.append( ft.Column([
            ft.Row(
                controls=[
                    ft.Container(expand=True),  # Espaciador para alinear el menú a la derecha
                    self.menu
                ],
                alignment=ft.MainAxisAlignment.END,
                vertical_alignment=ft.CrossAxisAlignment.START
            ),
            self.view_container,
            ft.Divider(),
            self.navigation_bar,
        ], expand=True))
        self.page.update()
    
    
    # Primera pantalla app
    def build(self):
        if self.instrucciones_bool:
            return ft.Column([
                self.instrucciones(),
            ])
        else:
            self.es_inicio = False
            return ft.Column([
            ft.Row(
                controls=[
                    ft.Container(expand=True),  # Espaciador para alinear el menú a la derecha
                    self.menu
                ],
                alignment=ft.MainAxisAlignment.END,
                vertical_alignment=ft.CrossAxisAlignment.START
            ),
            self.view_container,
            ft.Divider(),
            self.navigation_bar,
        ], expand=True)
