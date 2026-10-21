"""
Autor: Arana Hernandez Yamileth 
Fecha de termino : 19/10/2026
Descripcion : Este programa permite consultar informacion economica publicado
por el banco de Mexico (Banxico) calcular intereses financieros y convertir cantidades 
entre pesos mexicanos y monedas extranjeras .Los reportes de los calculos se guardan en archivos 
de texto (.txt) y puden enviarse por correo electronico mediante Gmail.
Objetivo generar: Desarroyar un programa de Python que integre informacion economica
de Banxico con operaciones basicas de matematicas financieras, automatizando los calculos y elaboracion
de reportes.
"""
import os
import smtplib
import requests
from datetime import datetime
from email.message import EmailMessage
from dotenv import load_dotenv
import time

load_dotenv()
TOKEN_BANXICO = os.getenv("TOKEN_BANXICO", "").strip()
SERIE_CETES = os.getenv("SERIE_CETES", "SF60633").strip()
SERIE_USD = os.getenv("SERIE_USD","SF43718").strip()
SERIE_EUR = os.getenv("SERIE_EUR", "SF46410").strip()
SERIE_GBP = os.getenv("SERIE_GBP", "SF46407").strip()
HOSTMAIL = os.getenv("HOSTMAIL","smtp.gmail.com").strip()
USERMAIL = os.getenv("USERMAIL","").strip()
PASSWORD = os.getenv("PASSWORD", "").strip()
try:
    PORTMAIL = int(os.getenv("PORTMAIL","587"))
except ValueError:
    PORTMAIL = 587

URL_BANXICO = "https://www.banxico.org.mx/SieAPIRest/service/v1/series/"
BASE_DIAS = 365
TIEMPO_ESPERA = 15
def consultar_serie(id_serie):
    """
    Consulta el dato más reciente disponible de una serie de Banxico.
    """
    if not TOKEN_BANXICO or TOKEN_BANXICO == "PEGA_AQUI_TU_TOKEN":
        print("Error: configura tu token de Banxico en el archivo .env.")
        return None
    id_serie = id_serie.strip()
    if not id_serie:
        print("Error: el identificador no puede estar vacío.")
        return None
    url = f"{URL_BANXICO}{id_serie}/datos/oportuno"
    encabezados = {"Bmx-Token": TOKEN_BANXICO,"Accept": "application/json"}
    try:
        respuesta = requests.get(url,headers=encabezados,timeout=TIEMPO_ESPERA)
        if respuesta.status_code != 200:
            print(f"Error HTTP {respuesta.status_code} " "al consultar Banxico.")
            print("URL consultada:", respuesta.url)
            print("Detalle:", respuesta.text[:1000])
            return None
        contenido = respuesta.json()
        series = contenido["bmx"]["series"]
        if not series or not series[0].get("datos"):
            print("La serie no tiene datos disponibles.")
            return None
        dato = series[0]["datos"][0]
        valor_texto = dato["dato"].strip().replace(",", "")
        if valor_texto.upper() in ("N/E", "N/D", "NA", ""):
            print("El dato más reciente no es numérico.")
            return None
        valor = float(valor_texto)
        return {"serie": id_serie, "nombre": series[0].get("titulo", "Sin título"),"fecha": dato.get("fecha", "Sin fecha"),"valor": valor}
    except requests.exceptions.Timeout:
        print("Error se agotó el tiempo espera a la conexión con Banxico.")
    except requests.exceptions.ConnectionError:
        print("No se pudo establecer conexión con Banxico.")
    except requests.exceptions.RequestException as error:
        print(f"Error en la solicitud: {error}")
    except (ValueError, KeyError, IndexError, TypeError) as error:
        print(f"Error al procesar la respuesta de Banxico: {error}")
    return None


