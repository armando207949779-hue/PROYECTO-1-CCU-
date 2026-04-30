# App Streamlit: Registro mantenimiento válvulas KRONES Línea 2 (SIN LOGO)

import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, date
from zoneinfo import ZoneInfo

# =====================================================
# CONFIGURACIÓN GENERAL
# =====================================================
st.set_page_config(
    page_title="Registro Mantenimiento Válvulas L2",
    layout="wide"
)

SHEET_URL = "https://docs.google.com/spreadsheets/d/12SH_kgBr436fu6gsuqISgXANebVtV_XL2AUH9WASfoI/edit?usp=sharing"
ZONA_HORARIA = ZoneInfo("America/Santiago")

TURNOS = ["", "A", "B", "C"]

OPERADORES = [
    "",
    "RICHARD RUZ",
    "DIDIMO VALERO",
    "JORGE GONZALES",
    "JUAN RUPERTUS MONDACA",
    "OTRO"
]

REPUESTOS = [
    "BLOQUE",
    "O-RINGS",
    "RESORTE",
    "ON/OFF",
    "OTRO"
]

NUMEROS_VALVULA = list(range(1, 113))


# =====================================================
# GOOGLE SHEETS
# =====================================================
@st.cache_resource(ttl=60)
def conectar_google_sheet():
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


def inicializar_hoja(ws):
    headers = [
        "Fecha",
        "Turno",
        "Operador",
        "Número Válvula",
        "Repuesto / Mantención",
        "Observaciones",
        "Fecha Registro",
        "Origen"
    ]

    try:
        if ws.row_values(1) != headers:
            ws.update("A1:H1", [headers])
    except Exception:
        ws.update("A1:H1", [headers])


def obtener_fecha_registro():
    return datetime.now(ZONA_HORARIA).strftime("%Y-%m-%d %H:%M:%S")


def guardar_registros(filas):
    ws = conectar_google_sheet()
    inicializar_hoja(ws)
    ws.append_rows(filas, value_input_option="USER_ENTERED")


# =====================================================
# ESTILO
# =====================================================
st.markdown(
    """
    <style>
    .block-container {padding-top: 1rem; padding-bottom: 1rem;}
    div[data-testid="stCheckbox"] {margin-bottom: -12px;}
    div[data-testid="stCheckbox"] label {font-size: 0.75rem;}
    div[data-testid="stVerticalBlock"] {gap: 0.35rem;}
    </style>
    """,
    unsafe_allow_html=True
)


# =====================================================
# ENCABEZADO (SIN LOGO)
# =====================================================
st.markdown(
    """
    <div style='text-align:left; padding-bottom:10px;'>
        <h1 style='color:#0E4C92; margin-bottom:0px;'>
            Registro de Mantenimiento de Válvulas KRONES
        </h1>
        <h3 style='color:#2E86C1; margin-top:4px;'>
            Línea 2 · Planta Modelo
        </h3>
        <p style='color:#5D6D7E;'>
            Formulario para registrar mantenciones operacionales.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)


# =====================================================
# DATOS GENERALES
# =====================================================
with st.container(border=True):
    st.subheader("Datos generales")

    col1, col2, col3 = st.columns(3)

    with col1:
        fecha = st.date_input("Fecha", value=date.today())

    with col2:
        turno = st.selectbox("Turno", TURNOS)

    with col3:
        operador_sel = st.selectbox("Operador", OPERADORES)

    operador_manual = ""
    if operador_sel == "OTRO":
        operador_manual = st.text_input("Especificar operador").upper().strip()

    operador_final = operador_manual if operador_sel == "OTRO" else operador_sel


# =====================================================
# REPUESTO (SELECCIÓN ÚNICA)
# =====================================================
with st.container(border=True):
    st.subheader("Repuesto / Mantención")

    repuesto_sel = st.selectbox("Seleccione", [""] + REPUESTOS)

    otro_repuesto = ""
    if repuesto_sel == "OTRO":
        otro_repuesto = st.text_input("Especificar OTRO").upper().strip()

    repuesto_final = otro_repuesto if repuesto_sel == "OTRO" else repuesto_sel

    observaciones = st.text_area("Observaciones", height=80)


# =====================================================
# VÁLVULAS
# =====================================================
with st.container(border=True):
    st.subheader("Selección de válvulas")

    columnas = 14

    for inicio in range(1, 113, columnas):
        cols = st.columns(columnas)
        for i, num in enumerate(range(inicio, min(inicio + columnas, 113))):
            with cols[i]:
                st.checkbox(str(num), key=f"val_{num}")

    valvulas = [
        n for n in NUMEROS_VALVULA
        if st.session_state.get(f"val_{n}", False)
    ]

    st.info(f"Seleccionadas: {len(valvulas)}")


# =====================================================
# RESUMEN
# =====================================================
with st.container(border=True):
    st.subheader("Resumen")

    st.write("Turno:", turno)
    st.write("Operador:", operador_final)
    st.write("Válvulas:", valvulas)
    st.write("Repuesto:", repuesto_final)

    guardar = st.button("Guardar", use_container_width=True)


# =====================================================
# GUARDADO
# =====================================================
if guardar:

    errores = []

    if not turno:
        errores.append("Seleccionar turno")
    if not operador_final:
        errores.append("Ingresar operador")
    if not valvulas:
        errores.append("Seleccionar válvulas")
    if not repuesto_sel:
        errores.append("Seleccionar repuesto")
    if repuesto_sel == "OTRO" and not otro_repuesto:
        errores.append("Especificar OTRO")

    if errores:
        for e in errores:
            st.error(e)

    else:
        filas = []
        fecha_reg = obtener_fecha_registro()

        for v in valvulas:
            filas.append([
                fecha.strftime("%d-%m-%Y"),
                turno,
                operador_final,
                v,
                repuesto_final,
                observaciones,
                fecha_reg,
                "Streamlit"
            ])

        try:
            guardar_registros(filas)
            st.success(f"{len(filas)} registros guardados correctamente")
        except Exception as e:
            st.error(f"Error: {e}")
