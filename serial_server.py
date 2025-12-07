import serial
import socket
import json
import time
import threading

PUERTO_SERIAL = "COM7"
BAUD = 9600

HOST = "127.0.0.1"
PUERTO_SOCKET = 5000

# Lista de clientes conectados
clientes = []
clientes_lock = threading.Lock()

# Último dato recibido (se comparte con todos los clientes)
ultimo_dato = None
dato_lock = threading.Lock()

def broadcast_data(data):
    """Envía datos a todos los clientes conectados"""
    global clientes
    
    with clientes_lock:
        clientes_desconectados = []
        
        for cliente in clientes:
            try:
                cliente.send(json.dumps(data).encode() + b"\n")
            except Exception as e:
                print(f"❌ Error enviando a cliente: {e}")
                clientes_desconectados.append(cliente)
        
        # Eliminar clientes desconectados
        for cliente in clientes_desconectados:
            try:
                cliente.close()
            except:
                pass
            clientes.remove(cliente)
            print(f"📤 Cliente desconectado. Total: {len(clientes)}")

def leer_serial(ser):
    """Thread que lee datos del puerto serial"""
    global ultimo_dato
    
    print("📖 Iniciando lectura del puerto serial...")
    
    while True:
        try:
            if ser.in_waiting > 0:
                line = ser.readline().decode().strip()

                if not line:
                    continue

                print(f"📨 Serial: {line}")

                try:
                    data = json.loads(line)
                    
                    # Guardar último dato
                    with dato_lock:
                        ultimo_dato = data
                    
                    # Enviar a todos los clientes
                    broadcast_data(data)
                    
                except json.JSONDecodeError:
                    print("❗ No es JSON válido")

        except Exception as e:
            print(f"❌ Error leyendo serial: {e}")
            time.sleep(1)

def manejar_cliente(conn, addr):
    """Thread para manejar cada cliente individualmente"""
    print(f"📡 Nuevo cliente conectado: {addr}")
    
    with clientes_lock:
        clientes.append(conn)
        print(f"👥 Total de clientes: {len(clientes)}")
    
    try:
        # Enviar último dato disponible al conectarse
        if ultimo_dato:
            conn.send(json.dumps(ultimo_dato).encode() + b"\n")
        
        # Mantener conexión abierta
        while True:
            # Recibir datos del cliente (keepalive)
            data = conn.recv(1024)
            if not data:
                break
            time.sleep(0.1)
            
    except Exception as e:
        print(f"❌ Error con cliente {addr}: {e}")
    finally:
        with clientes_lock:
            if conn in clientes:
                clientes.remove(conn)
                print(f"📤 Cliente {addr} desconectado. Total: {len(clientes)}")
        try:
            conn.close()
        except:
            pass

def aceptar_clientes(server):
    """Thread que acepta nuevas conexiones"""
    print(f"🚀 Servidor listo en {HOST}:{PUERTO_SOCKET}")
    print("⏳ Esperando conexiones...")
    
    while True:
        try:
            conn, addr = server.accept()
            
            # Crear thread para manejar este cliente
            client_thread = threading.Thread(
                target=manejar_cliente, 
                args=(conn, addr),
                daemon=True
            )
            client_thread.start()
            
        except Exception as e:
            print(f"❌ Error aceptando cliente: {e}")
            time.sleep(1)

def main():
    print("=" * 50)
    print("🔌 SERVIDOR SERIAL MULTI-CLIENTE")
    print("=" * 50)
    
    # Conectar al puerto serial
    print(f"\n🔌 Conectando a {PUERTO_SERIAL} @ {BAUD} baud...")
    try:
        ser = serial.Serial(PUERTO_SERIAL, BAUD, timeout=1)
        print("✔ Puerto serial conectado")
    except Exception as e:
        print(f"❌ Error conectando serial: {e}")
        return

    # Crear servidor socket
    print(f"\n🌐 Creando servidor socket en {HOST}:{PUERTO_SOCKET}...")
    try:
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((HOST, PUERTO_SOCKET))
        server.listen(5)  # Permitir hasta 5 conexiones en cola
        print("✔ Servidor socket listo")
    except Exception as e:
        print(f"❌ Error creando servidor: {e}")
        ser.close()
        return

    # Iniciar thread de lectura serial
    serial_thread = threading.Thread(target=leer_serial, args=(ser,), daemon=True)
    serial_thread.start()

    # Iniciar thread de aceptación de clientes
    accept_thread = threading.Thread(target=aceptar_clientes, args=(server,), daemon=True)
    accept_thread.start()

    print("\n✅ Sistema iniciado correctamente")
    print("📊 Estadísticas en tiempo real:")
    print("-" * 50)

    # Loop principal - mostrar estadísticas
    try:
        while True:
            time.sleep(5)
            with clientes_lock:
                num_clientes = len(clientes)
            
            with dato_lock:
                ultimo = ultimo_dato
            
            print(f"👥 Clientes conectados: {num_clientes} | 📨 Último dato: {ultimo}")
            
    except KeyboardInterrupt:
        print("\n\n✋ Deteniendo servidor...")
        
        # Cerrar todas las conexiones
        with clientes_lock:
            for cliente in clientes:
                try:
                    cliente.close()
                except:
                    pass
        
        server.close()
        ser.close()
        print("✔ Servidor detenido correctamente")

if __name__ == "__main__":
    main()