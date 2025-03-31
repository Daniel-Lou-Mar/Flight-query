import sys
import os
import sqlite3
import datetime
import pandas as pd
import re
from errors import VanessaLovesDani
import pycountry
from airportsdata import load
from concurrent.futures import ThreadPoolExecutor
from tkinter import messagebox
import json

# Cargamos la base de datos de aeropuertos
airports_IATA = load('IATA')

###########################################################################
#################################FUNCIONES#################################
###########################################################################

##Funcion para guardar configuracion de la aplicacion en un json###
# Ruta del archivo de configuración
CONFIG_FILE = "config.json"

def cargar_configuracion():
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "w") as file:
            json.dump({"mostrar_instrucciones": True}, file)  # Crear con valor predeterminado
    with open(CONFIG_FILE, "r") as file:
        return json.load(file)

def guardar_configuracion(config):
    with open(CONFIG_FILE, "w") as file:
        json.dump(config, file)
        
################################################################

###Funcion para transformar la fecha a formato ISO###

def fecha_iso(fichero, fecha):
    
    # Sacamos nombre arhivo a partir de su ruta para averiguar si es S o W
    fichero = os.path.basename(fichero)

    match = re.match(r"([SWsw])(\d{2})", fichero.strip())
    if not match:
        raise VanessaLovesDani("El archivo no tiene el formato de nombre correcto.")
    fichero = match.groups()
    
    fecha = fecha.upper()
    match = re.match(r"(\d{1,2})([A-Z]{3})", fecha.strip())
    try:
        dia, mes_abrev = match.groups()
        mes = datetime.datetime.strptime(mes_abrev, "%b").month
        año_fiche = fichero[1]
        if fichero[0].upper() == "W":
            año = "20" + año_fiche if mes in [10, 11, 12] else "20" + str(int(año_fiche) + 1) 
        elif fichero[0].upper() == "S":
            año = "20" + año_fiche
        fecha_iso = datetime.datetime.strptime(f"{dia}{mes_abrev}{año}", "%d%b%Y").strftime("%Y-%m-%d")
        return fecha_iso
    except:
        raise VanessaLovesDani("La fecha no tiene el formato correcto.")

###Funcion para procesar las lineas del archivo###

def procesar_linea(linea, fichero, index):
    try:
        # DEFINIMOS VARIABLES PARA INSERTAR EN LA BASE DE DATOS
        est, apto, estad, comp, num, h_llegada, h_salida, lun, mart, mierc, juev, vier, sab, dom, ini, fin, codigo, n_pasajeros, avion = (
            linea[1], linea[7:10], linea[13], linea[17:20], linea[20:24], linea[26:30], linea[30:34], 
            linea[35], linea[36], linea[37], linea[38], linea[39], linea[40], linea[41], 
            linea[43:48], linea[48:53], linea[66:69], linea[204:207], linea[210:213]
        )
        # Convertir fechas del vuelo a formato ISO
        fecha_ini_db = fecha_iso(fichero, ini)
        fecha_fin_db = fecha_iso(fichero, fin)

        # OBTENEMOS EL PAÍS DEL AEROPUERTO
        codigos = pais_aeropuerto(codigo, index)
        
        # Retornar los valores procesados
        return (est, apto, estad, comp, num, h_llegada, h_salida, lun, mart, mierc, juev, vier, sab, dom, 
                fecha_ini_db, fecha_fin_db, codigos[1], codigos[0], codigos[2], n_pasajeros, avion)
    except:
        raise VanessaLovesDani(f"Error procesando la línea {index + 1}. El contenido del archivo no tiene el formato correcto.")

###Funcion para obtener el codigo ICAO, país y ciudad del aeropuerto###

def pais_aeropuerto(codigo,linea):
    try:
        if codigo == "ZZZ":
            return ["ZZZ", "ZZZZ", "ZZZZ"]
        país = pycountry.countries.get(alpha_2=airports_IATA[codigo]['country'])
        ICAO = airports_IATA[codigo]['icao']
        ciudad = airports_IATA[codigo]['city']
        return (país.name, ICAO, ciudad)
    except:
        messagebox.showerror("Error", f"El código de aeropuerto en la línea {linea + 1} no se encuentra en la base de datos, no se tomó en cuenta.")
        return ["ZZZ", "ZZZZ", "ZZZZ"]

