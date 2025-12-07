import cv2
import os

# Rutas de entrada
img1_path = "fotos/1.png"
img2_path = "fotos/2.png"
img3_path = "fotos/3.png"
img4_path = "fotos/4.png"

# Carpeta de salida
output_folder = "fotos_redimensionadas"
os.makedirs(output_folder, exist_ok=True)

# Cargar imágenes
img1 = cv2.imread(img1_path)
img2 = cv2.imread(img2_path)
img3 = cv2.imread(img3_path)
img4 = cv2.imread(img4_path)

# Validar carga
if img1 is None:
    raise ValueError("Error cargando la imagen 1. Verifica la ruta fotos/1.png")

if img2 is None or img3 is None or img4 is None:
    raise ValueError("Error cargando alguna imagen (2,3 o 4). Verifica las rutas.")

# Obtener tamaño base (el de la 1)
h1, w1 = img1.shape[:2]

# Redimensionar TODAS al tamaño de img1
img1_resized = img1  # ya tiene el tamaño correcto
img2_resized = cv2.resize(img2, (w1, h1), interpolation=cv2.INTER_AREA)
img3_resized = cv2.resize(img3, (w1, h1), interpolation=cv2.INTER_AREA)
img4_resized = cv2.resize(img4, (w1, h1), interpolation=cv2.INTER_AREA)

# Guardar imágenes
cv2.imwrite(f"{output_folder}/1_resized.png", img1_resized)
cv2.imwrite(f"{output_folder}/2_resized.png", img2_resized)
cv2.imwrite(f"{output_folder}/3_resized.png", img3_resized)
cv2.imwrite(f"{output_folder}/4_resized.png", img4_resized)

print("Imágenes redimensionadas al tamaño de la imagen 1:")
print(f"- {output_folder}/1_resized.png")
print(f"- {output_folder}/2_resized.png")
print(f"- {output_folder}/3_resized.png")
print(f"- {output_folder}/4_resized.png")
