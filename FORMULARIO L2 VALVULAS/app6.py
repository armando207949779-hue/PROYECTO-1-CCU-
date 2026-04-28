# App Streamlit: Panel compacto de registro mantenimiento válvulas KRONES Línea 2

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
    except:
        ws.update("A1:G1", [headers])


def obtener_hora_chile():
    return datetime.now(ZONA_HORARIA).strftime("%Y-%m-%d %H:%M:%S")


def guardar_registros(filas):
    ws = conectar()
    init_sheet(ws)
    ws.append_rows(filas, value_input_option="USER_ENTERED")

# =====================================================
# ESTADO CHECKBOXES
# =====================================================
for numero in NUMEROS_VALVULA:
    key = f"chk_valvula_{numero}"
    if key not in st.session_state:
        st.session_state[key] = False

# 🔥 Limpieza segura después de guardar
if st.session_state.get("limpiar_despues_guardar", False):
    for numero in NUMEROS_VALVULA:
        st.session_state[f"chk_valvula_{numero}"] = False
    st.session_state["limpiar_despues_guardar"] = False

def seleccionar_todas():
    for numero in NUMEROS_VALVULA:
        st.session_state[f"chk_valvula_{numero}"] = True

def limpiar():
    for numero in NUMEROS_VALVULA:
        st.session_state[f"chk_valvula_{numero}"] = False

def obtener_valvulas_seleccionadas():
    return [
        n for n in NUMEROS_VALVULA
        if st.session_state.get(f"chk_valvula_{n}", False)
    ]

# =====================================================
# ESTILO
# =====================================================
st.markdown("""
<style>
div[data-testid="stCheckbox"] {
    margin-bottom: -14px;
}
div[data-testid="stCheckbox"] label {
    font-size: 0.72rem;
}
</style>
""", unsafe_allow_html=True)

# =====================================================
# ENCABEZADO
# =====================================================
st.markdown("""
<div style='text-align:center'>
<h1>🔧 PANEL DE MANTENIMIENTO</h1>
<h3>VÁLVULAS KRONES · LÍNEA 2</h3>
</div>
""", unsafe_allow_html=True)

# =====================================================
# DATOS GENERALES
# =====================================================
with st.container(border=True):
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        fecha = st.date_input("Fecha")

    with col2:
        turno = st.selectbox("Turno", TURNOS)

    with col3:
        operador = st.text_input("Operador").upper()

    with col4:
        repuesto = st.selectbox("Repuesto", REPUESTOS)

    observaciones = st.text_area("Observaciones")

# =====================================================
# SELECCIÓN VÁLVULAS
# =====================================================
with st.container(border=True):

    col_a, col_b, col_c = st.columns([1,1,4])

    col_a.button("Seleccionar todas", on_click=seleccionar_todas)
    col_b.button("Limpiar", on_click=limpiar)

    seleccionadas = obtener_valvulas_seleccionadas()
    col_c.info(f"Seleccionadas: {len(seleccionadas)}")

    columnas = 14

    for i in range(1, 113, columnas):
        cols = st.columns(columnas)

        for j, numero in enumerate(range(i, min(i+columnas,113))):
            with cols[j]:
                st.checkbox(str(numero), key=f"chk_valvula_{numero}")

# =====================================================
# GUARDAR
# =====================================================
guardar = st.button("💾 Guardar")

if guardar:

    seleccionadas = obtener_valvulas_seleccionadas()

    if not operador.strip():
        st.error("Operador vacío")

    elif not seleccionadas:
        st.error("Selecciona válvulas")

    else:
        filas = []

        for v in seleccionadas:
            filas.append([
                fecha.strftime("%d-%m-%Y"),
                turno,
                operador,
                v,
                repuesto,
                observaciones,
                obtener_hora_chile()
            ])

        try:
            guardar_registros(filas)
            st.success(f"Guardado OK ({len(filas)} registros)")
            st.balloons()

            # 🔥 limpieza segura
            st.session_state["limpiar_despues_guardar"] = True
            st.rerun()

        except Exception as e:
            st.error(f"Error: {e}")