###Funcion para obtener la ruta del archivo sql###

def obtener_ruta_archivo(nombre_archivo):
    if getattr(sys, 'frozen', False):  # Si se está ejecutando como ejecutable
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, nombre_archivo)

ruta_sql = obtener_ruta_archivo("base_datos_flights.sql")

###Funcion para guardar la consulta realizada en un archivo de texto###

def info_consulta(fichero, nombre_informe, avion, estados, compañías, pais, dia, fecha_inicio, fecha_fin):
    # Modificar la ruta para que el informe de texto se guarde en la carpeta
    with open(f"consultas_realizadas/{nombre_informe}.txt", "w") as f:
        f.write(f"Fichero: {fichero}\n")
        if avion:
            f.write(f"Avión: {avion}\n")
        if estados:
            f.write(f"Estados: {estados}\n")
        if compañías:
            f.write(f"Compañías: {compañías}\n")
        if pais:
            f.write(f"País: {pais}\n")
        if dia:
            f.write(f"Día: {dia}\n")
        f.write(f"Fecha Inicio: {fecha_inicio}\n")
        f.write(f"Fecha Fin: {fecha_fin}\n")


############################################################################
##############################CÓDIGO PRINCIPAL##############################
############################################################################

###Funcion para preguntar al usuario y realizar la consulta###