def pedir_numero(mensaje, minimo=0):
    """
    Solicita un número válido y comprueba su valor mínimo sirve para las opciones lo hace mas facil y ordenado te ahorras texto
    """
    while True:
        try:
            numero = float(input(mensaje).strip())
            if numero != numero or abs(numero) == float("inf"):
                print("Error: introduce un número finito.")
                continue
            if numero < minimo:
                print(f"Error: el número debe ser mayor o igual a {minimo}.")
                continue
            return numero
        except ValueError:
            print("Favor de introducir un número válido.")

def validar_correo(correo):
    """
    Comprueba que el correo contenga una arroba y un punto en el dominio para que sea un correo valido
    """
    return (correo.count("@") == 1 and " " not in correo and "." in correo.split("@")[-1])

def generar_informe(titulo, datos):
    """
    Construye un informe con fecha y datos calculados para enviar al correo electronico
    son los datos que debe de tener para ser valido y llevar un registro de consultas
    """
    lineas = ["=" * 50,titulo,"=" * 50,f"Fecha de generación: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",""]
    lineas.extend(datos)
    lineas.extend(["","Informe generado por el Sistema Financiero con Banxico."])
    return "\n".join(lineas)

def guardar_reporte(nombre_archivo, contenido):
    """
    Guarda el informe en un archivo de texto para ser enviado al servidor que solicite la informacion.
    """
    try:
        with open(nombre_archivo, "w", encoding="utf-8") as archivo:
            archivo.write(contenido)
        print(f"Informe se ha guardado en: {nombre_archivo}")
        return True
    except OSError as error:
        print(f"No se pudo guardar el informe por favor intentelo de nuevo: {error}")
        return False


def enviar_email(asunto, contenido):
    """
    Envía el informe en el cuerpo del correo como texto plano para ser leido por el servidor.
    """
    if not USERMAIL or not PASSWORD:
        print("Configura USERMAIL y PASSWORD en el archivo .env.")
        print("No se envió el correo asi que verifique o intentelo de nuevo.")
        return False
    if not HOSTMAIL or PORTMAIL <= 0:
        print("Error: revisa HOSTMAIL y PORTMAIL en el archivo .env. al parecer son incorrectos")
        return False
    while True:
        destinatario = input("Escribe el correo del destinatario por favor recuerda que debe llevar un @ y un (.) para ser valido: ").strip()
        if validar_correo(destinatario):
            break
        print("Error: introduce una dirección de correo válida como la ya mencionada.")
    mensaje = EmailMessage()
    mensaje["From"] = USERMAIL
    mensaje["To"] = destinatario
    mensaje["Subject"] = asunto
    mensaje.set_content(contenido)
    try:
        with smtplib.SMTP( HOSTMAIL,PORTMAIL,timeout=20) as servidor:
            servidor.ehlo()
            servidor.starttls()
            servidor.ehlo()
            servidor.login(USERMAIL, PASSWORD)
            servidor.send_message(mensaje)
        print("El servidor aceptó el correo para su envío asi que compruebe en la bandeja de entrada o en la carpeta de spam.")
        return True
    except smtplib.SMTPAuthenticationError:
        print("Error de autenticación revisa tus credenciales de correo porque estan incorrectas")
    except smtplib.SMTPRecipientsRefused:
        print("El servidor rechazó al destinatario asi que checa el correo escrito.")
    except smtplib.SMTPConnectError:
        print("No se pudo conectar al servidor de correo intentalo de nuevo.")
    except (smtplib.SMTPException, OSError) as error:
        print(f"Error al enviar el correo intentalo otra vez: {error}")
    return False

def entregar_informe(nombre_archivo, asunto, contenido):
    """
    Guarda el informe e intenta enviarlo por correo al destinario de manera correcta y bien hecha aqui nadamas es poner las
    funciones ya hechas anteriormente
    """
    guardar_reporte(nombre_archivo, contenido)
    enviar_email(asunto, contenido)

