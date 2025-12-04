import cv2
import numpy as np
from pathlib import Path
import requests
from itertools import product

def recortar_lechugas_optimizado(imagen_path, output_dir="lechugas_recortadas", auto_optimizar=True):
    """
    Detecta y recorta cada lechuga individualmente de una imagen aérea.
    Con opción de auto-optimización de parámetros.
    
    Args:
        imagen_path: Ruta de la imagen de entrada
        output_dir: Carpeta donde se guardarán las lechugas recortadas
        auto_optimizar: Si True, prueba diferentes parámetros para maximizar detecciones
    """

    Path(output_dir).mkdir(exist_ok=True)
    

    img = cv2.imread(imagen_path)
    if img is None:
        print(f"Error: No se pudo cargar la imagen {imagen_path}")
        return
    
    if auto_optimizar:
        print(" Iniciando búsqueda de parámetros óptimos...\n")
        mejor_config = optimizar_parametros(img)
        print(f"\n✓ Mejor configuración encontrada:")
        print(f"  - HSV inferior: {mejor_config['lower_green']}")
        print(f"  - HSV superior: {mejor_config['upper_green']}")
        print(f"  - Área mínima: {mejor_config['min_area']}")
        print(f"  - Área máxima: {mejor_config['max_area']}")
        print(f"  - Lechugas detectadas: {mejor_config['count']}\n")
        
        params = mejor_config
    else:
        # Parámetros por defecto
        params = {
            'lower_green': np.array([25, 100, 80]),
            'upper_green': np.array([37, 255, 192]),
            'min_area': 50,
            'max_area': 1100
        }
    
    lechugas = detectar_y_recortar(img, params, output_dir)
    return lechugas


def optimizar_parametros(img):

    h_min_range = range(20, 40, 3)      
    h_max_range = range(30, 50, 3)     
    s_min_range = range(40, 120, 20)    
    v_min_range = range(40, 120, 20)    

    min_area_range = [30, 50, 80, 100]
    max_area_range = [800, 1000, 1200, 1500, 2000]
    
    mejor_config = {
        'count': 0,
        'lower_green': None,
        'upper_green': None,
        'min_area': None,
        'max_area': None
    }
    
    total_iteraciones = (len(h_min_range) * len(h_max_range) * 
                        len(s_min_range) * len(v_min_range) * 
                        len(min_area_range) * len(max_area_range))
    
    print(f"Probando {total_iteraciones} combinaciones de parámetros...")
    iteracion = 0
    
    # Iterar sobre combinaciones
    for h_min, h_max, s_min, v_min, min_area, max_area in product(
        h_min_range, h_max_range, s_min_range, v_min_range, 
        min_area_range, max_area_range
    ):
        if h_min >= h_max:
            continue
        
        iteracion += 1
        if iteracion % 100 == 0:
            print(f"  Progreso: {iteracion}/{total_iteraciones} ({iteracion*100//total_iteraciones}%)")
        
        # Crear parámetros de prueba
        params = {
            'lower_green': np.array([h_min, s_min, v_min]),
            'upper_green': np.array([h_max, 255, 255]),
            'min_area': min_area,
            'max_area': max_area
        }
        
        # Contar detecciones con estos parámetros
        count = contar_detecciones(img, params)
        
        # Actualizar si es mejor
        if count > mejor_config['count']:
            mejor_config['count'] = count
            mejor_config['lower_green'] = params['lower_green']
            mejor_config['upper_green'] = params['upper_green']
            mejor_config['min_area'] = params['min_area']
            mejor_config['max_area'] = params['max_area']
            print(f"  ✓ Nueva mejor configuración: {count} lechugas detectadas")
    
    return mejor_config


def contar_detecciones(img, params):
    """
    Cuenta cuántas lechugas se detectan con los parámetros dados.
    """
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, params['lower_green'], params['upper_green'])
    
    # Operaciones morfológicas
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=2)
    
    # Encontrar contornos
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Contar contornos válidos
    count = 0
    for contour in contours:
        area = cv2.contourArea(contour)
        if params['min_area'] < area < params['max_area']:
            count += 1
    
    return count


def detectar_y_recortar(img, params, output_dir):
    """
    Detecta y recorta lechugas usando los parámetros especificados.
    """
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, params['lower_green'], params['upper_green'])
    
    # Operaciones morfológicas
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=2)
    
    # Encontrar contornos
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    lechugas_recortadas = []
    contador = 0
    
    for contour in contours:
        area = cv2.contourArea(contour)
        
        if params['min_area'] < area < params['max_area']:
            x, y, w, h = cv2.boundingRect(contour)
            
            # Añadir margen
            margen = 10
            x_inicio = max(0, x - margen)
            y_inicio = max(0, y - margen)
            x_fin = min(img.shape[1], x + w + margen)
            y_fin = min(img.shape[0], y + h + margen)

            
            contador += 1

            
            lechugas_recortadas.append({
                'id': contador,
                'posicion': (x, y),
                'tamaño': (w, h),
                'area': area
            })
        
    return lechugas_recortadas


if __name__ == "__main__":
    ruta_imagen = r"C:\Users\Jesus E S\Documents\Tec 2\Proyect\inmaduras.jpg"
    
    info_lechugas = recortar_lechugas_optimizado(
        ruta_imagen, 
        output_dir="lechugas_recortadas_auto",
        auto_optimizar=True
    )
    

    if info_lechugas:

        lechcugas_contador = len(info_lechugas)
