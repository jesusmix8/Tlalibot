import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
import cv2
import json
import socket
import threading
from streamlit_autorefresh import st_autorefresh
from collections import deque

# Actualizar cada 2 segundos
st_autorefresh(interval=2000, key="datarefresh")

# ============================================
# CLIENTE DE DATOS - INTEGRADO
# ============================================
class ClienteDatos:
    def __init__(self, host="127.0.0.1", puerto=5000):
        self.host = host
        self.puerto = puerto
        self.socket = None
        self.conectado = False
        self.ultimo_dato = None
        self.callbacks = []
        self.intentando_reconectar = False
        
        self.conectar()
    
    def conectar(self):
        """Conecta al servidor de datos"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(5)  # Timeout de 5 segundos
            self.socket.connect((self.host, self.puerto))
            self.conectado = True
            self.intentando_reconectar = False
            
            # Iniciar thread de lectura
            thread = threading.Thread(target=self.leer_datos, daemon=True)
            thread.start()
        except Exception as e:
            self.conectado = False
            raise e
    
    def leer_datos(self):
        """Lee datos del servidor continuamente"""
        buffer = ""
        while self.conectado:
            try:
                datos = self.socket.recv(1024).decode()
                if not datos:
                    self.conectado = False
                    break
                
                buffer += datos
                
                while "\n" in buffer:
                    linea, buffer = buffer.split("\n", 1)
                    if linea.strip():
                        try:
                            self.ultimo_dato = json.loads(linea)
                            for callback in self.callbacks:
                                callback(self.ultimo_dato)
                        except json.JSONDecodeError:
                            pass
            except Exception as e:
                self.conectado = False
                break
        
        # Intentar reconectar
        if not self.intentando_reconectar:
            self.intentando_reconectar = True
            threading.Thread(target=self.reconectar, daemon=True).start()
    
    def reconectar(self):
        """Intenta reconectar al servidor"""
        while self.intentando_reconectar:
            time.sleep(3)
            try:
                self.conectar()
                print("✔ Reconectado al servidor")
                break
            except:
                print("⏳ Intentando reconectar...")
    
    def obtener_datos(self):
        """Retorna el último dato recibido"""
        return self.ultimo_dato
    
    def suscribirse(self, callback):
        """Suscribe una función para que se ejecute cuando lleguen datos"""
        self.callbacks.append(callback)
    
    def desconectar(self):
        """Cierra la conexión"""
        self.conectado = False
        self.intentando_reconectar = False
        if self.socket:
            try:
                self.socket.close()
            except:
                pass

# ============================================
# INICIALIZACIÓN
# ============================================

# Conectar al servidor de datos compartido
if "cliente_datos" not in st.session_state:
    try:
        st.session_state.cliente_datos = ClienteDatos(host="127.0.0.1", puerto=5000)
        st.session_state.serial_error = None
    except Exception as e:
        st.session_state.cliente_datos = None
        st.session_state.serial_error = f"No se pudo conectar al servidor de datos: {e}"

# Buffer de datos históricos en memoria (últimos 50 registros)
if "datos_historicos" not in st.session_state:
    st.session_state.datos_historicos = deque(maxlen=50)

# Inicializar último tiempo de actualización
if "ultimo_tiempo" not in st.session_state:
    st.session_state.ultimo_tiempo = None

def agregar_dato_historico(temp, hum, lechugas):
    """Agrega un nuevo dato al historial"""
    timestamp = datetime.now()
    st.session_state.datos_historicos.append({
        'timestamp': timestamp,
        'temperatura': temp,
        'humedad': hum,
        'lechugas': lechugas
    })
    st.session_state.ultimo_tiempo = timestamp

def obtener_datos_reales():
    """Lee datos del servidor compartido y actualiza historial"""
    if st.session_state.cliente_datos is None or st.session_state.serial_error:
        return None, None
    
    try:
        dato = st.session_state.cliente_datos.obtener_datos()
        if dato:
            temp = dato.get("temperatura")
            hum = dato.get("humedad")
            
            # Guardar en session_state para que persista
            if temp is not None:
                st.session_state.temp_actual = temp
            if hum is not None:
                st.session_state.hum_actual = hum
            
            # Agregar al historial si han pasado al menos 2 segundos
            if temp is not None and hum is not None:
                ahora = datetime.now()
                if (st.session_state.ultimo_tiempo is None or 
                    (ahora - st.session_state.ultimo_tiempo).total_seconds() >= 2):
                    lechugas = st.session_state.get('lechugas_actual', 435)
                    agregar_dato_historico(temp, hum, lechugas)
            
            return temp, hum
    except Exception as e:
        st.session_state.serial_error = f"Error leyendo datos: {e}"
    
    # Retornar último valor guardado si no hay datos nuevos
    return st.session_state.get("temp_actual"), st.session_state.get("hum_actual")

def obtener_dataframe_historico():
    """Convierte el buffer de datos históricos en DataFrame"""
    if len(st.session_state.datos_historicos) > 0:
        return pd.DataFrame(list(st.session_state.datos_historicos))
    else:
        # Datos de ejemplo iniciales
        datos_ejemplo = [
            {'timestamp': datetime.now() - timedelta(minutes=i*2), 
             'temperatura': 21.0 + i*0.2, 
             'humedad': 38.0 + i*1.5,
             'lechugas': 434}
            for i in range(10, 0, -1)
        ]
        return pd.DataFrame(datos_ejemplo)

# Configuración de la página
st.set_page_config(
    page_title="Tlalibot - Dashboard de Lechugas",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown("""
