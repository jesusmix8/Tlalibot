# ============================================
# SERVIDOR DE PUERTO SERIAL COMPARTIDO
# Archivo: serial_server.py
# Corre esto en una terminal separada
# ============================================

import serial
import json
import socket
import threading
import time
from datetime import datetime

class SerialServer:
    def __init__(self, puerto="COM8", baudrate=9600, puerto_socket=5000):
        self.puerto = puerto
        self.baudrate = baudrate
        self.puerto_socket = puerto_socket
        self.ser = None
        self.ultimo_dato = None
        self.clientes = []
        self.lock = threading.Lock()
        
        # Conectar a puerto serial
        self.conectar_serial()
    
    def conectar_serial(self):
        """Abre el puerto serial"""
        try:
            self.ser = serial.Serial(self.puerto, self.baudrate, timeout=1)
            print(f"✅ Puerto {self.puerto} abierto correctamente")
        except Exception as e:
            print(f"❌ Error abriendo puerto {self.puerto}: {e}")
            self.ser = None
    
    def leer_serial(self):
        """Lee continuamente del puerto serial"""
        while True:
            try:
                if self.ser and self.ser.in_waiting > 0:
                    linea = self.ser.readline().decode("utf-8").strip()
                    if linea:
                        try:
                            dato = json.loads(linea)
                            with self.lock:
                                self.ultimo_dato = dato
                            print(f"📊 Datos recibidos: {dato}")
                            self.broadcast_datos(dato)
                        except json.JSONDecodeError:
                            print(f"⚠️ Datos inválidos: {linea}")
                time.sleep(0.1)
            except Exception as e:
                print(f"Error leyendo serial: {e}")
                time.sleep(1)
    
    def broadcast_datos(self, dato):
        """Envía datos a todos los clientes conectados"""
        with self.lock:
            clientes_desconectados = []
            for cliente_socket in self.clientes:
                try:
                    mensaje = json.dumps(dato) + "\n"
                    cliente_socket.sendall(mensaje.encode())
                except Exception as e:
                    print(f"Error enviando a cliente: {e}")
                    clientes_desconectados.append(cliente_socket)
            
            # Eliminar clientes desconectados
            for cliente in clientes_desconectados:
                try:
                    cliente.close()
                except:
                    pass
                self.clientes.remove(cliente)
    
    def manejar_cliente(self, cliente_socket, addr):
        """Maneja conexión de un cliente"""
        print(f"🔗 Cliente conectado: {addr}")
        try:
            # Enviar último dato si existe
            with self.lock:
                if self.ultimo_dato:
                    mensaje = json.dumps(self.ultimo_dato) + "\n"
                    cliente_socket.sendall(mensaje.encode())
            
            # Mantener conexión abierta
            while True:
                time.sleep(1)
        except Exception as e:
            print(f"Error con cliente {addr}: {e}")
        finally:
            with self.lock:
                if cliente_socket in self.clientes:
                    self.clientes.remove(cliente_socket)
            cliente_socket.close()
            print(f"❌ Cliente desconectado: {addr}")
    
    def iniciar_servidor_socket(self):
        """Inicia servidor socket para distribuir datos"""
        servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        servidor.bind(("127.0.0.1", self.puerto_socket))
        servidor.listen(5)
        print(f"🚀 Servidor socket escuchando en puerto {self.puerto_socket}")
        
        while True:
            try:
                cliente_socket, addr = servidor.accept()
                with self.lock:
                    self.clientes.append(cliente_socket)
                # Manejo de cliente en thread separado
                thread = threading.Thread(target=self.manejar_cliente, args=(cliente_socket, addr))
                thread.daemon = True
                thread.start()
            except Exception as e:
                print(f"Error aceptando cliente: {e}")
    
    def iniciar(self):
        """Inicia el servidor"""
        # Thread para leer serial
        thread_serial = threading.Thread(target=self.leer_serial)
        thread_serial.daemon = True
        thread_serial.start()
        
        # Thread para servidor socket
        thread_socket = threading.Thread(target=self.iniciar_servidor_socket)
        thread_socket.daemon = True
        thread_socket.start()
        
        print("=" * 50)
        print("🌱 SERVIDOR DE DATOS EN TIEMPO REAL INICIADO")
        print("=" * 50)
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n✋ Servidor detenido")
            if self.ser:
                self.ser.close()

if __name__ == "__main__":
    servidor = SerialServer(puerto="COM8", baudrate=9600, puerto_socket=5000)
    servidor.iniciar()