def consultar_serie_usuario():
    """
    Consulta una serie y muestra los datos estas no llevan informe debido a eso
    este no fue creado aqui nadamas es checar datos y eso y que te devuelva el titulo y el valor
    """
    print("\nCONSULTA DE SERIES DE BANXICO")
    print("Escribe el identificador de la serie que deseas consultar. Ejemplo: SF60633")
    id_serie = input("Identificador de la serie (es la serie que consultas en Banxico): ").strip()
    if not id_serie:
        print("Error: debes escribir un identificador.")
        return
    resultado = consultar_serie(id_serie)
    if resultado is None:
        print("No fue posible obtener los datos de esa serie , verifica el identificador e inténtalo nuevamente.")
        return
    print("\nDATOS OBTENIDOS DE BANXICO")
    print(f"Identificador: {resultado['serie']}")
    print(f"Nombre de la serie: {resultado['nombre']}")
    print(f"Fecha del dato: {resultado['fecha']}")
    print(f"Valor: {resultado['valor']:.6f}")
    print("\nConsulta realizada correctamente.")

def calcular_interes():
    """
    Calcula interés simple o compuesto con la tasa consultada en los CETES recordando que este valor solo
    es de 28 dias ademas de estructura de informe
    """
    print("\nCÁLCULO DE INTERESES CON CETES")
    print("1. Interés simple")
    print("2. Interés compuesto")
    tipo = input("Selecciona el tipo de interés: ").strip()
    if tipo not in ("1", "2"):
        print("Opción no válida.")
        return
    capital = pedir_numero("Capital inicial: ", minimo=0.000001)
    dias = pedir_numero("Número de días: ", minimo=0)
    if dias == 0:
        print("El número de días debe ser mayor que cero.")
        return
    cetes = consultar_serie(SERIE_CETES)
    if cetes is None:
        print("No se pudo obtener la tasa de CETES intentelo de nuevo.")
        return
    tasa = cetes["valor"]
    if tasa <= 0 or tasa >= 100:
        print("La tasa obtenida no parece válida verifica la serie.")
        return
    tasa_decimal = tasa / 100
    tiempo = dias / BASE_DIAS
    if tipo == "1":
        interes = capital * tasa_decimal * tiempo
        monto_final = capital + interes
        nombre_tipo = "Interés simple"
    else:
        monto_final = capital * (1 + tasa_decimal) ** tiempo
        interes = monto_final - capital
        nombre_tipo = "Interés compuesto"
    print("\nRESULTADO DEL CÁLCULO")
    print(f"Nombre de la serie: {cetes['nombre']}")
    print(f"Fecha de la tasa: {cetes['fecha']}")
    print(f"Tasa anual consultada: {tasa:.6f}%")
    print(f"Tipo de interés: {nombre_tipo}")
    print(f"Capital inicial: ${capital:,.2f} MXN")
    print(f"Tiempo: {dias:g} días")
    print(f"Interés calculado: ${interes:,.2f} MXN")
    print(f"Monto final: ${monto_final:,.2f} MXN")
    informe = generar_informe("INFORME DE CÁLCULO DE INTERESES",[ f"Serie: {cetes['serie']}",f"Nombre de la serie: {cetes['nombre']}",
                                                                   f"Fecha de la tasa: {cetes['fecha']}", f"Tasa anual: {tasa:.6f}%",
                                                                    f"Tipo de interés: {nombre_tipo}",f"Capital inicial: ${capital:,.2f} MXN",
                                                                   f"Tiempo: {dias:g} días" ,f"Interés calculado: ${interes:,.2f} MXN",
                                                                   f"Monto final: ${monto_final:,.2f} MX", "", "Interés simple: I = C * r * t",
                                                                 "Monto compuesto: M = C * (1 + r) ** t", "La tasa r se expresa en decimal y t en años."])
    entregar_informe("reporte_intereses.txt","Informe de cálculo de intereses", informe)