def preguntar(fichero, nombre_informe, avion, estados, compañías, pais, dia_ini, fecha_inicio, fecha_fin):
    if not fichero:
        raise VanessaLovesDani("Debes seleccionar un archivo.")
    if not nombre_informe:
        raise VanessaLovesDani("El nombre del informe es obligatorio.")
    if pais and not pycountry.countries.get(name=pais):
        raise VanessaLovesDani("El país no es válido.")
    if estados and estados.upper() not in ["S", "L"]:
        raise VanessaLovesDani("El estado no es válido.")
    if not fecha_inicio or not fecha_fin:
        raise VanessaLovesDani("Escribe un rango de fechas.")
        
    # Convertir fechas de entrada del usuario a formato ISO para filtrado
    fecha_ini_usuario = fecha_iso(fichero, fecha_inicio)
    fecha_fin_usuario = fecha_iso(fichero, fecha_fin)

    
    # CONECTAMOS BASE DE DATOS Y LEEMOS FICHERO RECIBIDO
    with sqlite3.connect(f"{ruta_sql}") as db, open(fichero, "r") as fr:
        cursor = db.cursor()
        valores_a_insertar = []
        
        with ThreadPoolExecutor() as executor:
            lineas = list(fr)
            resultados = list(executor.map(lambda args: procesar_linea(*args), 
                                           [(linea, fichero, index) for index, linea in enumerate(lineas)]))
            valores_a_insertar.extend(resultados)
        
        try:
            # INSERTAMOS LOS VALORES EN LA BASE DE DATOS
            cursor.executemany('''
                                INSERT INTO vuelos VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                ''', valores_a_insertar)
        except:
            raise VanessaLovesDani("El contenido del archivo no tiene el formato correcto.")
        
        # Manejar los filtros de la consulta
        pais = pais.strip().lower() if pais else ""
        estados = estados.strip().upper() if estados else ""
        lista = [avion, estados, compañías, pais]
        lista_final = [indice for indice, valor in enumerate(lista) if valor != ""]
        dias_diccionario = {"lunes": "1",
                            "martes": "2",
                            "miercoles": "3",
                            "jueves": "4", 
                            "viernes": "5",
                            "sabado": "6",
                            "domingo": "7"} # DICCIONARIO PARA CAMBIAR EL DÍA POR SU VALOR EN LA BASE DE DATOS
        diccionario = {0: f"LOWER(TRIM(avion)) = '{avion.strip().lower()}'",
                       1: f"estado = '{estados}'",
                       2: f"LOWER(TRIM(compa)) = '{compañías.strip().lower()}'",
                       3: f"LOWER(Pais) = '{pais}'"} # DICCIONARIO PARA PODER PASAR A CODIGO SQL LOS VALORES DE LA CONSULTA
        filtros = [diccionario[i] for i in lista_final]
        
        # Calcular la semana pico de afluencia del mes dentro del rango de fechas del usuario
        sql = f"""
            SELECT lunes, martes, miercoles, jueves, viernes, sabado, domingo, 
                DATE(inicio), DATE(final), estado, compa, n_vuelo, h_llegada, h_salida, Codigo_OACI, Pais, Ciudad, n_pasajeros, avion
            FROM vuelos 
            WHERE inicio <= DATE(?) 
            AND final >= DATE(?)"""
        if filtros:
            sql += f" AND {' AND '.join(filtros)}"
        if dia_ini:
            dia_lista = dia_ini.split(",")
            dia_validos = []
            for d in dia_lista:
                d_lower = d.strip().lower()
                if d_lower in dias_diccionario:
                    dia_validos.append(d_lower)
                else:
                    raise VanessaLovesDani(f"El día {d} no es válido.")
            
            valor_dia = [f"{d} = {dias_diccionario[d]}" for d in dia_validos] # Cambiamos el dia para que se pueda escribir en la base de datos la consulta
            sql += f" AND ({' OR '.join(valor_dia)})"

        cursor.execute(sql, (fecha_fin_usuario, fecha_ini_usuario))
        vuelos = cursor.fetchall()
        
        # Calcular la semana y día pico de afluencia del mes dentro del rango de fechas del usuario
        conteo_pico_dia = -1
        dia_actual = datetime.datetime.strptime(fecha_ini_usuario, "%Y-%m-%d")
        conteo = {}
        conteo2 = {}
        paises_pasajeros = {}

        while dia_actual <= datetime.datetime.strptime(fecha_fin_usuario, "%Y-%m-%d"):
            semana_actual = dia_actual.strftime("%Y-%W")
            conteo_dia = 0
            lista_datos_dia = []
            for vuelo in vuelos:
                weekday = dia_actual.weekday()
                vuelo_lunes, vuelo_martes, vuelo_miercoles, vuelo_jueves, vuelo_viernes, vuelo_sabado, vuelo_domingo, vuelo_in, vuelo_fin, vuelo_estado, vuelo_compañía, n_vuelo, vuelo_llegada, vuelo_salida, oaci, vuelo_pais, ciudad, pasajeros, vuelo_avion = vuelo
                dias = {vuelo_lunes: "Lunes", vuelo_martes: "Martes", vuelo_miercoles: "Miércoles", vuelo_jueves: "Jueves", vuelo_viernes: "Viernes", vuelo_sabado: "Sábado", vuelo_domingo: "Domingo"}
                dias_final = [valor  for dia, valor in dias.items() if dia != 0]
                if vuelo_in <= dia_actual.strftime("%Y-%m-%d") <= vuelo_fin:
                    if weekday == 0 and vuelo_lunes.strip() == '1' and (not dia_ini or any((int(dias_diccionario[d.strip().lower()]) - 1) == weekday for d in dia_lista)):  # Lunes
                        conteo_dia += 1
                        lista_datos_dia.append((vuelo_estado, vuelo_compañía, n_vuelo, vuelo_avion, vuelo_llegada, vuelo_salida, ", ".join(dias_final), vuelo_in, vuelo_fin, oaci, vuelo_pais, ciudad))
                    elif weekday == 1 and vuelo_martes.strip() == '2' and (not dia_ini or any((int(dias_diccionario[d.strip().lower()]) - 1) == weekday for d in dia_lista)):  # Martes
                        conteo_dia += 1
                        lista_datos_dia.append((vuelo_estado, vuelo_compañía, n_vuelo, vuelo_avion, vuelo_llegada, vuelo_salida, ", ".join(dias_final), vuelo_in, vuelo_fin, oaci, vuelo_pais, ciudad))
                    elif weekday == 2 and vuelo_miercoles.strip() == '3' and (not dia_ini or any((int(dias_diccionario[d.strip().lower()]) - 1) == weekday for d in dia_lista)):  # Miércoles
                        conteo_dia += 1
                        lista_datos_dia.append((vuelo_estado, vuelo_compañía, n_vuelo, vuelo_avion, vuelo_llegada, vuelo_salida, ", ".join(dias_final), vuelo_in, vuelo_fin, oaci, vuelo_pais, ciudad))
                    elif weekday == 3 and vuelo_jueves.strip() == '4' and (not dia_ini or any((int(dias_diccionario[d.strip().lower()]) - 1) == weekday for d in dia_lista)):  # Jueves
                        conteo_dia += 1
                        lista_datos_dia.append((vuelo_estado, vuelo_compañía, n_vuelo, vuelo_avion, vuelo_llegada, vuelo_salida, ", ".join(dias_final), vuelo_in, vuelo_fin, oaci, vuelo_pais, ciudad))
                    elif weekday == 4 and vuelo_viernes.strip() == '5' and (not dia_ini or any((int(dias_diccionario[d.strip().lower()]) - 1) == weekday for d in dia_lista)):  # Viernes
                        conteo_dia += 1
                        lista_datos_dia.append((vuelo_estado, vuelo_compañía, n_vuelo, vuelo_avion, vuelo_llegada, vuelo_salida, ", ".join(dias_final), vuelo_in, vuelo_fin, oaci, vuelo_pais, ciudad))
                    elif weekday == 5 and vuelo_sabado.strip() == '6' and (not dia_ini or any((int(dias_diccionario[d.strip().lower()]) - 1) == weekday for d in dia_lista)):  # Sábado
                        conteo_dia += 1
                        lista_datos_dia.append((vuelo_estado, vuelo_compañía, n_vuelo, vuelo_avion, vuelo_llegada, vuelo_salida, ", ".join(dias_final), vuelo_in, vuelo_fin, oaci, vuelo_pais, ciudad))
                    elif weekday == 6 and vuelo_domingo.strip() == '7' and (not dia_ini or any((int(dias_diccionario[d.strip().lower()]) - 1) == weekday for d in dia_lista)):  # Domingo
                        conteo_dia += 1
                        lista_datos_dia.append((vuelo_estado, vuelo_compañía, n_vuelo, vuelo_avion, vuelo_llegada, vuelo_salida, ", ".join(dias_final), vuelo_in, vuelo_fin, oaci, vuelo_pais, ciudad))
                    
                    if vuelo_pais not in paises_pasajeros:
                        paises_pasajeros[vuelo_pais] = pasajeros
                    paises_pasajeros[vuelo_pais] += pasajeros

            # Acumulamos los datos en la semana correspondiente
            if semana_actual not in conteo:
                conteo[semana_actual] = [0, []]
            conteo[semana_actual][0] += conteo_dia
            conteo[semana_actual][1].extend(lista_datos_dia)
                
            if conteo_dia > conteo_pico_dia:
                conteo_pico_dia = conteo_dia
                conteo2.clear()
                conteo2[dia_actual.strftime("%Y-%m-%d")] = [conteo_dia, lista_datos_dia]
            elif conteo_dia == conteo_pico_dia:
                conteo2[dia_actual.strftime("%Y-%m-%d")] = [conteo_dia, lista_datos_dia]

            dia_actual += datetime.timedelta(days=1)

        
        # Determinamos la semana pico recorriendo el diccionario
        conteo_pico_semana = -1
        conteo_final = {}
        for sem, (conteo_sem, datos_sem) in conteo.items():
            if conteo_sem > conteo_pico_semana:
                conteo_pico_semana = conteo_sem
                conteo_final.clear()
                conteo_final[sem] = [conteo_sem, datos_sem]
            elif conteo_sem == conteo_pico_semana:
                conteo_final[sem] = [conteo_sem, datos_sem]
        
        # Determinamos paises con más pasajeros
        paises_pasajeros = dict(sorted(paises_pasajeros.items(), key=lambda x: x[1], reverse=True)[:10])
        

        # Escribir el informe
        if conteo_pico_dia > 0:
            # Crear carpeta 'consultas_realizadas' si no existe
            os.makedirs("consultas_realizadas", exist_ok=True)
            # Modificar la ruta para que el archivo Excel se guarde en la carpeta
            with pd.ExcelWriter(f'consultas_realizadas/{nombre_informe}.xlsx') as writer:
                
                for dia, datos in conteo2.items():
                    df = pd.DataFrame(datos[1], columns=["Estado", "Compañía", "Número de vuelo", "Tipo Avión", "Hora de llegada", "Hora de salida", "Días", "Inicio", "Final", "Código OACI", "País", "Ciudad"])
                    df.to_excel(writer, sheet_name=f"Día {dia}, {datos[0]}", index=False) #El normbre de la hoja será "Dia {número de dia}, {conteo de vuelos}"
                    worksheet = writer.sheets[f"Día {dia}, {datos[0]}"]
                    # Ajustar el ancho de las columnas
                    worksheet.column_dimensions['A'].width = 20 
                    worksheet.column_dimensions['B'].width = 20
                    worksheet.column_dimensions['C'].width = 20
                    worksheet.column_dimensions['D'].width = 20
                    worksheet.column_dimensions['E'].width = 20
                    worksheet.column_dimensions['F'].width = 20
                    worksheet.column_dimensions['G'].width = 54
                    worksheet.column_dimensions['H'].width = 20
                    worksheet.column_dimensions['I'].width = 20
                    worksheet.column_dimensions['J'].width = 20
                    worksheet.column_dimensions['K'].width = 20
                    worksheet.column_dimensions['L'].width = 20

                
                for semana, datos in conteo_final.items():
                    df = pd.DataFrame(datos[1], columns=["Estado", "Compañía", "Número de vuelo", "Tipo Avión", "Hora de llegada", "Hora de salida", "Días", "Inicio", "Final", "Código OACI", "País", "Ciudad"])
                    df.to_excel(writer, sheet_name=f"Semana {semana}, {datos[0]}", index=False) #El normbre de la hoja será "Semana {número de semana}, {conteo de vuelos}"
                    worksheet = writer.sheets[f"Semana {semana}, {datos[0]}"]
                    # Ajustar el ancho de las columnas
                    worksheet.column_dimensions['A'].width = 20 
                    worksheet.column_dimensions['B'].width = 20
                    worksheet.column_dimensions['C'].width = 20
                    worksheet.column_dimensions['D'].width = 20
                    worksheet.column_dimensions['E'].width = 20
                    worksheet.column_dimensions['F'].width = 20
                    worksheet.column_dimensions['G'].width = 54
                    worksheet.column_dimensions['H'].width = 20
                    worksheet.column_dimensions['I'].width = 20
                    worksheet.column_dimensions['J'].width = 20
                    worksheet.column_dimensions['K'].width = 20
                    worksheet.column_dimensions['L'].width = 20

                
                df = pd.DataFrame(list(paises_pasajeros.items()), columns=["País", "Número de pasajeros"])
                df.to_excel(writer, sheet_name=f"Paises con más pasajeros", index=False)
                worksheet = writer.sheets[f"Paises con más pasajeros"]
                # Ajustar el ancho de las columnas
                worksheet.column_dimensions['A'].width = 20 
                worksheet.column_dimensions['B'].width = 20
            info_consulta(fichero, nombre_informe, avion, estados, compañías, pais, dia_ini, fecha_inicio, fecha_fin)
        else:
            raise VanessaLovesDani("No hay vuelos que coincidan con tu consulta en el rango de fechas proporcionado.")
            
        # Vaciar base de datos
        cursor.execute("DELETE FROM vuelos")