<style>
    .main {
        background: linear-gradient(135deg, #f5f7fa 0%, #e8f5e9 100%);
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 15px;
        color: white;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin: 10px 0;
    }
    
    .temp-card {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    }
    
    .hum-card {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
    }
    
    .lettuce-card {
        background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
    }
    
    .alert-danger {
        background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #ff4757;
        margin: 10px 0;
        animation: pulse 2s infinite;
    }
    
    .alert-warning {
        background: linear-gradient(135deg, #fddb92 0%, #d1fdff 100%);
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #ffa502;
        margin: 10px 0;
    }
    
    .alert-success {
        background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #26de81;
        margin: 10px 0;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.8; }
    }
    
    .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        border: none;
        padding: 10px 30px;
        font-weight: bold;
        transition: all 0.3s;
    }
    
    .stButton>button:hover {
        transform: scale(1.05);
        box-shadow: 0 5px 15px rgba(0,0,0,0.3);
    }
    
    h1, h2, h3 {
        color: #2d3436;
    }
    
    .login-container {
        max-width: 400px;
        margin: 100px auto;
        padding: 40px;
        background: white;
        border-radius: 20px;
        box-shadow: 0 10px 40px rgba(0,0,0,0.1);
    }
    
    .realtime-badge {
        display: inline-block;
        background: #ff4757;
        color: white;
        padding: 5px 15px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: bold;
        animation: pulse 2s infinite;
    }
