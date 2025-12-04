import telebot
from Tlalibot.script_lechugas import recortar_lechugas_optimizado
from db import guardar_registro
from cliente_datos import ClienteDatos
import os
import cv2
import numpy as np
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "registros.db")

# -------------------------------
# CONFIG
# -------------------------------
TOKEN = "8404642199:AAG7-nOu0W7Y_slsFjoq8BwInY7SiylwmfI"
bot = telebot.TeleBot(TOKEN)

# Directorio para guardar las fotos capturadas
FOTOS_DIR = os.path.join(BASE_DIR, "fotos_capturadas")
FOTOS_PROCESADAS_DIR = os.path.join(BASE_DIR, "fotos_procesadas")
os.makedirs(FOTOS_DIR, exist_ok=True)
os.makedirs(FOTOS_PROCESADAS_DIR, exist_ok=True)

# Configuración de la cámara
CAMERA_INDEX = 0  # 0 para la cámara por defecto, 1, 2... para otras cámaras

# Crear cliente de datos (se conecta al servidor)
cliente = ClienteDatos(host="127.0.0.1", puerto=5000)

# -------------------------------
# FUNCIONES
# -------------------------------
def capturar_foto_camara():
    """
    Captura una foto desde la cámara conectada
    Retorna la ruta del archivo guardado o None si hay error
    """
    print("📷 Abriendo cámara...")
    cap = cv2.VideoCapture(CAMERA_INDEX)
    
    if not cap.isOpened():
        print("❌ Error: No se pudo abrir la cámara")
        return None
    
    # Dar tiempo a la cámara para ajustarse
    import time
    time.sleep(1)
    
    # Capturar varios frames y usar el último (mejor calidad)
    for _ in range(5):
        ret, frame = cap.read()
    
    ret, frame = cap.read()
    cap.release()
    
    if not ret:
        print("❌ Error: No se pudo capturar la imagen")
        return None
    
    # Guardar imagen con timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"captura_{timestamp}.jpg"
    filepath = os.path.join(FOTOS_DIR, filename)
    
    cv2.imwrite(filepath, frame)
    print(f"✓ Foto guardada: {filepath}")
    
    return filepath

