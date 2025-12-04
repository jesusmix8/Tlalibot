import cv2
import numpy as np
import os

# Ruta a tu imagen (ajústala según tu PC)
IMAGE_PATH = r"C:\Users\Jesus E S\Documents\Tec 2\Proyect\inmaduras.jpg"

# Leer imagen
img = cv2.imread(IMAGE_PATH)
if img is None:
    raise FileNotFoundError("No se pudo abrir la imagen. Verifica la ruta.")

# Convertir a HSV
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

# Separar canales
h, s, v = cv2.split(hsv)

# Crear carpeta de salida
os.makedirs("hsv_output", exist_ok=True)

# Guardar canales
cv2.imwrite("hsv_output/h_channel.jpg", h)
cv2.imwrite("hsv_output/s_channel.jpg", s)
cv2.imwrite("hsv_output/v_channel.jpg", v)

print("Canales guardados en carpeta hsv_output/")

# -------- SELECTOR INTERACTIVO DE HSV --------

def pick_color(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        pixel = hsv[y, x]
        print(f"HSV en ({x},{y}): {pixel}")

# Crear ventana
cv2.namedWindow("Imagen")
cv2.setMouseCallback("Imagen", pick_color)

print("Haz clic en la imagen para obtener valores HSV (ESC para salir)")

# Mostrar imagen
while True:
    cv2.imshow("Imagen", img)
    key = cv2.waitKey(1) & 0xFF
    if key == 27:  # ESC para salir
        break

cv2.destroyAllWindows()
