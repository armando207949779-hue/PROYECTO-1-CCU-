# App Streamlit: Registro mantenimiento válvulas KRONES Línea 2
# Versión con logo, formato mejorado, margen ajustado y operadores actualizados

import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, date
from zoneinfo import ZoneInfo
from pathlib import Path
import base64

# =====================================================
# CONFIGURACIÓN GENERAL
# =====================================================
st.set_page_config(
    page_title="Registro Mantenimiento Válvulas L2",
    page_icon="🏢",
    layout="wide"
)

SHEET_URL = "https://docs.google.com/spreadsheets/d/12SH_kgBr436fu6gsuqISgXANebVtV_XL2AUH9WASfoI/edit?usp=sharing"
ZONA_HORARIA = ZoneInfo("America/Santiago")

# =====================================================
# RUTAS DEL PROYECTO / LOGO
# =====================================================
BASE_DIR = Path(__file__).resolve().parent

LOGO_CANDIDATES = [
    BASE_DIR / "assets" / "CCU_logo_(2018).svg.png",
    BASE_DIR.parent / "assets" / "CCU_logo_(2018).svg.png",
]

LOGO_PATH = next(
    (path for path in LOGO_CANDIDATES if path.exists()),
    LOGO_CANDIDATES[0]
)

# =====================================================
# LISTAS FORMULARIO
# =====================================================
TURNOS = ["", "A", "B", "C"]