</style>
""", unsafe_allow_html=True)

# Credenciales de usuario
USUARIO_CORRECTO = "admin"
CONTRASEÑA_CORRECTA = "lechugas2025"

# Configuración de alertas
TEMP_MIN = 18.0
TEMP_MAX = 26.0
HUMEDAD_MIN = 35.0
HUMEDAD_MAX = 50.0

def verificar_alertas(temp, hum):
    """Verifica si hay alertas de temperatura o humedad"""
    alertas = []
    
    if temp is None or hum is None:
        return alertas
    
    # Alertas de temperatura
    if temp < TEMP_MIN:
        alertas.append({
            'tipo': 'danger',
            'icono': '🥶',
            'titulo': '¡ALERTA DE TEMPERATURA BAJA!',
            'mensaje': f'La temperatura actual ({temp}°C) está por debajo del mínimo recomendado ({TEMP_MIN}°C)'
        })
    elif temp > TEMP_MAX:
        alertas.append({
            'tipo': 'danger',
            'icono': '🔥',
            'titulo': '¡ALERTA DE TEMPERATURA ALTA!',
            'mensaje': f'La temperatura actual ({temp}°C) está por encima del máximo recomendado ({TEMP_MAX}°C)'
        })
    elif temp < TEMP_MIN + 1 or temp > TEMP_MAX - 1:
        alertas.append({
            'tipo': 'warning',
            'icono': '⚠️',
            'titulo': 'Advertencia de Temperatura',
            'mensaje': f'La temperatura actual ({temp}°C) está cerca de los límites recomendados'
        })
    
    # Alertas de humedad
    if hum < HUMEDAD_MIN:
        alertas.append({
            'tipo': 'danger',
            'icono': '💧',
            'titulo': '¡ALERTA DE HUMEDAD BAJA!',
            'mensaje': f'La humedad actual ({hum}%) está por debajo del mínimo recomendado ({HUMEDAD_MIN}%)'
        })
    elif hum > HUMEDAD_MAX:
        alertas.append({
            'tipo': 'danger',
            'icono': '💦',
            'titulo': '¡ALERTA DE HUMEDAD ALTA!',
            'mensaje': f'La humedad actual ({hum}%) está por encima del máximo recomendado ({HUMEDAD_MAX}%)'
        })
    elif hum < HUMEDAD_MIN + 2 or hum > HUMEDAD_MAX - 2:
        alertas.append({
            'tipo': 'warning',
            'icono': '⚠️',
            'titulo': 'Advertencia de Humedad',
            'mensaje': f'La humedad actual ({hum}%) está cerca de los límites recomendados'
        })
    
    # Si todo está bien
    if not alertas:
        alertas.append({
            'tipo': 'success',
            'icono': '✅',
            'titulo': 'Condiciones Óptimas',
            'mensaje': 'Todos los parámetros están dentro de los rangos ideales'
        })
    
    return alertas

def mostrar_alertas(alertas):
    """Muestra las alertas en la interfaz"""
    for alerta in alertas:
        st.markdown(f"""
        <div class="alert-{alerta['tipo']}">
            <h3>{alerta['icono']} {alerta['titulo']}</h3>
            <p style="margin: 5px 0 0 0; font-size: 16px;">{alerta['mensaje']}</p>
        </div>
        """, unsafe_allow_html=True)

def login_page():
    """Página de inicio de sesión"""
    st.markdown("<div class='login-container'>", unsafe_allow_html=True)
    
    st.markdown("<h1 style='text-align: center;'>🌱 Tlalibot</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #636e72;'>Sistema de Monitoreo de Lechugas</p>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    
    usuario = st.text_input("👤 Usuario", placeholder="Ingrese su usuario")
    contraseña = st.text_input("🔒 Contraseña", type="password", placeholder="Ingrese su contraseña")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("Iniciar Sesión", use_container_width=True):
            if usuario == USUARIO_CORRECTO and contraseña == CONTRASEÑA_CORRECTA:
                st.session_state.logged_in = True
                st.success("✅ Inicio de sesión exitoso!")
                time.sleep(0.5)
                st.rerun()
            else:
                st.error("❌ Usuario o contraseña incorrectos")
    
    st.markdown("<br><p style='text-align: center; color: #b2bec3; font-size: 14px;'>Demo: admin / lechugas2025</p>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

def dashboard_page():
    """Página principal del dashboard"""
    
    # Header
    col1, col2 = st.columns([6, 1])
    with col1:
        st.markdown("# 🌱 Tlalibot - Dashboard de Lechugas")
        st.markdown(f"**Última actualización:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} <span class='realtime-badge'>● LIVE</span>", unsafe_allow_html=True)
    with col2:
        if st.button("Cerrar Sesión"):
            st.session_state.logged_in = False
            st.rerun()
    
    st.markdown("---")
    
    # Mostrar estado del puerto serial
    if st.session_state.serial_error:
        st.error(f"❌ {st.session_state.serial_error}")
        st.info("💡 **Soluciones:**\n1. Asegúrate de que `serial_server.py` está corriendo\n2. Verifica que el servidor esté escuchando en puerto 5000\n3. Comprueba que el ESP32 esté conectado")
    else:
        estado_conexion = "🟢 Conectado" if st.session_state.cliente_datos.conectado else "🔴 Desconectado"
        st.success(f"✅ {estado_conexion} al servidor de datos | 📊 {len(st.session_state.datos_historicos)} registros en memoria")
    
    st.markdown("")
    
    # Obtener datos en tiempo real
    temp_actual, hum_actual = obtener_datos_reales()
    
    # Obtener DataFrame histórico
    df = obtener_dataframe_historico()

    # Si no hay datos del sensor, usar últimos del historial
    if temp_actual is None or hum_actual is None:
        if len(df) > 0:
            temp_actual = df['temperatura'].iloc[-1]
            hum_actual = df['humedad'].iloc[-1]
        else:
            temp_actual = 21.0
            hum_actual = 38.0

    lechugas_actual = st.session_state.get('lechugas_actual', 435)
    
    # Sistema de Alertas
    st.markdown("## 🔔 Sistema de Alertas")
    alertas = verificar_alertas(temp_actual, hum_actual)
    mostrar_alertas(alertas)
    
    st.markdown("---")
    
    # Tarjetas de métricas
    st.markdown("## 📊 Métricas en Tiempo Real")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card lettuce-card">
            <h3>🥬 Total Lechugas</h3>
            <h1 style="margin: 10px 0;">{lechugas_actual}</h1>
            <p>Plantas monitoreadas</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        estado_temp = "🔥" if temp_actual > TEMP_MAX else "🥶" if temp_actual < TEMP_MIN else "✅"
        st.markdown(f"""
        <div class="metric-card temp-card">
            <h3>{estado_temp} Temperatura</h3>
            <h1 style="margin: 10px 0;">{temp_actual:.1f}°C</h1>
            <p>Rango ideal: {TEMP_MIN}°C - {TEMP_MAX}°C</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        estado_hum = "💦" if hum_actual > HUMEDAD_MAX else "💧" if hum_actual < HUMEDAD_MIN else "✅"
        st.markdown(f"""
        <div class="metric-card hum-card">
            <h3>{estado_hum} Humedad</h3>
            <h1 style="margin: 10px 0;">{hum_actual:.1f}%</h1>
            <p>Rango ideal: {HUMEDAD_MIN}% - {HUMEDAD_MAX}%</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        promedio_temp = df['temperatura'].mean()
        promedio_hum = df['humedad'].mean()
        st.markdown(f"""
        <div class="metric-card">
            <h3>📈 Promedios</h3>
            <p style="margin: 10px 0;">Temp: {promedio_temp:.1f}°C</p>
            <p style="margin: 0;">Hum: {promedio_hum:.1f}%</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Gráficas
    st.markdown("## 📈 Gráficas en Tiempo Real")
    
    tab1, tab2, tab3 = st.tabs(["🌡️ Temperatura", "💧 Humedad", "🥬 Lechugas"])
    
    with tab1:
        # Gráfica de temperatura con zonas de alerta
        fig_temp = go.Figure()
        
        # Zona de temperatura óptima
        fig_temp.add_hrect(y0=TEMP_MIN, y1=TEMP_MAX, 
                            fillcolor="green", opacity=0.1, 
                            annotation_text="Zona Óptima", 
                            annotation_position="right")
        
        # Línea de temperatura
        fig_temp.add_trace(go.Scatter(
            x=df['timestamp'], 
            y=df['temperatura'],
            mode='lines+markers',
            name='Temperatura',
            line=dict(color='#f5576c', width=3),
            marker=dict(size=8)
        ))
        
        fig_temp.update_layout(
            title="Evolución de la Temperatura en Tiempo Real",
            xaxis_title="Tiempo",
            yaxis_title="Temperatura (°C)",
            hovermode='x unified',
            height=400
        )
        st.plotly_chart(fig_temp, use_container_width=True)
    
    with tab2:
        # Gráfica de humedad con zonas de alerta
        fig_hum = go.Figure()
        
        # Zona de humedad óptima
        fig_hum.add_hrect(y0=HUMEDAD_MIN, y1=HUMEDAD_MAX, 
                            fillcolor="blue", opacity=0.1, 
                            annotation_text="Zona Óptima", 
                            annotation_position="right")
        
        # Línea de humedad
        fig_hum.add_trace(go.Scatter(
            x=df['timestamp'], 
            y=df['humedad'],
            mode='lines+markers',
            name='Humedad',
            line=dict(color='#00f2fe', width=3),
            marker=dict(size=8),
            fill='tozeroy'
        ))
        
        fig_hum.update_layout(
            title="Evolución de la Humedad en Tiempo Real",
            xaxis_title="Tiempo",
            yaxis_title="Humedad (%)",
            hovermode='x unified',
            height=400
        )
        st.plotly_chart(fig_hum, use_container_width=True)
    
    with tab3:
        # Gráfica de lechugas
        fig_lettuce = px.line(df, x='timestamp', y='lechugas', 
                                title='Evolución del Número de Lechugas',
                                markers=True)
        fig_lettuce.update_traces(line_color='#43e97b', line_width=3)
        fig_lettuce.update_layout(height=400)
        st.plotly_chart(fig_lettuce, use_container_width=True)
    
    st.markdown("---")
    
    # Tabla de registros
    st.markdown("## 📋 Últimos Registros")
    df_display = df.tail(15).copy()
    df_display['timestamp'] = df_display['timestamp'].dt.strftime('%H:%M:%S')
    df_display = df_display[['timestamp', 'temperatura', 'humedad', 'lechugas']]
    df_display.columns = ['Hora', 'Temp (°C)', 'Humedad (%)', 'Lechugas']
    st.dataframe(df_display, use_container_width=True, hide_index=True)
    
    # Configuración de alertas
    with st.expander("⚙️ Configurar Umbrales de Alerta"):
        st.markdown("### Ajusta los límites de temperatura y humedad")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**🌡️ Temperatura**")
            st.slider("Temp. Mínima (°C)", 10.0, 25.0, TEMP_MIN, 0.5, key="temp_min_slider")
            st.slider("Temp. Máxima (°C)", 20.0, 35.0, TEMP_MAX, 0.5, key="temp_max_slider")
        
        with col2:
            st.markdown("**💧 Humedad**")
            st.slider("Humedad Mínima (%)", 20.0, 50.0, HUMEDAD_MIN, 1.0, key="hum_min_slider")
            st.slider("Humedad Máxima (%)", 40.0, 80.0, HUMEDAD_MAX, 1.0, key="hum_max_slider")
        
        st.info("💡 Los valores se guardan en variables de sesión. Para cambios permanentes, modifica las constantes en el código.")

# Inicializar estado de sesión
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'temp_actual' not in st.session_state:
    st.session_state.temp_actual = None
if 'hum_actual' not in st.session_state:
    st.session_state.hum_actual = None
if 'lechugas_actual' not in st.session_state:
    st.session_state.lechugas_actual = 435

# Mostrar página correspondiente
if st.session_state.logged_in:
    dashboard_page()
else:
    login_page()