def convertir_moneda():
    """
    Convierte entre pesos mexicanos, USD, EUR y GBP esta lo la pidio pero estaba padre y me aparecio un tutorial en you tube 
    tambien esta la estructura del informe que se crea y no incluye comision bancaria porque hacer eso era mas  complejo
    """
    print("\nCONVERSIÓN DE MONEDAS")
    print("1. Pesos mexicanos a dólares (USD)")
    print("2. Dólares (USD) a pesos mexicanos")
    print("3. Pesos mexicanos a euros (EUR)")
    print("4. Euros (EUR) a pesos mexicanos")
    print("5. Pesos mexicanos a libras esterlinas (GBP)")
    print("6. Libras esterlinas (GBP) a pesos mexicanos")
    opcion = input("Selecciona una opción: ").strip()
    configuracion = {"1": ("USD", SERIE_USD, False),"2": ("USD", SERIE_USD, True),"3": ("EUR", SERIE_EUR, False),"4": ("EUR", SERIE_EUR, True),"5": ("GBP", SERIE_GBP, False),"6": ("GBP", SERIE_GBP, True)}
    if opcion not in configuracion:
        print("Opción no válida.")
        return
    moneda, id_serie, a_pesos = configuracion[opcion]
    cantidad = pedir_numero("Cantidad que deseas convertir lee  y elige correctamente: ",minimo=0)
    cambio = consultar_serie(id_serie)
    if cambio is None:
        print(f"No se pudo consultar el tipo de cambio de {moneda} vuelve a intentarlo")
        return
    tipo_cambio = cambio["valor"]
    if tipo_cambio <= 0:
        print("Error: el tipo de cambio debe ser mayor que cero.")
        return
    if a_pesos:
        convertido = cantidad * tipo_cambio
        origen = moneda
        destino = "MXN"
        formula = "Cantidad extranjera * tipo de cambio"
    else:
        convertido = cantidad / tipo_cambio
        origen = "MXN"
        destino = moneda
        formula = "Cantidad en MXN / tipo de cambio"
    print("\nRESULTADO DE LA CONVERSIÓN")
    print(f"Serie: {cambio['serie']}")
    print(f"Nombre de la serie: {cambio['nombre']}")
    print(f"Fecha del tipo de cambio: {cambio['fecha']}")
    print(f"Tipo de cambio consultado: {tipo_cambio:.6f}")
    print(f"Cantidad original: {cantidad:,.2f} {origen}")
    print(f"Cantidad convertida: {convertido:,.2f} {destino}")
    informe = generar_informe("INFORME DE CONVERSIÓN DE MONEDA",[f"Serie: {cambio['serie']}",f"Nombre de la serie: {cambio['nombre']}",
                                                                 f"Fecha del tipo de cambio: {cambio['fecha']}",f"Tipo de cambio consultado: {tipo_cambio:.6f}",
                                                                 f"Cantidad original: {cantidad:,.2f} {origen}", f"Cantidad convertida: {convertido:,.2f} {destino}",
                                                                  f"Fórmula utilizada: {formula}", "","El cálculo no incluye comisiones bancarias."] )
    entregar_informe("reporte_conversion.txt", "Informe de conversión de moneda",informe )

def salir():
    """
    Muestra el mensaje de salida y la espera de 5 segundos
    """
    print("\nCerrando el Sistema Financiero con Banxico, se cerrará en 5 segundos...")
    time.sleep(5)
    print("Programa finalizado gracias por utilizarlo vuelva nuevamente ")
   
def menu_principal():
    """
    Muestra las cuatro opciones del sistema es lo principal del programa y lo que realiza en general.
    """
    while True:
        print(" SISTEMA FINANCIERO CON BANXICO REALIZADO BAJO EL ASESORAMIENTO DEL MAESTRO TANGLE")
        print("1. Consultar una serie de Banxico")
        print("2. Calcular interés con CETES")
        print("3. Conversión de monedas")
        print("4. Salir")
        opcion = input("Selecciona una opción: ").strip()
        if opcion == "1":
            consultar_serie_usuario()
        elif opcion == "2":
            calcular_interes()
        elif opcion == "3":
            convertir_moneda()
        elif opcion == "4":
            salir()
            break
        else:
            print("Opción no válida. Selecciona del 1 al 4.")

if __name__ == "__main__":
    try:
        menu_principal()
    except (EOFError, KeyboardInterrupt):
        print("\nPrograma interrumpido por el usuario.")

