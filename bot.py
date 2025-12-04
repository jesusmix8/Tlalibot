import telebot
from script_lechugas import recortar_lechugas_optimizado
from db import guardar_registro
from cliente_datos import ClienteDatos
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "registros.db")

# -------------------------------
# CONFIG
# -------------------------------
TOKEN = "8404642199:AAG7-nOu0W7Y_slsFjoq8BwInY7SiylwmfI"
bot = telebot.TeleBot(TOKEN)

# Ruta de imagen
IMAGEN = r"C:\Users\Jesus E S\Documents\Tec 2\Proyect\inmaduras.jpg"

# Crear cliente de datos (se conecta al servidor)
cliente = ClienteDatos(host="127.0.0.1", puerto=5000)

# -------------------------------
# FUNCIONES
# -------------------------------
def detectar_lechugas():
    lechugas = recortar_lechugas_optimizado(
        IMAGEN,
        output_dir="lechugas_recortadas_auto",
        auto_optimizar=True
    )
    return len(lechugas) if lechugas else 0

def obtener_datos_sensor():
    """Obtiene datos del servidor compartido"""
    print("⏳ Obteniendo datos del sensor...")
    return cliente.obtener_datos()

# -------------------------------
# EVENTO: CUANDO EL BOT RECIBE UN MENSAJE
# -------------------------------
@bot.message_handler(func=lambda msg: True)
def responder(msg):
    chat_id = msg.chat.id

    bot.send_message(chat_id, "🔍 Procesando imagen...")

    # 1. Datos del sensor (del servidor compartido)
    sensor = obtener_datos_sensor()
    print("Datos del sensor:", sensor)
    if sensor:
        temperatura = sensor.get("temperatura", "No disponible")
        humedad = sensor.get("humedad", "No disponible")
    else:
        temperatura = "No disponible"
        humedad = "No disponible"

    # 2. Procesamiento de imagen
    cantidad = detectar_lechugas()

    # 3. Guardar en SQLite
    guardar_registro(
        cantidad,
        None if temperatura == "No disponible" else float(temperatura),
        None if humedad == "No disponible" else float(humedad)
    )

    # 4. Mensaje final
    texto = f"""
**RESULTADOS DEL ANÁLISIS**

Lechugas detectadas: **{cantidad}**
Temperatura: **{temperatura}°C**
Humedad: **{humedad}%**

Listo! 🚀
"""
    bot.send_message(chat_id, texto, parse_mode="Markdown")

# -------------------------------
# INICIAR BOT
# -------------------------------
print("🤖 BOT ENCENDIDO")
print("Esperando comandos del usuario...")

try:
    bot.infinity_polling()
except KeyboardInterrupt:
    print("\n✋ Bot detenido")
    cliente.desconectar()