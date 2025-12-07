import telebot
from script_lechugas import recortar_lechugas_optimizado, dibujar_lechugas
from db import guardar_registro
from cliente_datos import ClienteDatos
import os
import cv2


import random as rnd
# -------------------------------
# CONFIG
# -------------------------------


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "registros.db")
TOKEN = "8404642199:AAG7-nOu0W7Y_slsFjoq8BwInY7SiylwmfI"


bot = telebot.TeleBot(TOKEN)

# Cliente de datos
cliente = ClienteDatos(host="127.0.0.1", puerto=5000)

# Reintentos de conexión
MAX_INTENTOS = 3

# -------------------------------
# FUNCIONES
# -------------------------------
def detectar_lechugas(imagen_path):
    lechugas = recortar_lechugas_optimizado(
        imagen_path,
        output_dir="lechugas_recortadas_auto",
        auto_optimizar=True
    )
    return lechugas if lechugas else []

def obtener_datos_sensor():
    print("⏳ Obteniendo datos del sensor...")
    for intento in range(MAX_INTENTOS):
        try:
            data = cliente.obtener_datos()
            return data
        except Exception as e:
            print(f"❌ Intento {intento + 1}/{MAX_INTENTOS} - Error: {e}")
            if intento < MAX_INTENTOS - 1:
                import time
                time.sleep(2)
    return None

def enviar_mensaje_largo(chat_id, texto, parse_mode="Markdown"):
    """Divide mensajes largos en partes de máximo 4096 caracteres"""
    MAX_CHARS = 4096
    
    if len(texto) <= MAX_CHARS:
        bot.send_message(chat_id, texto, parse_mode=parse_mode)
    else:
        partes = texto.split("\n\n")
        mensaje_actual = ""
        
        for parte in partes:
            if len(mensaje_actual) + len(parte) + 2 > MAX_CHARS:
                if mensaje_actual:
                    bot.send_message(chat_id, mensaje_actual, parse_mode=parse_mode)
                mensaje_actual = parte
            else:
                mensaje_actual += "\n\n" + parte if mensaje_actual else parte
        
        if mensaje_actual:
            bot.send_message(chat_id, mensaje_actual, parse_mode=parse_mode)

# -------------------------------
# EVENTO TELEGRAM
# -------------------------------
@bot.message_handler(func=lambda msg: True)
@bot.message_handler(func=lambda msg: True)
def responder(msg):
    chat_id = msg.chat.id

    bot.send_message(chat_id, "Procesando imagen...")

    # Elegir imagen al azar
    imgrand = rnd.randint(1, 4)
    IMAGEN = f"C:\\Users\\Jesus E S\\Documents\\Tec 2\\Proyect\\fotos\\{imgrand}.png"

    # 1. Datos sensor
    sensor = obtener_datos_sensor()
    print(" Datos del sensor obtenidos:", sensor)

    if sensor:
        temperatura = sensor.get("temperatura", "No disponible")
        humedad     = sensor.get("humedad", "No disponible")
    else:
        temperatura = "No disponible"
        humedad = "No disponible"

    # 2. Procesamiento imagen
    lechugas = detectar_lechugas(IMAGEN)
    cantidad = len(lechugas)

    # 3. Dibujar imagen con rectángulos
    imagen_con_cajas = dibujar_lechugas(IMAGEN, lechugas)
    ruta_salida_img = "resultado_lechugas.png"
    cv2.imwrite(ruta_salida_img, imagen_con_cajas)

    # 4. Guardar en DB
    guardar_registro(
        cantidad,
        None if temperatura == "No disponible" else float(temperatura),
        None if humedad == "No disponible" else float(humedad)
    )

    # 5. Enviar imagen detectada
    with open(ruta_salida_img, "rb") as f:
        bot.send_photo(chat_id, f, caption="🖼 Lechugas detectadas")

    # 6. Enviar resultado final
    texto = f"""**RESULTADOS DEL ANÁLISIS**

Lechugas detectadas: **{cantidad}**
Temperatura: **{temperatura}°C**
Humedad: **{humedad}%**

Listo! """

    enviar_mensaje_largo(chat_id, texto, parse_mode="Markdown")


# -------------------------------
# INICIAR BOT
# -------------------------------
print("BOT ENCENDIDO")
print(" Asegúrate de que el serial_server.py esté corriendo en otra terminal")
print("Esperando comandos del usuario...")

try:
    bot.infinity_polling()
except KeyboardInterrupt:
    cliente.desconectar()
    print("\n✋ Bot detenido")