OPERADORES = [
    "",
    "RODRIGO MIRANDA CATALAN",
    "MARCO QUILAHUEQUE CONTRERAS",
    "MAURICIO MOYA MAUREIRA",
    "JOSÉ RICARDO QUILÁN REYES",
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
# ESTILO GENERAL
# =====================================================
st.markdown(
    """
    <style>
    .block-container {
        padding-top: 0.8rem;
        padding-bottom: 1.2rem;
        padding-left: 2rem;
        padding-right: 2rem;
        max-width: 1180px;
    }

    h1 {
        text-align: center;
        margin-bottom: 0.2rem;
        color: #0E4C92;
        line-height: 1.15;
    }

    h2 {
        color: #2E86C1;
    }

    h3 {
        color: #0E4C92;
    }

    div[data-testid="stCheckbox"] {
        margin-bottom: -10px;
    }

    div[data-testid="stCheckbox"] label {
        font-size: 0.78rem;
    }

    div[data-testid="stVerticalBlock"] {
        gap: 0.35rem;
    }

    .valvula-resumen {
        background-color: rgba(30, 144, 255, 0.14);
        color: #1E90FF;
        border-radius: 8px;
        padding: 12px 16px;
        margin: 12px 18px 4px 18px;
        font-size: 0.95rem;
    }

    .valvula-lista {
        padding-left: 18px;
        padding-right: 18px;
        margin-top: 6px;
    }
    </style>
    """,
    unsafe_allow_html=True
)


# =====================================================
# FUNCIÓN LOGO
# =====================================================
def mostrar_logo():
    if LOGO_PATH.exists():
        logo_base64 = base64.b64encode(LOGO_PATH.read_bytes()).decode("utf-8")

        st.markdown(
            f"""
            <div style="
                width: 100%;
                display: flex;
                justify-content: center;
                align-items: center;
                margin-top: 1.4rem;
                margin-bottom: 2.2rem;
            ">
                <img
                    src="data:image/png;base64,{logo_base64}"
                    style="
                        width: 190px;
                        max-width: 70%;
                        display: block;
                    "
                    alt="Logo CCU"
                >
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.warning(f"Logo no encontrado: {LOGO_PATH}")


# =====================================================
# ENCABEZADO
# =====================================================
mostrar_logo()

st.markdown(
    """
    <div style='text-align: center; padding: 10px 10px 4px 10px;'>
        <h1 style='color:#0E4C92; margin-bottom:18px; font-size: 2.1rem;'>
            REGISTRO DE MANTENIMIENTO
        </h1>
        <h2 style='color:#2E86C1; margin-top:0px; font-size: 1.25rem; font-weight: 600;'>
            LÍNEA 2 · VÁLVULAS KRONES
        </h2>
        <p style='color:#5D6D7E; font-size: 1rem; margin-top: 18px;'>
            Formulario para registrar mantenciones operacionales de válvulas
        </p>
        <hr style='border: 1px solid #D6EAF8; width:75%; margin-top: 18px;'>
    </div>
    """,
    unsafe_allow_html=True
)

st.info("Complete todos los campos requeridos antes de guardar el registro.")


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
# REPUESTO / MANTENCIÓN
# =====================================================
with st.container(border=True):
    st.subheader("Repuesto / Mantención")

    col1, col2 = st.columns([1, 2])

    with col1:
        repuesto_sel = st.selectbox("Seleccione", [""] + REPUESTOS)

    with col2:
        otro_repuesto = ""

        if repuesto_sel == "OTRO":
            otro_repuesto = st.text_input("Especificar OTRO").upper().strip()

    repuesto_final = otro_repuesto if repuesto_sel == "OTRO" else repuesto_sel

    observaciones = st.text_area(
        "Observaciones",
        height=100,
        placeholder="Escriba observaciones adicionales..."
    )


# =====================================================
# SELECCIÓN DE VÁLVULAS
# =====================================================
with st.container(border=True):
    st.subheader("Selección de válvulas")

    st.caption("Seleccione una o más válvulas intervenidas.")

    st.markdown(
        """
        <div class="valvula-lista">
        """,
        unsafe_allow_html=True
    )

    columnas = 14

    for inicio in range(1, 113, columnas):
        cols = st.columns(columnas, gap="small")

        for i, num in enumerate(range(inicio, min(inicio + columnas, 113))):
            with cols[i]:
                st.checkbox(str(num), key=f"val_{num}")

    st.markdown("</div>", unsafe_allow_html=True)

    valvulas = [
        n for n in NUMEROS_VALVULA
        if st.session_state.get(f"val_{n}", False)
    ]

    st.markdown(
        f"""
        <div class="valvula-resumen">
            Válvulas seleccionadas: {len(valvulas)}
        </div>
        """,
        unsafe_allow_html=True
    )

    if valvulas:
        st.write(valvulas)


# =====================================================
# RESUMEN
# =====================================================
with st.container(border=True):
    st.subheader("Resumen")

    col1, col2 = st.columns(2)

    with col1:
        st.write("Fecha:", fecha)
        st.write("Turno:", turno)
        st.write("Operador:", operador_final)

    with col2:
        st.write("Repuesto / Mantención:", repuesto_final)
        st.write("Válvulas seleccionadas:", valvulas)

    if observaciones:
        st.write("Observaciones:", observaciones)

    guardar = st.button("Guardar registro", use_container_width=True)


# =====================================================
# VALIDACIÓN Y GUARDADO
# =====================================================
if guardar:

    errores = []

    if fecha is None:
        errores.append("Seleccionar fecha")

    if not turno:
        errores.append("Seleccionar turno")

    if not operador_final:
        errores.append("Seleccionar operador")

    if not repuesto_sel:
        errores.append("Seleccionar repuesto / mantención")

    if repuesto_sel == "OTRO" and not otro_repuesto:
        errores.append("Especificar repuesto / mantención")

    if not valvulas:
        errores.append("Seleccionar al menos una válvula")

    if errores:
        for error in errores:
            st.error(error)

    else:
        filas = []
        fecha_registro = obtener_fecha_registro()

        for valvula in valvulas:
            filas.append([
                fecha.strftime("%d-%m-%Y"),
                turno,
                operador_final,
                valvula,
                repuesto_final,
                observaciones,
                fecha_registro,
                "Formulario Válvulas KRONES L2"
            ])

        try:
            guardar_registros(filas)
            st.success(f"{len(filas)} registros guardados correctamente.")

        except Exception as e:
            st.error(f"Error al guardar: {e}")


# =====================================================
# FOOTER
# =====================================================
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; opacity: 0.6; font-size: 0.85rem;'>
        <b>Formulario Mantenimiento Válvulas KRONES Línea 2</b> · v1.2<br>
        Streamlit · Google Sheets
    </div>
    """,
    unsafe_allow_html=True
)