def dibujar_detecciones(imagen_path, lechugas_info):
    """
    Dibuja recuadros en la imagen mostrando las lechugas detectadas
    Retorna la ruta de la imagen procesada
    """
    # Cargar imagen original
    img = cv2.imread(imagen_path)
    if img is None:
        return None
    
    # Dibujar recuadros para cada lechuga detectada
    for lechuga in lechugas_info:
        x, y = lechuga['posicion']
        w, h = lechuga['tamaño']
        area = lechuga['area']
        id_lechuga = lechuga['id']
        
        # Añadir margen al recuadro
        margen = 10
        x_inicio = max(0, x - margen)
        y_inicio = max(0, y - margen)
        x_fin = min(img.shape[1], x + w + margen)
        y_fin = min(img.shape[0], y + h + margen)
        
        # Dibujar rectángulo (verde brillante)
        cv2.rectangle(img, (x_inicio, y_inicio), (x_fin, y_fin), (0, 255, 0), 3)
        
        # Agregar etiqueta con ID y área
        label = f"{id_lechuga}"
        
        # Fondo para el texto
        (label_width, label_height), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 1)
        cv2.rectangle(img, 
                     (x_inicio, y_inicio - label_height - 5), 
                     (x_inicio + label_width + 5, y_inicio), 
                     (0, 255, 0), -1)
        
        # Texto
        cv2.putText(img, label, (x_inicio + 2, y_inicio - 2), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)
    
    # Agregar contador total en la esquina superior
    total_text = f"Total: {len(lechugas_info)} lechugas"
    cv2.rectangle(img, (8, 8), (250, 40), (0, 255, 0), -1)
    cv2.putText(img, total_text, (5, 9), 
               cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
    
    # Guardar imagen procesada
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"procesada_{timestamp}.jpg"
    filepath = os.path.join(FOTOS_PROCESADAS_DIR, filename)
    cv2.imwrite(filepath, img)
    
    print(f"✓ Imagen procesada guardada: {filepath}")
    return filepath

def detectar_lechugas(imagen_path):
    """
    Procesa la imagen y detecta lechugas
    Retorna (cantidad, info_lechugas)
    """
    lechugas = recortar_lechugas_optimizado(
        imagen_path,
        output_dir="lechugas_recortadas_auto",
        auto_optimizar=True
    )
    
    cantidad = len(lechugas) if lechugas else 0
    return cantidad, lechugas

def obtener_datos_sensor():
    """Obtiene datos del servidor compartido"""
    print("⏳ Obteniendo datos del sensor...")
    return cliente.obtener_datos()

# -------------------------------
# COMANDOS DEL BOT
# -------------------------------
@bot.message_handler(commands=['start', 'ayuda'])
def enviar_bienvenida(msg):
    """Mensaje de bienvenida"""
    texto = """
🌱 **Bot de Detección de Lechugas**

Comandos disponibles:
/analizar - Captura foto y analiza lechugas
/estado - Verifica estado del bot
/ayuda - Muestra este mensaje

Envía cualquier mensaje para analizar lechugas 📸
"""
    bot.send_message(msg.chat.id, texto, parse_mode="Markdown")

@bot.message_handler(commands=['estado'])
def enviar_estado(msg):
    """Verifica el estado del sistema"""
    # Probar cámara
    cap = cv2.VideoCapture(CAMERA_INDEX)
    camara_ok = cap.isOpened()
    cap.release()
    
    # Probar sensor
    sensor_data = obtener_datos_sensor()
    sensor_ok = sensor_data is not None
    
    texto = f"""
🔍 **Estado del Sistema**

📷 Cámara: {'✅ Funcionando' if camara_ok else '❌ No disponible'}
🌡️ Sensor: {'✅ Conectado' if sensor_ok else '❌ Desconectado'}
"""
    bot.send_message(msg.chat.id, texto, parse_mode="Markdown")

@bot.message_handler(commands=['analizar'])
def analizar_comando(msg):
    """Comando específico para analizar"""
    procesar_analisis(msg)

@bot.message_handler(func=lambda msg: True)
def responder(msg):
    """Responde a cualquier mensaje"""
    procesar_analisis(msg)

# -------------------------------
# FUNCIÓN PRINCIPAL DE ANÁLISIS
# -------------------------------
def procesar_analisis(msg):
    """
    Función principal que:
    1. Captura foto de la cámara
    2. Procesa la imagen y detecta lechugas
    3. Dibuja recuadros en la imagen
    4. Obtiene datos del sensor
    5. Guarda en BD
    6. Envía resultados con imagen procesada
    """
    chat_id = msg.chat.id
    
    bot.send_message(chat_id, "📷 Capturando imagen...")
    
    # 1. Capturar foto de la cámara
    imagen_path = capturar_foto_camara()
    
    if imagen_path is None:
        bot.send_message(
            chat_id, 
            "❌ Error: No se pudo capturar la imagen.\n"
            "Verifica que la cámara esté conectada."
        )
        return
    
    bot.send_message(chat_id, "🔍 Procesando imagen y detectando lechugas...")
    
    # 2. Procesamiento de imagen y detección
    try:
        cantidad, lechugas_info = detectar_lechugas(imagen_path)
    except Exception as e:
        print(f"Error al procesar imagen: {e}")
        bot.send_message(chat_id, f"❌ Error al procesar la imagen: {str(e)}")
        return
    
    # 3. Dibujar recuadros en la imagen
    if lechugas_info and len(lechugas_info) > 0:
        imagen_procesada = dibujar_detecciones(imagen_path, lechugas_info)
        
        if imagen_procesada and os.path.exists(imagen_procesada):
            # Enviar imagen con detecciones
            try:
                with open(imagen_procesada, 'rb') as photo:
                    bot.send_photo(chat_id, photo, 
                                 caption=f"🌱 Imagen procesada - {cantidad} lechugas detectadas")
            except Exception as e:
                print(f"Error al enviar foto procesada: {e}")
                # Si falla, enviar la original
                try:
                    with open(imagen_path, 'rb') as photo:
                        bot.send_photo(chat_id, photo, caption="📸 Imagen capturada (original)")
                except Exception as e2:
                    print(f"Error al enviar foto original: {e2}")
        else:
            # Si no se pudo procesar, enviar original
            try:
                with open(imagen_path, 'rb') as photo:
                    bot.send_photo(chat_id, photo, caption="📸 Imagen capturada")
            except Exception as e:
                print(f"Error al enviar foto: {e}")
    else:
        # No se detectaron lechugas, enviar imagen original
        bot.send_message(chat_id, "⚠️ No se detectaron lechugas en la imagen")
        try:
            with open(imagen_path, 'rb') as photo:
                bot.send_photo(chat_id, photo, caption="📸 Imagen capturada (sin detecciones)")
        except Exception as e:
            print(f"Error al enviar foto: {e}")
    
    # 4. Datos del sensor (del servidor compartido)
    sensor = obtener_datos_sensor()
    print("Datos del sensor:", sensor)
    if sensor:
        temperatura = sensor.get("temperatura", "No disponible")
        humedad = sensor.get("humedad", "No disponible")
    else:
        temperatura = "No disponible"
        humedad = "No disponible"
    
    # 5. Guardar en SQLite
    guardar_registro(
        cantidad,
        None if temperatura == "No disponible" else float(temperatura),
        None if humedad == "No disponible" else float(humedad)
    )
    
    # 6. Mensaje final con resultados detallados
    if lechugas_info and len(lechugas_info) > 0:
        # Crear lista de lechugas detectadas
        detalles = "\n".join([
            f"{l['id']}: {l['area']:.0f}px² en ({l['posicion'][0]}, {l['posicion'][1]})"
            for l in lechugas_info[:5]  # Mostrar máximo 5
        ])
        
        if len(lechugas_info) > 5:
            detalles += f"\n  • ... y {len(lechugas_info) - 5} más"
        
        texto = f"""
✅ **RESULTADOS DEL ANÁLISIS**

🌱 Lechugas detectadas: **{cantidad}**
🌡️ Temperatura: **{temperatura}°C**
💧 Humedad: **{humedad}%**

📊 **Detalle de lechugas:**
{detalles}

✨ Análisis completado
"""
    else:
        texto = f"""
⚠️ **RESULTADOS DEL ANÁLISIS**

🌱 Lechugas detectadas: **0**
🌡️ Temperatura: **{temperatura}°C**
💧 Humedad: **{humedad}%**

💡 **Sugerencias:**
• Verifica la iluminación
• Ajusta la posición de la cámara
• Revisa si hay lechugas en el encuadre
"""
    
    bot.send_message(chat_id, texto, parse_mode="Markdown")

# -------------------------------
# INICIAR BOT
# -------------------------------
print("🤖 BOT ENCENDIDO")
print(f"📷 Cámara configurada: índice {CAMERA_INDEX}")
print(f"📁 Fotos originales: {FOTOS_DIR}")
print(f"📁 Fotos procesadas: {FOTOS_PROCESADAS_DIR}")
print("Esperando comandos del usuario...")

try:
    bot.infinity_polling()
except KeyboardInterrupt:
    print("\n✋ Bot detenido")
    cliente.desconectar()