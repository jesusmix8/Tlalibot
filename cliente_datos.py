# ============================================
# MÓDULO CLIENTE - Para usar en tus scripts
# Archivo: cliente_datos.py
# ============================================

import socket
import json
import threading
import time

class ClienteDatos:
    def __init__(self, host="127.0.0.1", puerto=5000):
        self.host = host
        self.puerto = puerto
        self.socket = None
        self.conectado = False
        self.ultimo_dato = None
        self.callbacks = []  # Para ejecutar funciones cuando llegan datos
        
        self.conectar()
    
    def conectar(self):
        """Conecta al servidor de datos"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.puerto))
            self.conectado = True
            print(f"✅ Conectado al servidor en {self.host}:{self.puerto}")
            
            # Iniciar thread de lectura
            thread = threading.Thread(target=self.leer_datos, daemon=True)
            thread.start()
        except Exception as e:
            print(f"❌ Error conectando al servidor: {e}")
            self.conectado = False
    
    def leer_datos(self):
        """Lee datos del servidor continuamente"""
        buffer = ""
        while self.conectado:
            try:
                datos = self.socket.recv(1024).decode()
                if not datos:
                    self.conectado = False
                    print("❌ Servidor desconectado")
                    break
                
                buffer += datos
                
                # Procesar mensajes completos (separados por \n)
                while "\n" in buffer:
                    linea, buffer = buffer.split("\n", 1)
                    if linea.strip():
                        try:
                            self.ultimo_dato = json.loads(linea)
                            # Ejecutar callbacks
                            for callback in self.callbacks:
                                callback(self.ultimo_dato)
                        except json.JSONDecodeError:
                            print(f"⚠️ Datos inválidos: {linea}")
            except Exception as e:
                print(f"Error leyendo datos: {e}")
                self.conectado = False
                time.sleep(2)
                self.conectar()
    
    def obtener_datos(self):
        """Retorna el último dato recibido"""
        return self.ultimo_dato
    
    def suscribirse(self, callback):
        """Suscribe una función para que se ejecute cuando lleguen datos"""
        self.callbacks.append(callback)
    
    def desconectar(self):
        """Cierra la conexión"""
        self.conectado = False
        if self.socket:
            self.socket.close()
            print("Desconectado del servidor")