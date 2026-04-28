# App Streamlit: Panel de registro mantenimiento válvulas KRONES Línea 2

import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
from zoneinfo import ZoneInfo

# =====================================================
# CONFIGURACIÓN GENERAL
# =====================================================
st.set_page_config(
    page_title="Panel Mantenimiento Válvulas L2",
    page_icon="🔧",
    layout="wide"
)

# 🔥 NUEVA RUTA
SHEET_URL = "https://docs.google.com/spreadsheets/d/12SH_kgBr436fu6gsuqISgXANebVtV_XL2AUH9WASfoI/edit?usp=sharing"

ZONA_HORARIA = ZoneInfo("America/Santiago")

TURNOS = ["A", "B", "C"]
NUMEROS_VALVULA = list(range(1, 113))
REPUESTOS = ["BLOQUE", "O-RINGS", "RESORTE", "ON/OFF", "OTRO"]

# =====================================================
# CONEXIÓN GOOGLE SHEETS
# =====================================================
@st.cache_resource
def conectar():
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=scope
    )

    client = gspread.authorize(creds)
    return client.open_by_url(SHEET_URL).sheet1


def init_sheet(ws):
    headers = [
        "Fecha",
        "Turno",
        "Operador",
        "Número Válvula",
        "Repuesto",
        "Observaciones",
        "Fecha registro"
    ]

    try:
        if ws.row_values(1) != headers:
            ws.update("A1:G1", [headers])
    except Exception:
        ws.update("A1:G1", [headers])


def obtener_hora_chile():
    return datetime.now(ZONA_HORARIA).strftime("%Y-%m-%d %H:%M:%S")


def guardar_registros(filas):
    ws = conectar()
    init_sheet(ws)
    ws.append_rows(filas, value_input_option="USER_ENTERED")


# =====================================================
# ESTADO DE SELECCIÓN
# =====================================================
if "valvulas_seleccionadas" not in st.session_state:
    st.session_state.valvulas_seleccionadas = []


def toggle_valvula(numero):
    if numero in st.session_state.valvulas_seleccionadas:
        st.session_state.valvulas_seleccionadas.remove(numero)
    else:
        st.session_state.valvulas_seleccionadas.append(numero)


# =====================================================
# ENCABEZADO
# =====================================================
st.markdown(
    """
    <div style='text-align:center; padding: 10px 0 20px 0;'>
        <h1 style='color:#0E4C92;'>🔧 PANEL DE MANTENIMIENTO</h1>
        <h3 style='color:#2E86C1;'>VÁLVULAS KRONES · LÍNEA 2</h3>
    </div>
    """,
    unsafe_allow_html=True
)

# =====================================================
# PANEL DE DATOS GENERALES
# =====================================================
with st.container(border=True):
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        fecha = st.date_input("📅 Fecha")

    with col2:
        turno = st.selectbox("👷 Turno", TURNOS)

    with col3:
        operador = st.text_input("👤 Operador").upper()

    with col4:
        repuesto = st.selectbox("📦 Repuesto", REPUESTOS)

    observaciones = st.text_area("📋 Observaciones", height=90)

# =====================================================
# PANEL DE SELECCIÓN
# =====================================================
with st.container(border=True):

    col_a, col_b = st.columns(2)

    with col_a:
        if st.button("Seleccionar todas"):
            st.session_state.valvulas_seleccionadas = NUMEROS_VALVULA.copy()
            st.rerun()

    with col_b:
        if st.button("Limpiar"):
            st.session_state.valvulas_seleccionadas = []
            st.rerun()

    columnas = 8

    for i in range(0, 112, columnas):
        cols = st.columns(columnas)
        for j in range(columnas):
            num = i + j + 1
            if num <= 112:
                with cols[j]:
                    if st.button(str(num)):
                        toggle_valvula(num)
                        st.rerun()

# =====================================================
# GUARDAR
# =====================================================
guardar = st.button("💾 Guardar")

if guardar:
    if not operador.strip():
        st.error("Operador vacío")
    elif not st.session_state.valvulas_seleccionadas:
        st.error("Selecciona válvulas")
    else:
        filas = []
        for v in st.session_state.valvulas_seleccionadas:
            filas.append([
                fecha.strftime("%d-%m-%Y"),
                turno,
                operador,
                v,
                repuesto,
                observaciones,
                obtener_hora_chile()
            ])

        guardar_registros(filas)
        st.success("Guardado OK")
